import asyncio
import logging

from aiogram import Bot, Dispatcher
from config import TOKEN
from handlers import router
from utils import ensure_data_file

logging.basicConfig(level=logging.INFO)


async def main():
    ensure_data_file()
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
