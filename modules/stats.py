"""
Statistics and error log module.
Commands: .gcaststats, .gcasterror
"""

from telethon import events
from config import OWNER_ID
from database.logs import get_stats, get_latest_errors
from utils.helpers import edit_or_send
from utils.logger import logger


def register(client, name: str = "owner"):
    """Register stats commands on the owner client."""

    # ─── .gcaststats ─────────────────────────────────────────────────────────
    @client.on(events.NewMessage(pattern=r"^\.gcaststats$", outgoing=True))
    async def gcaststats_handler(event):
        if event.sender_id != OWNER_ID:
            return

        today = await get_stats("today")
        week = await get_stats("week")
        total = await get_stats("all")

        text = (
            f"📈 **GCAST STATS**\n\n"
            f"**Hari Ini:**\n"
            f"  ✅ Berhasil: `{today['success']}`\n"
            f"  ❌ Gagal: `{today['fail']}`\n\n"
            f"**Minggu Ini:**\n"
            f"  ✅ Berhasil: `{week['success']}`\n"
            f"  ❌ Gagal: `{week['fail']}`\n\n"
            f"**Total:**\n"
            f"  ✅ Berhasil: `{total['success']}`\n"
            f"  ❌ Gagal: `{total['fail']}`"
        )
        await edit_or_send(event, text)

    # ─── .gcasterror ─────────────────────────────────────────────────────────
    @client.on(events.NewMessage(pattern=r"^\.gcasterror$", outgoing=True))
    async def gcasterror_handler(event):
        if event.sender_id != OWNER_ID:
            return

        errors = await get_latest_errors(limit=15)
        if not errors:
            await edit_or_send(event, "✅ **Tidak ada error dalam log.**")
            return

        lines = ["❌ **GCAST ERROR LOG** (15 terbaru)\n"]
        for i, e in enumerate(errors, 1):
            from utils.helpers import format_datetime
            ts = format_datetime(e.get("timestamp"))
            lines.append(
                f"{i}. 🔴 **Chat:** `{e['chat_id']}`\n"
                f"   📱 Session: `{e['session_name']}`\n"
                f"   💬 Error: `{e['error'][:80]}`\n"
                f"   🕐 `{ts}`"
            )

        await edit_or_send(event, "\n".join(lines))

