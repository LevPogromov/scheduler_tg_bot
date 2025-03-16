import asyncio
from datetime import datetime, timedelta

import pytz
from aiogram import Bot
from celery import shared_task

from app.config import TOKEN
from app.db import collection


def get_bot():
    return Bot(token=TOKEN)


def set_notification_task(user_id, text, diff):
    send_notification.apply_async(args=[user_id, text], countdown=diff)


@shared_task(name="send_notification")
def send_notification(user_id, text):
    async def async_send():
        bot = get_bot()
        await bot.send_message(chat_id=user_id, text=text)
        await bot.session.close()

    asyncio.run(async_send())


@shared_task(name="send_info_expired_tasks")
def send_info_expired_tasks():
    now_utc = datetime.now()
    msk_timezone = pytz.timezone("Europe/Moscow")
    now_msk = now_utc.replace(tzinfo=pytz.utc).astimezone(msk_timezone)

    overdue_tasks = collection.find(
        {"deadline": {"$lt": now_msk.strftime("%Y-%m-%d %H:%M")}, "status": "pending"}
    )

    async def async_send_info_expired_tasks():
        bot = get_bot()
        msk_timezone = pytz.timezone("Europe/Moscow")
        for task in overdue_tasks:
            now_utc = datetime.now()
            now_msk = now_utc.replace(tzinfo=pytz.utc).astimezone(msk_timezone)
            task_deadline = datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M")
            new_deadline = task_deadline + timedelta(days=1)
            deadline_msk = msk_timezone.localize(new_deadline)
            remaining = (deadline_msk - now_msk).total_seconds() // 3600

            if remaining <= 0:
                priority = 3
            else:
                priority = int(task["importance"]) * (1 / remaining)

            new_deadline_str = new_deadline.strftime("%Y-%m-%d %H:%M")

            collection.update_one(
                {"_id": task["_id"]},
                {"$set": {"deadline": new_deadline_str, "priority": priority}},
            )

            await bot.send_message(
                chat_id=task["user_id"],
                text=f"Задача '{task['_id']}' просрочена. Дедлайн перенесен на 1 день.",
            )
        await bot.session.close()

    asyncio.run(async_send_info_expired_tasks())


@shared_task(name="check_priority")
def check_priority():
    all_users = collection.distinct("user_id")
    now_utc = datetime.utcnow()
    msk_timezone = pytz.timezone("Europe/Moscow")
    now_msk = now_utc.replace(tzinfo=pytz.utc).astimezone(msk_timezone)
    for user_id in all_users:
        tasks = list(collection.find({"user_id": user_id}))
        for task in tasks:
            deadline_str = task["deadline"]
            deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")
            deadline_msk = msk_timezone.localize(deadline)
            remaining = (deadline_msk - now_msk).total_seconds() // 3600
            importance = task["importance"]
            if remaining <= 0:
                priority = 3
            else:
                priority = int(importance) * (1 / remaining)

            collection.update_one(
                {"_id": task["_id"]}, {"$set": {"priority": priority}}
            )
