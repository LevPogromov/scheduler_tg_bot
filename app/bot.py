import asyncio
import logging

from aiogram import Bot, Dispatcher
from config import TOKEN
from handlers import router

from app.celery_config import celery_app as celery_app

logging.basicConfig(level=logging.INFO)


async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
