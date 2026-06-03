"""
╭──────────────────────────────╮
│      AUTOGCAST MODULE        │
╰──────────────────────────────╯

Commands:
• .autogcast
• .autogcastall
• .autogcastsession
• .stopgcast
• .stopgcastsession

Developed by Tripan
"""

import asyncio
from datetime import datetime, timezone, timedelta
from telethon import events
from config import OWNER_ID, BROADCAST_DELAY
from database.autogcast import (
    save_autogcast, get_all_active_autogcast, get_autogcast_by_session,
    stop_autogcast_by_session, stop_all_autogcast, update_run_times,
    get_all_autogcast_status
)
from database.logs import log_broadcast
from database.sessions import get_all_sessions
from utils.helpers import get_target_groups, generate_task_id, format_datetime, edit_or_send
from utils.floodwait import safe_send_message, safe_delete_message
from utils.scheduler import add_job, remove_job, remove_all_jobs, get_job_info
from utils.logger import logger

# Global: task_id -> {"client_manager": ..., "message": ..., "session_name": ..., "all_sessions": bool}
_task_registry: dict[str, dict] = {}


async def _auto_broadcast_job(task_id: str, session_name: str, message: str, all_sessions: bool):
    """
    Core autogcast job function called by APScheduler.
    Handles auto-delete of previous messages and sends new ones.
    """
    from database.logs import (
        save_sent_message,
        get_sent_message,
        delete_sent_message_record,
    )

    task_info = _task_registry.get(task_id)
    if not task_info:
        logger.warning(f"[AutoGcast] Task {task_id} not in registry, skipping.")
        return

    client_manager = task_info["client_manager"]
    now = datetime.now(timezone.utc)

    if all_sessions:
        clients = client_manager.get_all_clients()
    else:
        c = client_manager.get_client_by_name(session_name)
        clients = {session_name: c} if c else {}

    if not clients:
        logger.warning(f"[AutoGcast] No active clients for task {task_id}")
        return

    for sess_name, client in clients.items():
        if client is None:
            continue

        groups = await get_target_groups(client)
        for dialog in groups:
            chat_id = dialog.id

            # Delete previous message if exists
            prev = await get_sent_message(chat_id, sess_name)
            if prev:
                deleted = await safe_delete_message(client, chat_id, prev["message_id"])
                if deleted:
                    await delete_sent_message_record(chat_id, sess_name)

            # Send new message
            msg, error = await safe_send_message(client, chat_id, message)
            if error:
                logger.warning(f"[AutoGcast] Failed to send to {chat_id}: {error}")
                await log_broadcast(task_id, sess_name, chat_id, None, False, error)
            else:
                await save_sent_message(chat_id, msg.id, sess_name)
                await log_broadcast(task_id, sess_name, chat_id, msg.id, True)

            await asyncio.sleep(BROADCAST_DELAY)

    # Update last/next run in DB
    from database.autogcast import get_autogcast_by_session
    task_doc = await get_autogcast_by_session(session_name)
    if task_doc:
        interval = task_doc["interval_minutes"]
        next_run = now + timedelta(minutes=interval)
        await update_run_times(task_id, now, next_run)



def register(client, client_manager, name: str = "owner"):
    """Register autogcast commands on the owner client."""

    # =============================================================================
    # AUTOGCAST COMMAND
    # =============================================================================
    @client.on(events.NewMessage(pattern=r"^\.autogcast\s+(\d+)\s+([\s\S]+)$", outgoing=True))
    async def autogcast_handler(event):
        if event.sender_id != OWNER_ID:
            return

        interval = int(event.pattern_match.group(1))
        message = event.pattern_match.group(2).strip()

        if interval < 1:
            await event.edit("❌ **Interval minimal 1 menit.**")
            return

        me = await client.get_me()
        task_id = await save_autogcast(
            session_name=name,
            user_id=me.id,
            interval_minutes=interval,
            message=message,
            all_sessions=False,
        )

        _task_registry[task_id] = {
            "client_manager": client_manager,
            "message": message,
            "session_name": name,
            "all_sessions": False,
        }

        add_job(task_id, _auto_broadcast_job, interval,
                session_name=name, message=message, all_sessions=False)

        await event.edit(
            f"✅ **Auto GCast AKTIF**\n\n"
            f"⏱ **Interval:** `{interval} menit`\n"
            f"📱 **Session:** `{name}`\n"
            f"🆔 **Task ID:** `{task_id}`\n\n"
            f"💬 **Pesan:**\n{message[:100]}{'...' if len(message) > 100 else ''}"
        )

    # =============================================================================
    # AUTOGCAST ALL COMMAND
    # =============================================================================
    @client.on(events.NewMessage(pattern=r"^\.autogcastall\s+(\d+)\s+([\s\S]+)$", outgoing=True))
    async def autogcastall_handler(event):
        if event.sender_id != OWNER_ID:
            return

        interval = int(event.pattern_match.group(1))
        message = event.pattern_match.group(2).strip()

        if interval < 1:
            await event.edit("❌ **Interval minimal 1 menit.**")
            return

        me = await client.get_me()
        task_id = await save_autogcast(
            session_name="__all__",
            user_id=me.id,
            interval_minutes=interval,
            message=message,
            all_sessions=True,
        )

        _task_registry[task_id] = {
            "client_manager": client_manager,
            "message": message,
            "session_name": "__all__",
            "all_sessions": True,
        }

        add_job(task_id, _auto_broadcast_job, interval,
                session_name="__all__", message=message, all_sessions=True)

        all_sessions = client_manager.get_all_clients()
        await event.edit(
            f"✅ **Auto GCast ALL AKTIF**\n\n"
            f"⏱ **Interval:** `{interval} menit`\n"
            f"📱 **Sessions:** `{len(all_sessions)}`\n"
            f"🆔 **Task ID:** `{task_id}`\n\n"
            f"💬 **Pesan:**\n{message[:100]}{'...' if len(message) > 100 else ''}"
        )

    # =============================================================================
    # AUTOGCAST SESSION COMMAND
    # =============================================================================
    @client.on(events.NewMessage(
        pattern=r"^\.autogcastsession\s+(\S+)\s+(\d+)\s+([\s\S]+)$", outgoing=True
    ))
    async def autogcastsession_handler(event):
        if event.sender_id != OWNER_ID:
            return

        session_name = event.pattern_match.group(1).strip()
        interval = int(event.pattern_match.group(2))
        message = event.pattern_match.group(3).strip()

        if interval < 1:
            await event.edit("❌ **Interval minimal 1 menit.**")
            return

        target_client = client_manager.get_client_by_name(session_name)
        if not target_client:
            await event.edit(f"❌ **Session `{session_name}` tidak ditemukan.**")
            return

        me = await client.get_me()
        task_id = await save_autogcast(
            session_name=session_name,
            user_id=me.id,
            interval_minutes=interval,
            message=message,
            all_sessions=False,
        )

        _task_registry[task_id] = {
            "client_manager": client_manager,
            "message": message,
            "session_name": session_name,
            "all_sessions": False,
        }

        add_job(task_id, _auto_broadcast_job, interval,
                session_name=session_name, message=message, all_sessions=False)

        await event.edit(
            f"✅ **Auto GCast Session AKTIF**\n\n"
            f"⏱ **Interval:** `{interval} menit`\n"
            f"📱 **Session:** `{session_name}`\n"
            f"🆔 **Task ID:** `{task_id}`\n\n"
            f"💬 **Pesan:**\n{message[:100]}{'...' if len(message) > 100 else ''}"
        )

    # =============================================================================
    # STOP GCAST COMMAND
    # =============================================================================
    @client.on(events.NewMessage(pattern=r"^\.stopgcast$", outgoing=True))
    async def stopgcast_handler(event):
        if event.sender_id != OWNER_ID:
            return

        stopped = await stop_all_autogcast()
        remove_all_jobs()
        _task_registry.clear()

        await event.edit(
            f"🛑 **Semua Auto GCast dihentikan.**\n"
            f"📊 **Tasks dihentikan:** `{stopped}`"
        )

    # =============================================================================
    # STOP GCAST SESSION COMMAND
    # =============================================================================
    @client.on(events.NewMessage(pattern=r"^\.stopgcastsession\s+(\S+)$", outgoing=True))
    async def stopgcastsession_handler(event):
        if event.sender_id != OWNER_ID:
            return

        session_name = event.pattern_match.group(1).strip()
        stopped = await stop_autogcast_by_session(session_name)

        # Find and remove job
        removed = 0
        for task_id, info in list(_task_registry.items()):
            if info["session_name"].lower() == session_name.lower():
                remove_job(task_id)
                del _task_registry[task_id]
                removed += 1

        if stopped or removed:
            await event.edit(
                f"🛑 **Auto GCast `{session_name}` dihentikan.**"
            )
        else:
            await event.edit(
                f"⚠️ **Tidak ada task aktif untuk session `{session_name}`.**"
            )

    # =============================================================================
    # GCAST STATUS COMMAND
    # =============================================================================
    @client.on(events.NewMessage(pattern=r"^\.gcaststatus$", outgoing=True))
    async def gcaststatus_handler(event):
        if event.sender_id != OWNER_ID:
            return

        task = await get_autogcast_by_session(name)
        if not task:
            await event.edit(
                f"📊 **AUTO GCAST STATUS**\n\n"
                f"📱 **Session:** `{name}`\n"
                f"🔴 **Status:** TIDAK AKTIF"
            )
            return

        job_info = get_job_info(task["task_id"])
        next_run_str = format_datetime(job_info["next_run"]) if job_info else "—"

        text = (
            f"📊 **AUTO GCAST STATUS**\n\n"
            f"📱 **Session:** `{task['session_name']}`\n"
            f"🟢 **Status:** {'RUNNING' if task['active'] else 'STOPPED'}\n"
            f"⏱ **Interval:** `{task['interval_minutes']} Menit`\n"
            f"🔢 **Total Run:** `{task.get('run_count', 0)}`\n"
            f"🕐 **Last Run:** `{format_datetime(task.get('last_run'))}`\n"
            f"⏭ **Next Run:** `{next_run_str}`\n"
            f"🆔 **Task ID:** `{task['task_id']}`\n\n"
            f"💬 **Pesan:**\n{task['message'][:150]}{'...' if len(task['message']) > 150 else ''}"
        )
        await event.edit(text)

    # =============================================================================
    # GCAST STATUS ALL COMMAND
    # =============================================================================
    @client.on(events.NewMessage(pattern=r"^\.gcaststatusall$", outgoing=True))
    async def gcaststatusall_handler(event):
        if event.sender_id != OWNER_ID:
            return

        tasks = await get_all_autogcast_status()
        if not tasks:
            await event.edit("📊 **Tidak ada task autogcast.**")
            return

        lines = ["📊 **ALL AUTO GCAST STATUS**\n"]
        for t in tasks:
            status = "🟢 RUNNING" if t["active"] else "🔴 STOPPED"
            lines.append(
                f"▸ **{t['session_name']}** | {status}\n"
                f"  ⏱ {t['interval_minutes']}m | Run: {t.get('run_count', 0)}x\n"
                f"  🕐 Last: {format_datetime(t.get('last_run'))}\n"
                f"  🆔 `{t['task_id']}`"
            )

        await event.edit("\n".join(lines))



async def restore_autogcast_tasks(client_manager):
    """
    Called on startup to restore autogcast tasks from MongoDB.
    Re-schedules any active tasks.
    """
    tasks = await get_all_active_autogcast()
    restored = 0

    for task in tasks:
        task_id = task["task_id"]
        session_name = task["session_name"]
        interval = task["interval_minutes"]
        message = task["message"]
        all_sessions = task.get("all_sessions", False)

        _task_registry[task_id] = {
            "client_manager": client_manager,
            "message": message,
            "session_name": session_name,
            "all_sessions": all_sessions,
        }

        add_job(task_id, _auto_broadcast_job, interval,
                session_name=session_name,
                message=message, all_sessions=all_sessions)
        restored += 1

    
    return restored
