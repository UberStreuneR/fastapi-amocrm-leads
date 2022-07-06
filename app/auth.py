import aiohttp, aiofiles
import json
from settings import settings
import os
import requests

import logging, sys

logging.basicConfig(
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
    level=logging.DEBUG,
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger("Sockets")
logging.getLogger("chardet.charsetprober").disabled = True


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


async def save_credentials(token, refresh_token):
    async with aiofiles.open("creds.json", "w") as file:
        data = {
            "API_KEY": token,
            "REFRESH_KEY": refresh_token
        }
        await file.write(json.dumps(data))


async def load_credentials():
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


async def update_or_set_token():
    auth_endpoint = settings.AUTH_ENDPOINT
    INTEGRATION_ID = os.environ.get("INTEGRATION_ID")
    SECRET_KEY = os.environ.get("SECRET_KEY")

    API_KEY, REFRESH_KEY = await load_credentials()

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

    else: # if the key is stale or we got HTTP401
        data.update({
            'grant_type': 'refresh_token',
            'refresh_token': REFRESH_KEY,
        })

    token = await make_auth_request(auth_endpoint, data)
    return token