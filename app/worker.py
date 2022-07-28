import os
from celery import Celery
from kombu import Queue, Exchange


app = Celery(__name__)
app.conf.broker_url = os.environ.get("CELERY_BROKER_URL")
app.autodiscover_tasks(packages=['app.settings'])


app.conf.task_queues = (
    Queue('settings', Exchange('settings', type='topic',
          auto_delete=True), routing_key='app.settings.*'),
)

app.conf.task_routes = {
    "app.settings.tasks.*": {"queue": "settings", 'routing_key': "app.settings.tasks"}}
