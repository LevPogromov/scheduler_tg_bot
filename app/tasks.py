from celery_config import celery


def set_notification_task(user_id, text, diff):
    pass


@celery.task
def send_notification(user_id, text):
    pass


@celery.task  # если есть просроченные, то идет вызов send_info_expired_tasks
def check_expired_tasks():
    pass


@celery.task
def send_info_expired_tasks(user_id, task_id):
    pass
