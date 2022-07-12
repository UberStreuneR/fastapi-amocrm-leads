import aiohttp, aiofiles
import json
from settings import settings
import os
import requests
from json_utils import prettify_json

async def make_auth_request(auth_endpoint, data):
    """Производит запрос на получение либо обновление токена"""

    r = requests.post(auth_endpoint, data=data)
    if r.status_code == 200:
        response_data = r.json()
        token = response_data['access_token']
        refresh_token = response_data['refresh_token']
        settings.API_KEY = token
        settings.REFRESH_KEY = refresh_token

        async with aiofiles.open("creds.json", "w") as file:
            data = {
                "API_KEY": token,
                "REFRESH_KEY": refresh_token
            }
            await file.write(prettify_json(json.dumps(data)))

        return token
    return None


async def save_credentials(token, refresh_token):
    """Сохраняет REFRESH_KEY и API_KEY"""

    settings.API_KEY = token
    settings.REFRESH_KEY = refresh_token

    async with aiofiles.open("creds.json", "w") as file:
        data = {
            "API_KEY": token,
            "REFRESH_KEY": refresh_token
        }
        await file.write(json.dumps(data))


async def load_credentials():
    """Загружает REFRESH_KEY и API_KEY"""

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


async def set_token():
    """Устанавливает токен, если его нет (сразу после запуска)"""

    auth_endpoint = settings.AUTH_ENDPOINT
    INTEGRATION_ID = os.environ.get("INTEGRATION_ID")
    SECRET_KEY = os.environ.get("SECRET_KEY")

    API_KEY = settings.API_KEY
    API_KEY_FROM_FILE, REFRESH_KEY_FROM_FILE = await load_credentials()

    if API_KEY_FROM_FILE is not None and REFRESH_KEY_FROM_FILE is not None:
        settings.API_KEY = API_KEY_FROM_FILE
        settings.REFRESH_KEY = REFRESH_KEY_FROM_FILE
        return


    data = {
        'client_id': INTEGRATION_ID,
        'client_secret': SECRET_KEY,
        'redirect_uri': 'https://example.com'
    }

    if API_KEY is None: # as it is initially
        AUTH_KEY = os.environ.get("AUTH_KEY")

        data.update({
            'grant_type': 'authorization_code',
            'code': AUTH_KEY,
        })
        token = await make_auth_request(auth_endpoint, data)
        return token

async def update_token():
    """Обновляет токен"""

    auth_endpoint = settings.AUTH_ENDPOINT
    INTEGRATION_ID = os.environ.get("INTEGRATION_ID")
    SECRET_KEY = os.environ.get("SECRET_KEY")

    REFRESH_KEY = settings.REFRESH_KEY
    # AUTH_KEY, REFRESH_KEY = await load_credentials()

    data = {
        'client_id': INTEGRATION_ID,
        'client_secret': SECRET_KEY,
        'grant_type': 'refresh_token',
        'refresh_token': REFRESH_KEY,
        'redirect_uri': 'https://example.com'
    }

    token = await make_auth_request(auth_endpoint, data)
    await set_token()
    return token