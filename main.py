"""
Telegram Userbot Full Management System
Main entry point — manages all Telethon clients, loads sessions from MongoDB,
registers all modules, starts APScheduler, and runs forever.

Deploy: Heroku Worker Dyno
"""

import asyncio
import signal
import sys
from datetime import datetime, timezone

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import (
    AuthKeyUnregisteredError,
    UserDeactivatedBanError,
    AuthKeyDuplicatedError,
    SessionExpiredError,
)

from config import API_ID, API_HASH, OWNER_ID, OWNER_SESSION
from database.mongo import get_db, close_db
from database.sessions import get_all_sessions, add_session, get_session_by_user_id
from utils.logger import logger
from utils.scheduler import start_scheduler, stop_scheduler


# ─────────────────────────────────────────────────────────────────────────────
# CLIENT MANAGER
# ─────────────────────────────────────────────────────────────────────────────

class ClientManager:
    """
    Manages multiple Telethon TelegramClient instances.
    Supports dynamic addition/removal of sessions at runtime.
    """

    def __init__(self):
        # name (lowercase) -> TelegramClient
        self._clients: dict[str, TelegramClient] = {}
        self._owner_client: TelegramClient | None = None
        self._owner_name: str = "owner"

    # ── Internal helpers ────────────────────────────────────────────────────

    def _normalize(self, name: str) -> str:
        return name.strip().lower()

    async def _create_client(self, session_string: str) -> TelegramClient:
        client = TelegramClient(
            StringSession(session_string),
            API_ID,
            API_HASH,
            device_model="Userbot",
            system_version="Linux",
            app_version="1.0",
            lang_code="en",
            system_lang_code="en",
        )
        return client

    # ── Owner client ────────────────────────────────────────────────────────

    async def setup_owner(self) -> TelegramClient | None:
        """
        Set up the owner's primary client using OWNER_SESSION env var.
        If OWNER_SESSION is empty, check the database for a session with OWNER_ID.
        """
        session_string = OWNER_SESSION.strip() if OWNER_SESSION else ""

        if not session_string:
            # Try to load from database
            doc = await get_session_by_user_id(OWNER_ID)
            if doc:
                session_string = doc["session"]
                
            else:
                logger.warning(
                    "[Main] OWNER_SESSION not set and no owner session in database. "
                    "Owner client will not be started. "
                    "Use .addsession to add the owner's session from another client."
                )
                return None

        try:
            client = await self._create_client(session_string)
            await client.connect()

            if not await client.is_user_authorized():
                logger.error("[Main] Owner session is not authorized.")
                await client.disconnect()
                return None

            me = await client.get_me()
            if me.id != OWNER_ID:
                logger.warning(
                    f"[Main] OWNER_SESSION belongs to user {me.id}, "
                    f"but OWNER_ID is {OWNER_ID}. Proceeding anyway."
                )

            self._owner_name = me.first_name or "owner"
            key = self._normalize(self._owner_name)
            self._clients[key] = client
            self._owner_client = client

            # Save/update in database
            await add_session(
                name=self._owner_name,
                user_id=me.id,
                username=me.username or "",
                session_string=session_string,
            )

            logger.info(
                f"[Main] Owner client ready: {me.first_name} "
                f"(@{me.username or 'no_username'}, ID={me.id})"
            )
            return client

        except AuthKeyUnregisteredError:
            logger.error("[Main] Owner session: AuthKeyUnregistered — session expired.")
        except UserDeactivatedBanError:
            logger.error("[Main] Owner session: Account is banned.")
        except AuthKeyDuplicatedError:
            logger.error("[Main] Owner session: AuthKeyDuplicated.")
        except Exception as e:
            logger.error(f"[Main] Owner session error: {e}")

        return None

    # ── Load all sessions from DB ───────────────────────────────────────────

    async def load_all_sessions(self):
        """Load and start all active sessions from MongoDB."""
        sessions = await get_all_sessions()
        started = 0

        for doc in sessions:
            # Skip if already loaded (owner)
            key = self._normalize(doc["name"])
            if key in self._clients:
                continue

            success = await self.start_session_by_string(doc["session"], doc["name"])
            if success:
                started += 1

        logger.info(f"[Main] Loaded {started} additional sessions from database.")

    # ── Start / stop individual sessions ────────────────────────────────────

    async def start_session_by_string(self, session_string: str, name: str) -> bool:
        """
        Start a client from a StringSession string.
        Returns True on success.
        """
        key = self._normalize(name)
        if key in self._clients:
            logger.info(f"[ClientManager] Session '{name}' already running, skipping.")
            return True

        try:
            client = await self._create_client(session_string)
            await client.connect()

            if not await client.is_user_authorized():
                logger.warning(f"[ClientManager] Session '{name}' is not authorized.")
                await client.disconnect()
                return False

            me = await client.get_me()
            self._clients[key] = client
            logger.info(f"[ClientManager] Started session '{name}' (ID={me.id})")
            return True

        except AuthKeyUnregisteredError:
            logger.error(f"[ClientManager] '{name}': AuthKeyUnregistered — session expired.")
        except UserDeactivatedBanError:
            logger.error(f"[ClientManager] '{name}': Account is banned.")
        except AuthKeyDuplicatedError:
            logger.error(f"[ClientManager] '{name}': AuthKeyDuplicated.")
        except Exception as e:
            logger.error(f"[ClientManager] '{name}': Error starting session: {e}")

        return False

    async def stop_session_by_name(self, name: str):
        """Disconnect and remove a client by name."""
        key = self._normalize(name)
        client = self._clients.pop(key, None)
        if client:
            try:
                await client.disconnect()
            except Exception as e:
                logger.warning(f"[ClientManager] Error disconnecting '{name}': {e}")
            logger.info(f"[ClientManager] Session '{name}' stopped.")

    # ── Accessors ────────────────────────────────────────────────────────────

    def get_owner_client(self) -> TelegramClient | None:
        return self._owner_client

    def get_client_by_name(self, name: str) -> TelegramClient | None:
        return self._clients.get(self._normalize(name))

    def get_all_clients(self) -> dict[str, TelegramClient]:
        return dict(self._clients)

    def is_running(self, name: str) -> bool:
        key = self._normalize(name)
        client = self._clients.get(key)
        return client is not None and client.is_connected()

    # ── Register modules on all clients ─────────────────────────────────────

    def register_all_modules(self):
        """
        Register all command handlers on the owner client only.
        (Only owner can send commands)
        """
        if not self._owner_client:
            logger.warning("[Main] No owner client — cannot register modules.")
            return

        from modules.owner import register as reg_owner
        from modules.session_manager import register as reg_session
        from modules.gcast import register as reg_gcast
        from modules.autogcast import register as reg_autogcast
        from modules.stats import register as reg_stats

        reg_owner(self._owner_client, self._owner_name)
        reg_session(self._owner_client, self, self._owner_name)
        reg_gcast(self._owner_client, self, self._owner_name)
        reg_autogcast(self._owner_client, self, self._owner_name)
        reg_stats(self._owner_client, self._owner_name)

        

    # ── Disconnect all ────────────────────────────────────────────────────────

    async def disconnect_all(self):
        """Gracefully disconnect all active clients."""
        for name, client in list(self._clients.items()):
            try:
                await client.disconnect()
                logger.info(f"[ClientManager] Disconnected '{name}'")
            except Exception as e:
                logger.warning(f"[ClientManager] Error disconnecting '{name}': {e}")
        self._clients.clear()

    # ── Run all clients ──────────────────────────────────────────────────────

    async def run_until_disconnected(self):
        """Run all active clients concurrently until they disconnect."""
        if not self._clients:
            logger.error("[Main] No active clients to run. Exiting.")
            return

        tasks = []
        for name, client in self._clients.items():
            if client.is_connected():
                tasks.append(asyncio.create_task(
                    client.run_until_disconnected(),
                    name=f"client_{name}"
                ))

        if not tasks:
            logger.error("[Main] No connected clients found.")
            return

        logger.info(f"[Main] Running {len(tasks)} client(s)...")
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

        for task in done:
            exc = task.exception()
            if exc:
                logger.error(f"[Main] Client task '{task.get_name()}' raised: {exc}")

        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

async def main():
    logger.info("═" * 50)
    logger.info("🚀 USERBOT STARTING")
    logger.info("═" * 50)

    # 1. Connect to MongoDB
    try:
        await get_db()
    except Exception as e:
        logger.critical(f"[Main] Failed to connect to MongoDB: {e}")
        sys.exit(1)

    # 2. Initialize client manager
    manager = ClientManager()

    # 3. Set up owner client
    owner_client = await manager.setup_owner()
    if not owner_client:
        logger.critical(
            "[Main] Could not start owner client. "
            "Please set OWNER_SESSION in your environment variables."
        )
        await close_db()
        sys.exit(1)

    # 4. Load all other sessions from MongoDB
    await manager.load_all_sessions()

    # 5. Register all command modules on owner client
    manager.register_all_modules()

    # 6. Start APScheduler
    start_scheduler()

    # 7. Restore autogcast tasks from DB
    from modules.autogcast import restore_autogcast_tasks
    restored = await restore_autogcast_tasks(manager)
    

    logger.info("═" * 50)
    logger.info("🚀 USERBOT ONLINE")
    logger.info(f"👤 Owner Session : {manager._owner_name}")
    logger.info(f"📱 Active Sessions : {len(manager.get_all_clients())}")
    logger.info(f"🔄 AutoGCast Restored : {restored}")
    logger.info("⚡ Status : READY")
    logger.info("═" * 50)

    # 8. Handle OS signals for graceful shutdown
    loop = asyncio.get_running_loop()

    async def shutdown():
        logger.info("[Main] Shutdown signal received. Cleaning up...")
        stop_scheduler()
        await manager.disconnect_all()
        await close_db()
        logger.info("[Main] Shutdown complete.")

    def handle_signal():
        asyncio.create_task(shutdown())

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, handle_signal)
        except NotImplementedError:
            pass  # Windows doesn't support add_signal_handler

    # 9. Run all clients
    logger.info("[Main] Userbot sudah siap sepenuhnya dan sedang menunggu command.")
    await manager.run_until_disconnected()

    # 10. Cleanup on exit
    stop_scheduler()
    await manager.disconnect_all()
    await close_db()
    logger.info("[Main] Userbot stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("[Main] KeyboardInterrupt — exiting.")
    except Exception as e:
        logger.critical(f"[Main] Fatal error: {e}", exc_info=True)
        sys.exit(1)
