import os
import queue
import time
from app.settings.utils import ContactManager, CompanyManager, HookHandler
from celery import Celery
from kombu import Queue, Exchange
from app.integrations.deps import get_amocrm_from_first_integration
from sqlmodel import Session
from app.database import engine


app = Celery(__name__)
app.conf.broker_url = os.environ.get("CELERY_BROKER_URL")
# app.autodiscover_tasks(packages=['app'])


@app.task(name="print_number", queue="settings")
def print_number(number: int):
    return number


@app.task(name="handle-hook", queue="settings")
def background_request(request_data):
    amocrm = get_amocrm_from_first_integration()
    with Session(engine) as session:
        contact_manager = ContactManager(amocrm, session)
        company_manager = CompanyManager(amocrm, session)

        handler = HookHandler(contact_manager, company_manager, amocrm)
        handler.handle(request_data)
        session.commit()


app.conf.task_queues = (
    Queue('settings', Exchange('settings', type='topic',
          auto_delete=True), routing_key='worker.*'),
)
