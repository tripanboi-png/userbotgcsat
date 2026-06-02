"""
FloodWait handler utility.
Automatically sleeps and retries on Telegram FloodWaitError.
"""

import asyncio
from telethon.errors import FloodWaitError
from utils.logger import logger


async def safe_send_message(client, entity, message: str, **kwargs):
    """
    Send a message with automatic FloodWait handling.
    Returns (message_object, error_string_or_None)
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            msg = await client.send_message(entity, message, **kwargs)
            return msg, None
        except FloodWaitError as e:
            wait_time = e.seconds + 5
            logger.warning(
                f"[FloodWait] FloodWait {e.seconds}s on attempt {attempt + 1}/{max_retries}. "
                f"Sleeping {wait_time}s..."
            )
            await asyncio.sleep(wait_time)
            if attempt == max_retries - 1:
                return None, f"FloodWait: {e.seconds}s (max retries exceeded)"
        except Exception as e:
            return None, str(e)
    return None, "Max retries exceeded"


async def safe_delete_message(client, chat_id: int, message_id: int) -> bool:
    """
    Delete a message safely. Returns True on success, False on any error.
    Does NOT raise exceptions.
    """
    try:
        await client.delete_messages(chat_id, message_id)
        return True
    except FloodWaitError as e:
        logger.warning(f"[FloodWait] FloodWait {e.seconds}s while deleting message. Skipping delete.")
        return False
    except Exception as e:
        logger.warning(f"[Delete] Could not delete message {message_id} in {chat_id}: {e}")
        return False


async def safe_get_dialogs(client, limit: int = 500) -> list:
    """Get all dialogs with FloodWait handling."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            dialogs = await client.get_dialogs(limit=limit)
            return dialogs
        except FloodWaitError as e:
            wait_time = e.seconds + 5
            logger.warning(f"[FloodWait] get_dialogs FloodWait {e.seconds}s. Sleeping {wait_time}s...")
            await asyncio.sleep(wait_time)
            if attempt == max_retries - 1:
                return []
        except Exception as e:
            logger.error(f"[Dialogs] Error getting dialogs: {e}")
            return []
    return []
