import asyncio
import logging

from aiogram import Bot, Dispatcher
from handlers import router

from app.celery_config import celery_app as celery_app
from app.config import TOKEN

logging.basicConfig(level=logging.INFO)


async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
