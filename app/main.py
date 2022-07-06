from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from aiohttp import ClientSession
import aiofiles
import requests
import asyncio
from datetime import datetime, timedelta
import os
import json

import logging, sys

logging.basicConfig(
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
    level=logging.DEBUG,
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger("Sockets")
logging.getLogger("chardet.charsetprober").disabled = True



app = FastAPI(docs_url=None, redoc_url=None)


"""Для отображения docs, в силу того что дефолтный cdn не подгружается"""
app.mount("/my_static", StaticFiles(directory="static"), name="static")

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/my_static/swagger-ui-bundle.js",
        swagger_css_url="/my_static/swagger-ui.css",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


API_URL = "https://devks.amocrm.ru/api/v4"
# API_RUL = os.environ.get("API_URL")
"""API_KEY будет устанавливаться изначально через os.environ.get("API_KEY"),
   а затем изменяться через os.environ["API_KEY"] = *new_value*
   Тогда мы не будем подключать ради него БД.
"""

async def make_auth_request(auth_endpoint, data):
    r = requests.post(auth_endpoint, data=data)
    if r.status_code == 200:
        response_data = r.json()
        token = response_data['access_token']
        refresh_token = response_data['refresh_token']
        async with aiofiles.open("creds.json", "w") as file:
            data = {
                "API_KEY": token,
                "REFRESH_KEY": refresh_token
            }
            await file.write(json.dumps(data))
        return token
    return None

@app.on_event("startup")
async def update_or_set_token():
    logger.info("UPDATE TOKEN UTILITY CALLED")
    auth_endpoint = "https://devks.amocrm.ru/oauth2/access_token"
    INTEGRATION_ID = os.environ.get("INTEGRATION_ID")
    SECRET_KEY = os.environ.get("SECRET_KEY")
    API_KEY, REFRESH_KEY = await get_api_key()
    data = {
        'client_id': INTEGRATION_ID,
        'client_secret': SECRET_KEY,
        'redirect_uri': 'https://example.com'
    }
    if API_KEY is None: # as it is initially
        AUTH_KEY = os.environ.get("AUTH_KEY")
        logger.info(f"SECRET_KEY {SECRET_KEY}\nAUTH_KEY {AUTH_KEY}\nINTEGRATION_ID {INTEGRATION_ID}")
        data.update({
            'grant_type': 'authorization_code',
            'code': AUTH_KEY,
        })
    else: # if the key is stale or we got HTTP401
        data.update({
            'grant_type': 'refresh_token',
            'refresh_token': REFRESH_KEY,
        })
    token = await make_auth_request(auth_endpoint, data)
    return token


async def get_api_key():
    try:
        async with aiofiles.open("creds.json", 'r') as file:
            data = await file.read()
            try:
                json_data = json.loads(data)
                API_KEY = json_data.get('API_KEY')
                REFRESH_KEY = json_data.get('REFRESH_KEY')
                return API_KEY, REFRESH_KEY
            except:
                return None, None
    except FileNotFoundError:
        return None, None

class HTTP401Exception(Exception):
    pass



async def get_leads(id: int, is_company: bool, session: ClientSession):
    """Получает информацию о контакте или компании и возвращает список лидов"""


    api_key, refresh_key = await get_api_key()
    logger.info(f"Get leads called, api key: {api_key}")
    headers = {
        'Authorization': f"Bearer {api_key}"
    }
    params = {
        "with": "leads"
    }
    if is_company:
        addendum = f"/companies/{id}"
    else:
        addendum = f"/contacts/{id}"
    async with session.get(API_URL + addendum, headers=headers, params=params) as response:
        if response.status == 200:
            logger.info("STATUS 200")
            content = await response.json()
            return content['_embedded']['leads']
        elif response.status == 401:
            logger.info("STATUS 401")
            raise HTTP401Exception
        else:
            logger.info(f"STATUS {response.status}")

async def check_lead(lead_link, session, months):
    """Делает запрос по ссылке лида, проверяет, что создан не позже 6 месяцев назад.
       Возвращает сумму оплаты лида, если тот оплачен"""
    api_key, refresh_key = await get_api_key()
    headers = {
    'Authorization': f"Bearer {api_key}"
    }
    async with session.get(lead_link, headers=headers) as response:
        content = await response.json()
        created_at = content['created_at']
        date = datetime.fromtimestamp(created_at)
        if datetime.now() - date > timedelta(days=int(months)*30):
            return None
        try:
            if content['custom_fields_values'][0]['values'][0]['value'] == 'Оплата получена':
                return content['price']
        except TypeError:
            return None


@app.get("/successful-leads/{id}")
async def successful_leads(id: int, is_company: bool, months):
    """Path-function для выведения количества успешных лидов контакта или компании за последние 6 месяцев"""
    async with ClientSession() as session:

        try:
            leads = await get_leads(id, is_company, session)
        except HTTP401Exception:
            await asyncio.create_task(update_or_set_token())
            leads = await asyncio.create_task(get_leads(id, is_company, session))
        tasks = []
        for lead in leads:
            tasks.append(check_lead(lead['_links']['self']['href'], session, months))
        results = await asyncio.gather(*tasks)
        while None in results:
            results.remove(None)
        print(results)
        return {f"Amount": len(results), "Sum": sum(results), "id": id, "is_company": is_company}

# @app.get("/test")
# async def test_func(api_key:str = Depends(get_api_key)):
#     print(api_key)
#     await update_or_set_token()
#     api_keys = await get_api_key()
#     print(api_keys)

#     return api_key