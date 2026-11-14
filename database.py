import aiosqlite
from config import DATABASE_NAME, FREE_LIMIT

async def init_db():
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                used_pages INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def add_user(telegram_id):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (telegram_id) VALUES (?)",
            (telegram_id,)
        )
        await db.commit()

async def get_user(telegram_id):
    await add_user(telegram_id)
    async with aiosqlite.connect(DATABASE_NAME) as db:
        async with db.execute(
            "SELECT used_pages FROM users WHERE telegram_id = ?",
            (telegram_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result[0]

async def get_remaining_pages(telegram_id):
    used_pages = await get_user(telegram_id)
    return max(0, FREE_LIMIT - used_pages)