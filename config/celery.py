import os
from kombu import Queue, Exchange
from celery import Celery
from config.settings import LOCAL_QUEUE_NAME,HIGH_PRIORITY_QUEUE

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("kubechat")
app.conf.task_queues = (
    Queue(LOCAL_QUEUE_NAME, Exchange(LOCAL_QUEUE_NAME), routing_key=LOCAL_QUEUE_NAME),
    Queue(HIGH_PRIORITY_QUEUE, Exchange(HIGH_PRIORITY_QUEUE), routing_key=HIGH_PRIORITY_QUEUE, priority=10),
)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")


# Load task modules from all registered Django app configs.
app.autodiscover_tasks()



if LOCAL_QUEUE_NAME != "":
    app.conf.task_routes = {
        'myapp.tasks.urgent_task': {'queue': HIGH_PRIORITY_QUEUE, 'routing_key': HIGH_PRIORITY_QUEUE},
        "kubechat.tasks.index.add_index_for_local_document": {"queue": f"{LOCAL_QUEUE_NAME}"},
        '*': {'queue': LOCAL_QUEUE_NAME},
    }

if __name__ == "__main__":
    app.start()