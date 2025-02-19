from datetime import datetime
import pytz

from aiogram import Router, types
from aiogram.filters import Command
from db import add_task, delete_tasks, get_tasks, update_task, done_task, delete_done_tasks

router = Router()


@router.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! Я бот-планировщик задач. Используйте /add, /tasks, /edit, /delete, /done, /delete_done."
    )


@router.message(Command("add"))
async def add(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Используйте: /add text YYYY-MM-DD HH:MM")
        return

    ans = args[1]
    parts = ans.rsplit(maxsplit=2)
    if len(parts) < 3:
        await message.answer("Используйте: /add text YYYY-MM-DD HH:MM")
        return

    text, deadline = parts[0], parts[1] + " " + parts[2]

    task_id = add_task(str(message.from_user.id), text, deadline)
    await message.answer(f"Задача добавлена! ID: {task_id}")

@router.message(Command("tasks"))
async def tasks(message: types.Message):
    user_id = str(message.from_user.id)
    user_tasks = get_tasks(user_id)
    if not user_tasks:
        await message.answer("У вас нет задач.")
        return

    msg = "Ваши задачи:\n"
    now_utc = datetime.utcnow()
    msk_timezone = pytz.timezone('Europe/Moscow')
    now_msk = now_utc.replace(tzinfo=pytz.utc).astimezone(msk_timezone)

    for task in user_tasks:
        try:
            deadline_str = task["deadline"]
            deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")

            deadline_msk = msk_timezone.localize(deadline)
            remaining_seconds = (deadline_msk - now_msk).total_seconds()
            remaining_hours = remaining_seconds // 3600

            status = (
                "Завершено" if task.get("status") == "done" else f"Осталось {remaining_hours:.0f} ч."
            )
            msg += f"{task['_id']}: {task['text']} ({status})\n"
        except ValueError as e:
            print(f"Ошибка при обработке даты задачи {task['_id']}: {e}")
            msg += f"Ошибка: Неверный формат даты для задачи {task['_id']}\n"

    await message.answer(msg)

@router.message(Command("edit"))
async def edit(message: types.Message):
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("Используйте: /edit task_id new_text")
        return

    task_id, new_text = args[1], args[2]
    update_task(str(message.from_user.id), task_id, new_text)
    await message.answer("Задача обновлена!")


@router.message(Command("delete"))
async def delete(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Используйте: /delete YYYY-MM-DD")
        return

    delete_tasks(str(message.from_user.id), args[1])
    await message.answer(f"Удалены задачи на {args[1]}")

@router.message(Command("done"))
async def done(message: types.Message):
    args = message.text.split()
    if len(args)< 2:
        await message.answer("Используйте /done task_id")
        return
    done_task(str(message.from_user.id), args[1])
    await message.answer(f"Задача {args[1]} выполнена")

@router.message(Command("delete_done"))
async def delete_done(message: types.Message):
    delete_done_tasks(str(message.from_user.id))
    await message.answer(f"Удалены выполненные задачи")