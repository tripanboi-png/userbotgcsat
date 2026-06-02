"""
Database operations for auto broadcast (autogcast) tasks.
Collection: autogcast
"""

from datetime import datetime, timezone
from database.mongo import get_collection
from utils.logger import logger

COLLECTION = "autogcast"


async def save_autogcast(
    session_name: str,
    user_id: int,
    interval_minutes: int,
    message: str,
    all_sessions: bool = False,
) -> str:
    """Create or update an autogcast entry. Returns the task_id."""
    col = await get_collection(COLLECTION)

    task_id = f"agc_{session_name.lower()}_{int(datetime.now(timezone.utc).timestamp())}"

    # Remove existing task for same session
    await col.delete_many({"session_name": session_name.lower(), "all_sessions": all_sessions})

    doc = {
        "task_id": task_id,
        "session_name": session_name.lower(),
        "user_id": user_id,
        "interval_minutes": interval_minutes,
        "message": message,
        "all_sessions": all_sessions,
        "active": True,
        "last_run": None,
        "next_run": None,
        "run_count": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    await col.insert_one(doc)
    
    return task_id


async def get_all_active_autogcast() -> list[dict]:
    """Return all active autogcast tasks."""
    col = await get_collection(COLLECTION)
    return await col.find({"active": True}).to_list(length=None)


async def get_autogcast_by_session(session_name: str) -> dict | None:
    col = await get_collection(COLLECTION)
    return await col.find_one({
        "session_name": session_name.lower(),
        "active": True
    })


async def stop_autogcast_by_session(session_name: str) -> bool:
    col = await get_collection(COLLECTION)
    result = await col.update_many(
        {"session_name": session_name.lower(), "active": True},
        {"$set": {"active": False, "updated_at": datetime.now(timezone.utc)}}
    )
    return result.modified_count > 0


async def stop_all_autogcast() -> int:
    col = await get_collection(COLLECTION)
    result = await col.update_many(
        {"active": True},
        {"$set": {"active": False, "updated_at": datetime.now(timezone.utc)}}
    )
    return result.modified_count


async def update_run_times(task_id: str, last_run: datetime, next_run: datetime):
    col = await get_collection(COLLECTION)
    await col.update_one(
        {"task_id": task_id},
        {"$set": {
            "last_run": last_run,
            "next_run": next_run,
            "updated_at": datetime.now(timezone.utc),
        }, "$inc": {"run_count": 1}}
    )


async def get_all_autogcast_status() -> list[dict]:
    """Return all autogcast tasks (active or not) for status display."""
    col = await get_collection(COLLECTION)
    return await col.find({}).sort("created_at", -1).to_list(length=50)
