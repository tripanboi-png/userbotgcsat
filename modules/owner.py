"""
Owner module: .ping, .alive, .help commands.
Only the OWNER_ID can trigger these.
"""

import time
import asyncio
from telethon import events
from config import OWNER_ID
from utils.logger import logger
from utils.helpers import edit_or_send


def register(client, name: str = "owner"):
    """Register owner commands on a Telethon client."""

    # ─── .ping ───────────────────────────────────────────────────────────────
    @client.on(events.NewMessage(pattern=r"^\.ping$", outgoing=True))
    async def ping_handler(event):
        if event.sender_id != OWNER_ID:
            return
        start = time.monotonic()
        msg = await event.edit("🏓 Pong!")
        elapsed = (time.monotonic() - start) * 1000
        await event.edit(f"🏓 **Pong!**\n⚡ `{elapsed:.2f}ms`")
        logger.info(f"[{name}] .ping → {elapsed:.2f}ms")

    # ─── .alive ──────────────────────────────────────────────────────────────
    @client.on(events.NewMessage(pattern=r"^\.alive$", outgoing=True))
    async def alive_handler(event):
        if event.sender_id != OWNER_ID:
            return
        me = await client.get_me()
        text = (
            "🤖 **USERBOT ALIVE**\n\n"
            f"👤 **Name:** {me.first_name} {me.last_name or ''}\n"
            f"🆔 **ID:** `{me.id}`\n"
            f"🐍 **Framework:** Telethon\n"
            f"📦 **Session:** `{name}`\n"
            f"✅ **Status:** Online & Running"
        )
        await edit_or_send(event, text)
        logger.info(f"[{name}] .alive triggered")

    # ─── .help ───────────────────────────────────────────────────────────────
    @client.on(events.NewMessage(pattern=r"^\.help$", outgoing=True))
    async def help_handler(event):
        if event.sender_id != OWNER_ID:
            return
        help_text = """
📖 **USERBOT HELP**

━━━━━━━━━━━━━━━━━━━━
🔧 **GENERAL**
━━━━━━━━━━━━━━━━━━━━
`.ping` — Check latency
`.alive` — Check bot status
`.help` — Show this help

━━━━━━━━━━━━━━━━━━━━
📱 **SESSION MANAGEMENT**
━━━━━━━━━━━━━━━━━━━━
`.addsession <string>` — Add new session
`.delsession <name>` — Remove a session
`.sessions` — List all sessions

━━━━━━━━━━━━━━━━━━━━
📢 **BROADCAST**
━━━━━━━━━━━━━━━━━━━━
`.gcast <msg>` — Broadcast (owner only)
`.gcastall <msg>` — Broadcast all sessions
`.gcastsession <name> <msg>` — Broadcast specific session

━━━━━━━━━━━━━━━━━━━━
⏰ **AUTO BROADCAST**
━━━━━━━━━━━━━━━━━━━━
`.autogcast <min> <msg>` — Auto broadcast owner
`.autogcastall <min> <msg>` — Auto broadcast all
`.autogcastsession <name> <min> <msg>` — Auto specific

━━━━━━━━━━━━━━━━━━━━
🛑 **STOP AUTO BROADCAST**
━━━━━━━━━━━━━━━━━━━━
`.stopgcast` — Stop all autogcast
`.stopgcastsession <name>` — Stop specific session

━━━━━━━━━━━━━━━━━━━━
📊 **STATUS & STATS**
━━━━━━━━━━━━━━━━━━━━
`.gcaststatus` — Status owner autogcast
`.gcaststatusall` — Status all sessions
`.gcaststats` — Broadcast statistics
`.gcasterror` — Show recent errors
"""
        await edit_or_send(event, help_text.strip())
        logger.info(f"[{name}] .help triggered")

    logger.info(f"[Owner] Commands registered for session '{name}'")
