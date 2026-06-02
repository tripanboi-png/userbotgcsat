"""
General helper utilities for the userbot.
"""

import uuid
import asyncio
from datetime import datetime, timezone
from telethon.tl.types import (
    Channel, Chat, User,
    InputPeerChannel, InputPeerChat,
)
from utils.logger import logger


def generate_task_id() -> str:
    """Generate a unique short task ID."""
    return str(uuid.uuid4())[:8].upper()


def format_duration(seconds: float) -> str:
    """Format seconds into human-readable duration."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.1f}m"
    hours = minutes / 60
    return f"{hours:.1f}h"


def format_datetime(dt: datetime | None) -> str:
    """Format datetime to readable string."""
    if dt is None:
        return "Never"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def is_group_or_supergroup(dialog) -> bool:
    """
    Returns True if dialog is a Group or Supergroup.
    Filters out: Channels (broadcast), Private chats, Bot chats, Saved Messages.
    """
    entity = dialog.entity

    # Skip saved messages (chat with yourself)
    if dialog.is_user:
        return False

    # Skip channels (broadcast only)
    if isinstance(entity, Channel):
        if entity.broadcast:
            return False  # This is a broadcast channel
        return True  # This is a supergroup (megagroup)

    # Regular group chat
    if isinstance(entity, Chat):
        return True

    return False


async def get_target_groups(client) -> list:
    """
    Get all groups and supergroups from dialogs.
    Excludes: channels, private chats, bots, saved messages.
    """
    from utils.floodwait import safe_get_dialogs
    dialogs = await safe_get_dialogs(client)

    groups = []
    for dialog in dialogs:
        if is_group_or_supergroup(dialog):
            groups.append(dialog)

    logger.info(f"[Helpers] Found {len(groups)} target groups out of {len(dialogs)} dialogs")
    return groups


def parse_command(text: str, prefix: str = ".") -> tuple[str, list[str]]:
    """
    Parse a command message into (command, args).
    Example: ".gcast Hello World" -> ("gcast", ["Hello", "World"])
    """
    if not text.startswith(prefix):
        return "", []
    parts = text[len(prefix):].split(maxsplit=1)
    if not parts:
        return "", []
    command = parts[0].lower()
    args = parts[1].split() if len(parts) > 1 else []
    return command, args


def parse_command_with_text(text: str, prefix: str = ".") -> tuple[str, str]:
    """
    Parse a command and return (command, full_text_remainder).
    Example: ".gcast Hello World" -> ("gcast", "Hello World")
    """
    if not text.startswith(prefix):
        return "", ""
    parts = text[len(prefix):].split(maxsplit=1)
    if not parts:
        return "", ""
    command = parts[0].lower()
    remainder = parts[1] if len(parts) > 1 else ""
    return command, remainder


async def edit_or_send(event, text: str):
    """Edit the current message, or send a new one if edit fails."""
    try:
        await event.edit(text)
    except Exception:
        await event.respond(text)
