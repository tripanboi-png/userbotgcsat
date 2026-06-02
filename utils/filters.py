"""
Custom event filters for Telethon.
"""

from telethon import events
from config import OWNER_ID


def owner_only(event: events.NewMessage.Event) -> bool:
    """Filter: only allow messages from the OWNER_ID."""
    return event.sender_id == OWNER_ID


def is_command(prefix: str = "."):
    """Returns a filter function that checks if message starts with prefix."""
    def _filter(event: events.NewMessage.Event) -> bool:
        return event.out and event.message.text.startswith(prefix)
    return _filter
