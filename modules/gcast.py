""""
╭──────────────────────────────╮
│      BROADCAST MODULE        │
╰──────────────────────────────╯

Commands:
• .gcast
• .gcastall
• .gcastsession

Developed by Tripan
"""

import asyncio
import time
from telethon import events
from config import OWNER_ID, BROADCAST_DELAY
from database.sessions import get_all_sessions, get_session_by_name
from database.logs import log_broadcast
from utils.helpers import (
    get_target_groups, generate_task_id, format_duration, edit_or_send
)
from utils.floodwait import safe_send_message
from utils.logger import logger


async def _broadcast_with_client(
    client,
    session_name: str,
    message: str,
    task_id: str,
) -> dict:
    """
    Core broadcast function. Sends message to all groups of the given client.
    Returns a result dict: {success, fail, total, errors}
    """
    groups = await get_target_groups(client)
    success = 0
    fail = 0
    errors = []

    for dialog in groups:
        chat_id = dialog.id
        try:
            msg, error = await safe_send_message(client, chat_id, message)
            if error:
                fail += 1
                errors.append({"chat_id": chat_id, "name": dialog.name, "error": error})
                await log_broadcast(task_id, session_name, chat_id, None, False, error)
            else:
                success += 1
                await log_broadcast(task_id, session_name, chat_id, msg.id, True)
        except Exception as e:
            err_str = str(e)
            fail += 1
            errors.append({"chat_id": chat_id, "name": dialog.name, "error": err_str})
            await log_broadcast(task_id, session_name, chat_id, None, False, err_str)

        await asyncio.sleep(BROADCAST_DELAY)

    return {
        "success": success,
        "fail": fail,
        "total": len(groups),
        "errors": errors,
    }


def register(client, client_manager, name: str = "owner"):
    """Register gcast commands on the owner client."""

    # =============================================================================
    # GCAST COMMAND
    # =============================================================================
    @client.on(events.NewMessage(pattern=r"^\.gcast\s+([\s\S]+)$", outgoing=True))
    async def gcast_handler(event):
        if event.sender_id != OWNER_ID:
            return

        message = event.pattern_match.group(1).strip()
        task_id = generate_task_id()

        await event.edit(
            f"📢 **Broadcasting...**\n"
            f"🆔 Task: `{task_id}`\n"
            f"👤 Session: `{name}`"
        )

        start_time = time.monotonic()
        result = await _broadcast_with_client(client, name, message, task_id)
        duration = time.monotonic() - start_time

        text = (
            f"📢 <b>GCAST SELESAI</b>\n\n"
            f"👥 <b>Grup:</b> {result['total']}\n"
            f"✅ <b>Berhasil:</b> {result['success']}\n"
            f"❌ <b>Gagal:</b> {result['fail']}\n"
            f"⏱ <b>Durasi:</b> {format_duration(duration)}\n"
            f"🆔 <b>Task:</b> {task_id}"
        )

        await event.edit(
            f"<blockquote>{text}</blockquote>",
            parse_mode="html"
        )


    # =============================================================================
    # GCAST ALL COMMAND
    # =============================================================================
    @client.on(events.NewMessage(pattern=r"^\.gcastall\s+([\s\S]+)$", outgoing=True))
    async def gcastall_handler(event):
        if event.sender_id != OWNER_ID:
            return

        message = event.pattern_match.group(1).strip()
        task_id = generate_task_id()

        all_sessions = await get_all_sessions()
        if not all_sessions:
            await event.edit("❌ **Tidak ada session aktif.**")
            return

        all_clients = client_manager.get_all_clients()
        if not all_clients:
            await event.edit("❌ **Tidak ada client yang berjalan.**")
            return

        await event.edit(
            f"📢 **Broadcasting ke semua session...**\n"
            f"📱 **Sessions:** `{len(all_clients)}`\n"
            f"🆔 Task: `{task_id}`"
        )

        start_time = time.monotonic()
        total_success = 0
        total_fail = 0
        total_groups = 0
        session_results = []

        for sess_name, sess_client in all_clients.items():
            sub_task = f"{task_id}_{sess_name}"
            result = await _broadcast_with_client(sess_client, sess_name, message, sub_task)
            total_success += result["success"]
            total_fail += result["fail"]
            total_groups += result["total"]
            session_results.append(f"  • **{sess_name}**: ✅{result['success']} ❌{result['fail']}")

        duration = time.monotonic() - start_time
        session_summary = "\n".join(session_results)

        text = (
            f"📢 **GCAST ALL SELESAI**\n\n"
            f"📱 **Sessions:** `{len(all_clients)}`\n"
            f"👥 **Total Grup:** `{total_groups}`\n"
            f"✅ **Berhasil:** `{total_success}`\n"
            f"❌ **Gagal:** `{total_fail}`\n"
            f"⏱ **Durasi:** `{format_duration(duration)}`\n"
            f"🆔 **Task:** `{task_id}`\n\n"
            f"📊 **Per Session:**\n{session_summary}"
        )
        await event.edit(text)
    

    # =============================================================================
    # GCAST SESSION COMMAND
    # =============================================================================
    @client.on(events.NewMessage(pattern=r"^\.gcastsession\s+(\S+)\s+([\s\S]+)$", outgoing=True))
    async def gcastsession_handler(event):
        if event.sender_id != OWNER_ID:
            return

        session_name = event.pattern_match.group(1).strip()
        message = event.pattern_match.group(2).strip()
        task_id = generate_task_id()

        # Find the session client
        target_client = client_manager.get_client_by_name(session_name)
        if not target_client:
            await event.edit(f"❌ **Session `{session_name}` tidak ditemukan atau tidak aktif.**")
            return

        await event.edit(
            f"📢 **Broadcasting via {session_name}...**\n"
            f"🆔 Task: `{task_id}`"
        )

        start_time = time.monotonic()
        result = await _broadcast_with_client(target_client, session_name, message, task_id)
        duration = time.monotonic() - start_time

        text = (
            f"📢 **GCAST SESSION SELESAI**\n\n"
            f"📱 **Session:** `{session_name}`\n"
            f"👥 **Grup:** `{result['total']}`\n"
            f"✅ **Berhasil:** `{result['success']}`\n"
            f"❌ **Gagal:** `{result['fail']}`\n"
            f"⏱ **Durasi:** `{format_duration(duration)}`\n"
            f"🆔 **Task:** `{task_id}`"
        )
        await event.edit(text)
    

    


# ─── Exported for autogcast use ───────────────────────────────────────────────
async def do_broadcast(client, session_name: str, message: str, task_id: str) -> dict:
    """Public broadcast function for use by autogcast module."""
    return await _broadcast_with_client(client, session_name, message, task_id)
