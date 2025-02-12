from utils import load_data, save_data


def add_task(user_id, text, deadline):
    data = load_data()

    if user_id not in data:
        data[user_id] = []

    task = {
        "id": len(data[user_id]) + 1,
        "text": text,
        "deadline": deadline,
        "status": "pending",
    }

    data[user_id].append(task)
    save_data(data)

    return task["id"]


def get_tasks(user_id):
    data = load_data()
    return data[user_id] if user_id in data else []


def update_task(user_id, task_id, new_text):
    data = load_data()

    for task in data[user_id]:
        if task["id"] == int(task_id):
            task["text"] = new_text
            break

    save_data(data)


def delete_tasks(user_id, date):
    data = load_data()
    data[user_id] = [
        task for task in data[user_id] if task["deadline"].split()[0] != date
    ]
    save_data(data)
