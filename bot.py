import asyncio
from aiogram import Bot, Dispatcher
from config import TOKEN
from database import init_db
from handlers import router

async def main():
    # ساخت دیتابیس
    await init_db()
    # اتصال به تلگرام
    bot = Bot(token=TOKEN)
    # راه‌اندازی Dispatcher
    dp = Dispatcher()
    # ثبت هندلرها
    dp.include_router(router)
    print("BoxOCR Bot is running...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())