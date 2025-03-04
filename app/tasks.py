from celery_config import celery

def set_notification_task(user_id, text, diff):
    send_notification.apply_async(args=(user_id, text), eta=diff)

@celery.task
def send_notification(user_id, text):
    return

@celery.task # если есть просроченные, то идет вызов send_info_expired_tasks
def check_expired_tasks():
    return

@celery.task
def send_info_expired_tasks(user_id, task_id):
    return
