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
`.addsession <string_session>` — Tambah akun baru
`.delsession <nama_akun>` — Hapus akun
`.sessions` — Lihat daftar akun aktif
━━━━━━━━━━━━━━━━━━━━
📢 **BROADCAST**
━━━━━━━━━━━━━━━━━━━━
`.gcast <msg>` — Broadcast (owner only)
`.gcastall <msg>` — Kirim pesan ke semua akun
`.gcastsession <nama_akun> <pesan>` — Kirim pesan melalui akun tertentu

━━━━━━━━━━━━━━━━━━━━
⏰ **AUTO BROADCAST**
━━━━━━━━━━━━━━━━━━━━
`.autogcast <menit> <pesan>` — Broadcast otomatis akun utama
`.autogcastall <menit> <pesan>` — Broadcast otomatis semua akun
`.autogcastsession <nama_akun> <menit> <pesan>` — Broadcast otomatis akun tertentu

━━━━━━━━━━━━━━━━━━━━
🛑 **STOP AUTO BROADCAST**
━━━━━━━━━━━━━━━━━━━━
`.stopgcast` — Hentikan semua auto broadcast
`.stopgcastsession <nama_akun>` — Hentikan auto broadcast akun tertentu

━━━━━━━━━━━━━━━━━━━━
📊 **STATUS & STATS**
━━━━━━━━━━━━━━━━━━━━
`.gcaststatus` — Status auto broadcast akun utama
`.gcaststatusall` — Status semua akun
`.gcaststats` — Broadcast statistics
`.gcasterror` — Lihat error terbaru
"""
        await edit_or_send(event, help_text.strip())

