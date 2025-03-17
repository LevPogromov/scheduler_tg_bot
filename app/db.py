from bson.objectid import ObjectId
from pymongo import MongoClient

from app.config import NAME_OF_COLLECTION, NAME_OF_DATABASE, URI

client = MongoClient(URI)
db = client[NAME_OF_DATABASE]
collection = db[NAME_OF_COLLECTION]


def add_task(user_id, text, deadline, importance, priority):
    task = {
        "user_id": user_id,
        "text": text,
        "importance": importance,
        "priority": priority,
        "deadline": deadline,
        "status": "pending",
    }
    result = collection.insert_one(task)
    return str(result.inserted_id)


def get_tasks(user_id):
    tasks = list(collection.find({"user_id": user_id}).sort("priority", -1))
    for task in tasks:
        task["_id"] = str(task["_id"])
    return tasks


def update_task(user_id, task_id, new_text):
    res = collection.update_one(
        {"user_id": user_id, "_id": ObjectId(task_id)}, {"$set": {"text": new_text}}
    )
    return res.modified_count != 0


def delete_tasks(user_id, date):
    res = collection.delete_many(
        {"user_id": user_id, "deadline": {"$regex": f"^{date}"}}
    )
    return res.deleted_count != 0


def done_task(user_id, task_id):
    res = collection.update_one(
        {"user_id": user_id, "_id": ObjectId(task_id)},
        {"$set": {"status": "done"}},
        upsert=False,
    )
    return res


def delete_done_tasks(user_id):
    res = collection.delete_many({"user_id": user_id, "status": "done"})
    return res.deleted_count != 0
