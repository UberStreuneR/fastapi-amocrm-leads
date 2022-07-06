import aiohttp, aiofiles
import asyncio
from datetime import datetime, timedelta
from exceptions import HTTP401Exception
from settings import settings
from auth import load_credentials, update_or_set_token


async def prepare_headers_and_params():

    api_key, refresh_key = await load_credentials()
    headers = {
        'Authorization': f"Bearer {api_key}"
    }
    params = {
        "with": "leads"
    }

    return headers, params
    
    

async def get_leads(id: int, is_company: bool, session: aiohttp.ClientSession):
    """Получает информацию о контакте или компании и возвращает список лидов"""

    headers, params = await prepare_headers_and_params()

    if is_company:
        addendum = f"/companies/{id}"
    else:
        addendum = f"/contacts/{id}"
    async with session.get(settings.API_URL + addendum, headers=headers, params=params) as response:
        if response.status == 200:
            content = await response.json()
            return content['_embedded']['leads']
        elif response.status == 401:
            raise HTTP401Exception
        else:
            pass


async def check_lead(lead_link, session, months):
    """Делает запрос по ссылке лида, проверяет, что создан не позже 6 месяцев назад.
       Возвращает сумму оплаты лида, если тот оплачен"""
    
    api_key, refresh_key = await load_credentials()
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


async def get_count_success_leads(id: int, is_company: bool, months: int):
    async with aiohttp.ClientSession() as session:

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
        return results