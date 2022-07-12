import aiohttp
import json
from utils import load_credentials
from request_template import request_or_retry
from settings import settings

async def prepare_headers():

    api_key, refresh_key = await load_credentials()
    headers = {
        'Authorization': f"Bearer {api_key}"
    }
    
    return headers
    

async def prepare_hook():
    """Проверяет, есть ли хук для текущего хоста, если нет, создает"""

    headers = await prepare_headers()
    host_url = settings.HOST_URL
    webhook_url = settings.API_URL + "/webhooks"

    webhook_post_data = {
        'destination': host_url,
        'settings': ['restore_lead', 'add_lead', 'status_lead']
    }

    params = {
        "filter[destination]": host_url
    }
    
    async with aiohttp.ClientSession() as session:
        request_kwargs = {
            'url': webhook_url,
            'request_type': "GET",
            'session': session,
            'headers': headers,
            'params': params
        }
        response_data = await request_or_retry(**request_kwargs)
        
        if host_url not in str(response_data):
            await request_or_retry(url=webhook_url, request_type="POST", session=session, headers=headers, data=json.dumps(webhook_post_data))


async def get_pipeline_id(session: aiohttp.ClientSession):
    headers = await prepare_headers()
    url = settings.API_URL + "/leads/pipelines"
    async with session.get(url, headers=headers) as r:
        response = await r.json()
        for pipeline in response['_embedded']['pipelines']:
            if pipeline['name'] == "Продажа":
                settings.pipeline_id = pipeline['id']
                return pipeline['id']


async def get_success_stage_id(pipeline_id: int, session: aiohttp.ClientSession):
    headers = await prepare_headers()
    url = settings.API_URL + f"/leads/pipelines/{pipeline_id}"
    async with session.get(url, headers=headers) as r:
        response = await r.json()
        for status in response['_embedded']['statuses']:
            if status['name'] == 'Закрыто. Оплата получена':
                settings.success_stage_id = status['id']


async def prepare_pipeline_and_success_stage_id():
    if settings.pipeline_id is None or settings.success_stage_id is None:
        async with aiohttp.ClientSession() as session:
            pipeline_id = await get_pipeline_id(session)
            await get_success_stage_id(pipeline_id, session)