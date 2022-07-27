import os
import time
from app.settings.utils import ContactManager, CompanyManager, HookHandler
from celery import Celery
from kombu import Queue, Exchange

app = Celery(__name__)
app.conf.broker_url = os.environ.get("CELERY_BROKER_URL")
# app.autodiscover_tasks(packages=['app'])


@app.task(name="print_number", queue="settings")
def print_number(number: int):
    return number


@app.task(name="handle-hook")
async def background_request(request_data, amocrm, session):
    contact_manager = ContactManager(amocrm, session)
    company_manager = CompanyManager(amocrm, session)

    handler = HookHandler(contact_manager, company_manager, amocrm)
    await handler.handle(request_data)


app.conf.task_queues = (
    Queue('settings', Exchange('settings', type='topic',
          auto_delete=True), routing_key='worker.*'),
)
