from datetime import datetime

import pytz
from aiogram import Router, types
from aiogram.filters import Command
from db import (
    add_task,
    delete_done_tasks,
    delete_tasks,
    done_task,
    get_tasks,
    update_task,
)
from tasks import set_notification_task

from app.cryption import decrypt_text, encrypt_text

router = Router()


@router.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! Я бот-планировщик задач. Используйте /add, /tasks, /edit, /delete, /done, /delete_done, /set_notification."
    )


@router.message(Command("add"))
async def add(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Используйте: /add text importance YYYY-MM-DD HH:MM где importance 1 - низкая важность, 2 - средняя, 3 - высокая"
        )
        return

    ans = args[1]
    parts = ans.rsplit(maxsplit=3)
    if len(parts) < 4:
        await message.answer(
            "Используйте: /add text importance YYYY-MM-DD HH:MM где importance 1 - низкая важность, 2 - средняя, 3 - высокая"
        )
        return

    text, deadline, importance = parts[0], parts[2] + " " + parts[3], parts[1]

    try:
        datetime.strptime(deadline, "%Y-%m-%d %H:%M")
    except ValueError:
        await message.answer("Неверный формат даты. Используйте: YYYY-MM-DD HH:MM")
        return

    if importance.isdigit():
        if int(importance) < 1 or int(importance) > 3:
            await message.answer(
                "Используйте: /add text importance YYYY-MM-DD HH:MM где importance 1 - низкая важность, 2 - средняя, 3 - высокая"
            )
            return
    else:
        await message.answer(
            "Используйте: /add text importance YYYY-MM-DD HH:MM где importance 1 - низкая важность, 2 - средняя, 3 - высокая"
        )
        return

    now_utc = datetime.now()
    msk_timezone = pytz.timezone("Europe/Moscow")
    now_msk = now_utc.replace(tzinfo=pytz.utc).astimezone(msk_timezone)
    deadline_msk = datetime.strptime(deadline, "%Y-%m-%d %H:%M")
    deadline_msk = msk_timezone.localize(deadline_msk)
    remaining = (deadline_msk - now_msk).total_seconds() // 3600

    if deadline_msk < now_msk:
        await message.answer("Нельзя добавлять задачи в прошлом!")
        return

    if remaining == 0:
        priority = 3
    else:
        priority = int(importance) * (1 / remaining)

    text = encrypt_text(text)

    task_id = add_task(str(message.from_user.id), text, deadline, importance, priority)
    await message.answer(f"Задача добавлена! ID: {task_id}")


@router.message(Command("tasks"))
async def tasks(message: types.Message):
    user_id = str(message.from_user.id)
    user_tasks = get_tasks(user_id)
    if not user_tasks:
        await message.answer("У вас нет задач.")
        return

    msg = "Ваши задачи:\n"
    now_utc = datetime.now()
    msk_timezone = pytz.timezone("Europe/Moscow")
    now_msk = now_utc.replace(tzinfo=pytz.utc).astimezone(msk_timezone)

    for task in user_tasks:
        deadline_str = task["deadline"]
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")

        deadline_msk = msk_timezone.localize(deadline)
        remaining = (deadline_msk - now_msk).total_seconds()

        hours = int(abs(remaining) // 3600)
        minutes = int(abs(remaining) // 60 % 60)
        seconds = int(abs(remaining) % 60)

        status = ""
        if task["status"] == "done":
            status = "Выполнено"
        elif remaining > 0:
            status = f"Осталось {hours} часов {minutes} минут {seconds} секунд"
        else:
            status = f"Просрочено на {hours} часов {minutes} минут {seconds} секунд"

        text = decrypt_text(task["text"])

        msg += f"{task['_id']}: {text} ({status})\n"

    await message.answer(msg)


@router.message(Command("edit"))
async def edit(message: types.Message):
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("Используйте: /edit task_id new_text")
        return

    task_id, new_text = args[1], args[2]

    new_text = encrypt_text(new_text)

    if update_task(str(message.from_user.id), task_id, new_text):
        await message.answer("Задача обновлена!")
    else:
        await message.answer("Указанный task_id не существует!")


@router.message(Command("delete"))
async def delete(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Используйте: /delete YYYY-MM-DD")
        return

    try:
        datetime.strptime(args[1], "%Y-%m-%d")
        if delete_tasks(str(message.from_user.id), args[1]):
            await message.answer(f"Удалены задачи на {args[1]}")
        else:
            await message.answer("Задач на этот день нет")

    except ValueError:
        await message.answer(
            f"Ошибка удаления задач на {args[1]}. Проверьте формат даты."
        )


@router.message(Command("done"))
async def done(message: types.Message):
    args = message.text.split(maxsplit=2)
    if len(args) < 2:
        await message.answer("Используйте /done task_id")
        return
    res = done_task(str(message.from_user.id), args[1])
    if res.modified_count == 0:
        await message.answer(
            f"Задача не выполнена, задача с id {args[1]} не существует"
        )
    else:
        await message.answer(f"Задача {args[1]} выполнена")


@router.message(Command("delete_done"))
async def delete_done(message: types.Message):
    if delete_done_tasks(str(message.from_user.id)):
        await message.answer("Удалены выполненные задачи")
    else:
        await message.answer("Нет выполненных задач")


@router.message(Command("set_notification"))
async def set_notification(message: types.Message):
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("Используйте: /set_notification task_id YYYY-MM-DD HH:MM")
        return

    task_id, deadline = args[1], args[2]
    try:
        deadline = datetime.strptime(deadline, "%Y-%m-%d %H:%M")
    except ValueError:
        await message.answer("Неверный формат даты. Используйте: YYYY-MM-DD HH:MM")
        return

    now_utc = datetime.now()
    msk_timezone = pytz.timezone("Europe/Moscow")
    now_msk = now_utc.replace(tzinfo=pytz.utc).astimezone(msk_timezone)
    deadline_msk = msk_timezone.localize(deadline)
    delay = (deadline_msk - now_msk).total_seconds()

    if delay < 0:
        await message.answer("Указанное время уже прошло.")
        return

    hours = int(delay // 3600)
    minutes = int(delay // 60 % 60)
    seconds = int(delay % 60)

    set_notification_task(
        message.from_user.id, f"Напоминание для задачи {task_id}", int(delay)
    )
    await message.answer(
        f"Напоминание установлено {hours} часов {minutes} минут {seconds} секунд"
    )
