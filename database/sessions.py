"""
Database operations for session management.
Collection: sessions
"""

from datetime import datetime, timezone
from database.mongo import get_collection
from utils.logger import logger

COLLECTION = "sessions"


async def add_session(name: str, user_id: int, username: str, session_string: str) -> bool:
    """Insert or update a session record."""
    col = await get_collection(COLLECTION)
    existing = await col.find_one({"user_id": user_id})
    if existing:
        await col.update_one(
            {"user_id": user_id},
            {"$set": {
                "name": name,
                "username": username,
                "session": session_string,
                "active": True,
                "updated_at": datetime.now(timezone.utc),
            }}
        )
        logger.info(f"[Sessions] Updated session for {name} ({user_id})")
    else:
        await col.insert_one({
            "name": name,
            "user_id": user_id,
            "username": username,
            "session": session_string,
            "active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        })
        logger.info(f"[Sessions] Added session for {name} ({user_id})")
    return True


async def get_all_sessions() -> list[dict]:
    """Return all active sessions."""
    col = await get_collection(COLLECTION)
    docs = await col.find({"active": True}).to_list(length=None)
    return docs


async def get_session_by_name(name: str) -> dict | None:
    """Return a session by its display name (case-insensitive)."""
    col = await get_collection(COLLECTION)
    return await col.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}, "active": True})


async def get_session_by_user_id(user_id: int) -> dict | None:
    col = await get_collection(COLLECTION)
    return await col.find_one({"user_id": user_id, "active": True})


async def deactivate_session(user_id: int) -> bool:
    """Soft-delete a session by user_id."""
    col = await get_collection(COLLECTION)
    result = await col.update_one(
        {"user_id": user_id},
        {"$set": {"active": False, "updated_at": datetime.now(timezone.utc)}}
    )
    return result.modified_count > 0


async def delete_session_by_name(name: str) -> dict | None:
    """Find and deactivate a session by name. Returns the session doc."""
    col = await get_collection(COLLECTION)
    doc = await col.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}})
    if doc:
        await col.update_one(
            {"_id": doc["_id"]},
            {"$set": {"active": False, "updated_at": datetime.now(timezone.utc)}}
        )
    return doc


async def count_active_sessions() -> int:
    col = await get_collection(COLLECTION)
    return await col.count_documents({"active": True})
