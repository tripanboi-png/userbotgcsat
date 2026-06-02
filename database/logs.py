"""
Database operations for broadcast logs and statistics.
Collections: gcast_logs, sent_messages
"""

from datetime import datetime, timezone, timedelta
from database.mongo import get_collection
from utils.logger import logger

LOGS_COLLECTION = "gcast_logs"
MESSAGES_COLLECTION = "sent_messages"


# ─── Broadcast Logs ─────────────────────────────────────────────────────────

async def log_broadcast(
    task_id: str,
    session_name: str,
    chat_id: int,
    message_id: int | None,
    success: bool,
    error: str | None = None,
):
    col = await get_collection(LOGS_COLLECTION)
    await col.insert_one({
        "task_id": task_id,
        "session_name": session_name,
        "chat_id": chat_id,
        "message_id": message_id,
        "success": success,
        "error": error,
        "timestamp": datetime.now(timezone.utc),
    })


async def get_errors_by_task(task_id: str) -> list[dict]:
    col = await get_collection(LOGS_COLLECTION)
    return await col.find({"task_id": task_id, "success": False}).to_list(length=100)


async def get_latest_errors(session_name: str | None = None, limit: int = 20) -> list[dict]:
    col = await get_collection(LOGS_COLLECTION)
    query = {"success": False}
    if session_name:
        query["session_name"] = session_name.lower()
    return await col.find(query).sort("timestamp", -1).to_list(length=limit)


async def get_stats(period: str = "all") -> dict:
    """
    Return success/fail counts.
    period: 'today', 'week', 'all'
    """
    col = await get_collection(LOGS_COLLECTION)
    now = datetime.now(timezone.utc)

    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start = now - timedelta(days=7)
    else:
        start = None

    query = {}
    if start:
        query["timestamp"] = {"$gte": start}

    pipeline = [
        {"$match": query},
        {"$group": {"_id": "$success", "count": {"$sum": 1}}}
    ]
    results = await col.aggregate(pipeline).to_list(length=None)

    success_count = 0
    fail_count = 0
    for r in results:
        if r["_id"] is True:
            success_count = r["count"]
        else:
            fail_count = r["count"]

    return {"success": success_count, "fail": fail_count}


# ─── Sent Messages (for auto-delete) ────────────────────────────────────────

async def save_sent_message(chat_id: int, message_id: int, session_name: str):
    col = await get_collection(MESSAGES_COLLECTION)
    await col.update_one(
        {"chat_id": chat_id, "session_name": session_name.lower()},
        {"$set": {
            "message_id": message_id,
            "updated_at": datetime.now(timezone.utc),
        }},
        upsert=True
    )


async def get_sent_message(chat_id: int, session_name: str) -> dict | None:
    col = await get_collection(MESSAGES_COLLECTION)
    return await col.find_one({
        "chat_id": chat_id,
        "session_name": session_name.lower()
    })


async def delete_sent_message_record(chat_id: int, session_name: str):
    col = await get_collection(MESSAGES_COLLECTION)
    await col.delete_one({
        "chat_id": chat_id,
        "session_name": session_name.lower()
    })


async def get_all_sent_messages_for_session(session_name: str) -> list[dict]:
    col = await get_collection(MESSAGES_COLLECTION)
    return await col.find({"session_name": session_name.lower()}).to_list(length=None)
