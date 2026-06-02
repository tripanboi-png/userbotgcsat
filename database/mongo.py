"""
MongoDB connection manager using Motor async driver.
Provides a singleton database client.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DB_NAME
from utils.logger import logger

_client: AsyncIOMotorClient | None = None
_db = None


async def get_db():
    global _client, _db
    if _db is None:
        _client = AsyncIOMotorClient(MONGO_URI)
        _db = _client[DB_NAME]
        # Ping to validate connection
        await _client.admin.command("ping")
        logger.info(f"[MongoDB] Connected to database: {DB_NAME}")
    return _db


async def close_db():
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("[MongoDB] Connection closed.")


async def get_collection(name: str):
    db = await get_db()
    return db[name]
