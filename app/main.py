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
# API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6ImU3MWQ3OTZlOTY5OTE1NWVjM2NhYjg3MTI3YzM3ZGEyNmM1MTkxZTE3MTg3NTJhOGMwM2ZmOWFmZTNlNTZmZDU5MzhhZjFjYTM4NzZkMzY4In0.eyJhdWQiOiIzNDQ3YzQzMS04OWIxLTQzMWQtYTc3ZC1kZjg5MGFmYjJlMzgiLCJqdGkiOiJlNzFkNzk2ZTk2OTkxNTVlYzNjYWI4NzEyN2MzN2RhMjZjNTE5MWUxNzE4NzUyYThjMDNmZjlhZmUzZTU2ZmQ1OTM4YWYxY2EzODc2ZDM2OCIsImlhdCI6MTY1NzA4NjQ0MSwibmJmIjoxNjU3MDg2NDQxLCJleHAiOjE2NTcxNzI4NDEsInN1YiI6IjgyNzIxMjYiLCJhY2NvdW50X2lkIjozMDE0OTk1OSwic2NvcGVzIjpbInB1c2hfbm90aWZpY2F0aW9ucyIsImZpbGVzIiwiY3JtIiwiZmlsZXNfZGVsZXRlIiwibm90aWZpY2F0aW9ucyJdfQ.Btb-SunbGjcVaO8p7mxb6mVHrg6Vz1fAt1nt5tr55ka1Xst0C9Nxf5TAtslYXEzz3rk8afzaWaB4vGVqqlF-ieztvtIzSfnyiBrJf5ByLMUg6OWE5_4nFY6xvrS3NjTbPLx0rAjDotg_B8A2HjmqQqZ0FW0fVNemkNLzwo9XtZ8422w4q7JdM0TESI4EKAXmMwbHtOky3LZXTH22tjvxcMuzI_6cfVni_4dD5y_f_IxLcZq1vCWfsriRpZoC3mufDVp3RlcARsZyjGn2ld3_YJ7L0-eQrD2bV-rKzH_CnLiVX38VZl8pQ0fOcrXNz22MbsHdhSg29JVVgP3-o4U-XA"
# API_KEY = os.environ.get("API_KEY"), initially should be None
# REFRESH_KEY = "def5020090d9bdc2ffb8aee2e8566d75cdf9a01cb6bbe743b6ac47def487d0408e2dfe37bc21db2b0c8f8e66b8c824755b439fbdbe0705e9afe3ae40e97c74623109700a5b1413d10a86761a7f975fb483a1d7121ed92660c1ddccebde8a9831637416bc51d7a0160912f234bb529157e8656ebaa6480376c5ad3aa64bda744778807d13769e6ead2b68099cfea47773955b678580089fd9f9148ad93b1d091870fe7cdd87bf34ab0719443a6def99bec30b39373d34a0523a1fc8be9c021bd4fe3ec61858d53dadde4e80cea528dece0f6def80c1caa003721576db1e83c3e2bd78a8af2ad49c9b9ade3b170f2907541851ef768ea5089397e1577e153b4b2cf356b264175e866fdb3d38325ab2cd16883b5794a90d4da8a0ed5e8197e51266c1601af98038405e82421f6e9ac30745f56a814e448a83650bd73857104ca69cfce769499d8a4dc3cf5c2cbc5a869402a10f0cbba243cf7d78f8bb827d7723720580dcc79137a8d0ab85ab4050d33bffd19ecc116b75e8d3ee8b385c415dedf70a90235ad3c05c9ca5511d2d1e6d8a979fe48d52fa613aa82f08c9b15a2d4d270b17f880b17fc3a3626ae36141ccdc0946117f71a84a9eb4e0c1c4d87d9602b92c5babe6d670307b0bea815181ee21f8cfc897182bc212a35856cce311d4a197db"
# REFRESH_KEY = os.environ.get("REFRESH_KEY"), initially should be None

# AUTH_KEY = "def5020098a6093b2db00a20b3e4c4bb68c15b04992960c491d68f24cf8f0085dbb23392b38caf18dfbd1f968815dd3c97f369aca6c71cfe4914fcc31f6b7cd6a0e431ab7b39e79407cd5cc4c7bcbaa905af11839576a64a2cff4baa5f7c22d11936ece8c7a66d36fa2678b16c59ff95326e56b9825a9fa482e9e972b12b46aa442d8afad24a13320a22b4246e24af909862e1388856cbcf243ab9572015ca66a979408c663486384e8143a89b6f32811e49be98c2ef52120be80fe09243983f22a4e62071000505e36b22b31d5f6632f30c3353028d0b7ff21ead0ed4a5d6b27ea506a0563d23db649e79cb0a8c754cf8b133dd92aa7099eaf24a7ae7c1f8096508c4bfb0ab28943144c3fb16caa4313f0bb4cf30a102406ad9a464360027cc943ca815786a3a70f376aa28bdd427ff9fb56474042b371602f5b2787e62ef522b8c980286b2c6d3bdbad57ee5b630ae0ae04b23b4e3f649fe47962dea5fcbfc3e72621fc2fc703289514564c11b4ce5b27b3d680bffcd18eadd4fd39330bcd822dd94affe07d65fd32e7a9fa02c408f86ee13c5e3430ff207bd736b15228e41671f642d6471e850545163c690651002d717d55b49dc6dc78516b042f690391d615dcf588afa9d8b8f2bcbba7629dd859d71ea00"
#AUTH_KEY = os.environ.get("AUTH_KEY")
# SECRET_KEY = "7Ph7FpgB4egqmlM2iyFNA8dAisOqobmiXEanm1uVBx6VExcrvyS8MNmgo8fpgrDv"

# @app.middleware("http")
# async def catch_exceptions_middleware(request: Request, call_next):
#     try:
#         return await call_next(request)
#     except HTTPException:
#         # you probably want some kind of logging here
#         await update_or_set_token()
#         logger.info("Hopefully updated the token")
#         return await call_next(request)



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

# @app.on_event("startup")
async def update_or_set_token():
    logger.info("UPDATE TOKEN UTILITY CALLED")
    auth_endpoint = "https://devks.amocrm.ru/oauth2/access_token"
    integration_id = os.environ.get("INTEGRATION_ID")
    SECRET_KEY = os.environ.get("SECRET_KEY")
    API_KEY, REFRESH_KEY = await get_api_key()
    data = {
        'client_id': integration_id,
        'client_secret': SECRET_KEY,
        'redirect_uri': 'https://example.com'
    }
    if API_KEY is None: # as it is initially
        AUTH_KEY = os.environ.get("AUTH_KEY")
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

    # credentials_exception = HTTPException(
    #     status_code=status.HTTP_401_UNAUTHORIZED,
    #     detail="Could not validate credentials",
    #     headers={"WWW-Authenticate": "Bearer"},
    # )

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
            # update_or_set_token()
            # return get_leads(id, is_company, session)
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
        # print(content)
        created_at = content['created_at']
        date = datetime.fromtimestamp(created_at)
        if datetime.now() - date > timedelta(days=int(months)*30):
            return None
        try:
            if content['custom_fields_values'][0]['values'][0]['value'] == 'Оплата получена':
                return content['price']
        except TypeError:
            return None


# def get_leads_and_update_if_needed(get_leads_function, update_function, *args):
#     async def wrapper():
#         try:
#             return await get_leads_function(*args)
#         except HTTPException:
#             await update_function()
#             return await get_leads_function(*args)
#     return wrapper

@app.get("/successful-leads/{id}")
async def successful_leads(id: int, is_company: bool, months):
    """Path-function для выведения количества успешных лидов контакта или компании за последние 6 месяцев"""
    async with ClientSession() as session:

        # leads = await asyncio.create_task(get_leads(id, is_company, session))
        get_leads_params = (id, is_company, session)
        # leads = await asyncio.create_task(get_leads_and_update_if_needed(get_leads, update_or_set_token, *get_leads_params)())
        try:
            leads = await get_leads(id, is_company, session)
            # leads = await asyncio.create_task(get_leads(id, is_company, session))
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

@app.get("/test")
async def test_func(api_key:str = Depends(get_api_key)):
    print(api_key)
    await update_or_set_token()
    api_keys = await get_api_key()
    print(api_keys)
    # auth_endpoint = "https://devks.amocrm.ru/oauth2/access_token"
    # data = {
    #     'client_id': integration_id,
    #     'client_secret': secret_key,
    #     'grant_type': 'refresh_token',
    #     # 'grant_type': 'authorization_code',
    #     'refresh_token': refresh,
    #     # 'code': auth_token,
    #     'redirect_uri': 'https://example.com'
    # }
    # requests.post(auth_endpoint)
    return api_key