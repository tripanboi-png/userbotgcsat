"""
Session management module.
Commands: .addsession, .delsession, .sessions
"""

import asyncio
from telethon import events, TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError,
    AuthKeyUnregisteredError,
    UserDeactivatedBanError,
    AuthKeyDuplicatedError,
)
from config import API_ID, API_HASH, OWNER_ID
from database.sessions import (
    add_session, get_all_sessions, delete_session_by_name,
    get_session_by_name
)
from utils.logger import logger
from utils.helpers import edit_or_send


def register(client, client_manager, name: str = "owner"):
    """
    Register session management commands on the owner client.
    client_manager: reference to the ClientManager instance.
    """

    # ─── .addsession ─────────────────────────────────────────────────────────
    @client.on(events.NewMessage(pattern=r"^\.addsession\s+(.+)$", outgoing=True))
    async def addsession_handler(event):
        if event.sender_id != OWNER_ID:
            return

        session_string = event.pattern_match.group(1).strip()
        await event.edit("⏳ Validating session...")

        try:
            test_client = TelegramClient(
                StringSession(session_string),
                API_ID,
                API_HASH,
            )
            await test_client.connect()

            if not await test_client.is_user_authorized():
                await event.edit("❌ **Session tidak valid atau sudah expired.**")
                await test_client.disconnect()
                return

            me = await test_client.get_me()
            await test_client.disconnect()

        except AuthKeyUnregisteredError:
            await event.edit("❌ **Auth key tidak terdaftar. Session expired.**")
            return
        except UserDeactivatedBanError:
            await event.edit("❌ **Akun ini telah diban oleh Telegram.**")
            return
        except AuthKeyDuplicatedError:
            await event.edit("❌ **Auth key duplikat. Session tidak bisa digunakan.**")
            return
        except Exception as e:
            await event.edit(f"❌ **Error validasi session:**\n`{e}`")
            return

        # Save to DB
        display_name = me.first_name or f"user_{me.id}"
        username = f"@{me.username}" if me.username else "Tidak Ada"

        await add_session(
            name=display_name,
            user_id=me.id,
            username=me.username or "",
            session_string=session_string,
        )

        # Start the client
        await client_manager.start_session_by_string(session_string, display_name)

        text = (
            f"✅ **Session berhasil ditambahkan**\n\n"
            f"👤 **Nama:** {me.first_name} {me.last_name or ''}\n"
            f"🔗 **Username:** {username}\n"
            f"🆔 **ID:** `{me.id}`"
        )
        await event.edit(text)
        logger.info(f"[SessionManager] Added session: {display_name} ({me.id})")

    # ─── .delsession ─────────────────────────────────────────────────────────
    @client.on(events.NewMessage(pattern=r"^\.delsession\s+(.+)$", outgoing=True))
    async def delsession_handler(event):
        if event.sender_id != OWNER_ID:
            return

        session_name = event.pattern_match.group(1).strip()
        await event.edit(f"⏳ Menghapus session `{session_name}`...")

        doc = await delete_session_by_name(session_name)
        if not doc:
            await event.edit(f"❌ **Session `{session_name}` tidak ditemukan.**")
            return

        # Stop the client if running
        await client_manager.stop_session_by_name(session_name)

        await event.edit(
            f"✅ **Session `{doc['name']}` berhasil dihapus.**\n"
            f"🆔 User ID: `{doc['user_id']}`"
        )
        logger.info(f"[SessionManager] Deleted session: {doc['name']} ({doc['user_id']})")

    # ─── .sessions ───────────────────────────────────────────────────────────
    @client.on(events.NewMessage(pattern=r"^\.sessions$", outgoing=True))
    async def sessions_handler(event):
        if event.sender_id != OWNER_ID:
            return

        sessions = await get_all_sessions()
        if not sessions:
            await event.edit("📭 **Tidak ada session aktif.**")
            return

        lines = ["📱 **ACTIVE SESSIONS**\n"]
        for i, s in enumerate(sessions, 1):
            username = f"@{s['username']}" if s.get("username") else "—"
            is_running = client_manager.is_running(s["name"])
            status_icon = "🟢" if is_running else "🔴"
            lines.append(
                f"{i}. {status_icon} **{s['name']}**\n"
                f"   └ {username} | ID: `{s['user_id']}`"
            )

        lines.append(f"\n**Total:** `{len(sessions)}`")
        await event.edit("\n".join(lines))
        logger.info(f"[SessionManager] .sessions → {len(sessions)} sessions")

    logger.info(f"[SessionManager] Commands registered for '{name}'")
