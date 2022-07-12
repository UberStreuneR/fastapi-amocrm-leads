import aiohttp, asyncio
import json
from logger import logger
from auth import update_token

async def request_or_retry(url, request_type, session, headers=None, params=None, data=None, seconds=0, add=None):

    if request_type == "GET":
        async with session.get(url, headers=headers, params=params) as request:
            try:
                response = await request.json()
                return response
            except aiohttp.client_exceptions.ContentTypeError as e:
                logger.exception(e)

    elif request_type == "POST":
        async with session.post(url, headers=headers, params=params, data=json.dumps(data)) as request:
            try:
                response = await request.json()
                return response
            except aiohttp.client_exceptions.ContentTypeError as e:
                logger.exception(e)

    elif request_type == "PATCH":
        async with session.patch(url, headers=headers, data=data) as request:
            try:
                response = await request.json()
                return response
            except aiohttp.client_exceptions.ContentTypeError as e:
                logger.exception(e)
                
    elif request_type == "DELETE":
        async with session.delete(url, headers=headers, params=params, data=json.dumps(data)) as request:
            try:
                response = await request.json()
                return response
            except aiohttp.client_exceptions.ContentTypeError as e:
                logger.exception(e)
    
    request_kwargs = {
        'url': url,
        'request_type': request_type,
        'session': session,
        'headers': headers,
        'params': params,
        'data': data,
        'seconds': seconds + 5
    }

    if request.status == 429:
        if seconds > 50:
            return
        # logger.info(f"AWAITING {seconds + 5} seconds\nRESPONSE {await request.text()}")
        await asyncio.sleep(seconds + 5)
        return await request_or_retry(**request_kwargs)
    elif request.status == 401:    
        await update_token()
        return await request_or_retry(**request_kwargs)