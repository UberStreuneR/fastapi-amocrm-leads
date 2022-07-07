import aiohttp, aiofiles
import asyncio
from datetime import datetime, timedelta
import json
from fastapi import Request
from exceptions import HTTP401Exception
from settings import settings
from auth import load_credentials, update_token
from querystring_parser import parser
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


async def prepare_headers():

    api_key, refresh_key = await load_credentials()
    headers = {
        'Authorization': f"Bearer {api_key}"
    }
    
    return headers
    

async def prepare_hook():
    headers = await prepare_headers()
    host_url = settings.HOST_URL
    webhook_url = settings.API_URL + "/webhooks"
    webhook_post_data = {
        'destination': host_url,
        'settings': ['restore_lead', 'add_lead', 'update_lead', 'status_lead']
    }
    params = {
        "filter[destination]": host_url
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(webhook_url, headers=headers, params=params) as response:
            response_data = await response.json()
        if host_url not in str(response_data):
            await session.post(webhook_url, headers=headers, data=json.dumps(webhook_post_data))


async def delete_hook():
    
    headers = await prepare_headers()
    host_url = settings.HOST_URL
    webhook_url = settings.API_URL + "/webhooks"
    webhook_post_data = {
        'destination': host_url,
    }
    # requests.delete(webhook_url, headers=headers, data=json.dumps(webhook_post_data))
    async with aiohttp.ClientSession() as session:
        await session.delete(webhook_url, headers=headers, data=json.dumps(webhook_post_data))


async def get_leads(id: int, is_company: bool, session: aiohttp.ClientSession):
    """Получает информацию о контакте или компании и возвращает список лидов"""

    headers = await prepare_headers()
    params = {
        "with": "leads"
    }

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
    
    headers = await prepare_headers()

    async with session.get(lead_link, headers=headers) as response:
        content = await response.json(content_type=None)
        # logger.info(f"LEAD CONTENT \n\n\n{content}\n\n\n")
        created_at = content['created_at']
        date = datetime.fromtimestamp(created_at)
        if datetime.now() - date > timedelta(days=int(months)*30):
            return None
        try:
            if content['custom_fields_values'][0]['values'][0]['value'] == 'Оплата получена':
                # logger.info(f"FIELD VALUE {content['custom_fields_values'][0]['values'][0]['value']}")
                return content['price']
            elif not 'Этап &quot;Закрыто&quot;' in str(content['custom_fields_values']):
                return "Open Lead"
        except TypeError:
            return None


async def get_count_success_leads(id: int, is_company: bool, months: int, session: aiohttp.ClientSession):

    try:
        leads = await get_leads(id, is_company, session)
    except HTTP401Exception:
        await asyncio.create_task(update_token())
        leads = await asyncio.create_task(get_leads(id, is_company, session))

    tasks = []
    for lead in leads:
        tasks.append(check_lead(lead['_links']['self']['href'], session, months))

    results = await asyncio.gather(*tasks)

    while None in results:
        results.remove(None)
    return results


async def get_json_from_hook(request: Request):
    if request.headers['Content-Type'] == 'application/x-www-form-urlencoded':
        data = await request.body()
        json_data = parser.parse(data, normalized=True)
        return json_data

def get_lead_id(data):
    lead_id = list(data['leads'].items())[0][1][0]['id']
    return lead_id


async def get_lead_main_contact_and_company(data, session: aiohttp.ClientSession):
    params = {
        'with': 'contacts'
    }

    lead_id = get_lead_id(data)
    lead_link = settings.API_URL + f"/leads/{lead_id}"

    headers = await prepare_headers()

    main_contact, company = None, None
    async with session.get(lead_link, params=params, headers=headers) as response:
        content = await response.json()

        contacts = content['_embedded']['contacts']
        for contact in contacts:
            if contact['is_main']:
                main_contact = contact['id']

        company = content['_embedded']['companies']
        try:
            company = company[0]
            return main_contact, company['id']
        except IndexError:
            return main_contact, None
        

async def get_main_contacts_success_leads(contact_id, session: aiohttp.ClientSession):
    results = await get_count_success_leads(contact_id, is_company=False, months=6, session=session)
    return results

async def get_company_success_leads(company_id, session: aiohttp.ClientSession):
    results = await get_count_success_leads(company_id, is_company=True, months=6, session=session)
    return results

async def update_company_leads_sum_field(company_id, sum_of_leads: int, session: aiohttp.ClientSession):

    headers= await prepare_headers()

    url = settings.API_URL + f"/companies/{company_id}"
    fields_data = {
        "custom_fields_values": [{
            'field_id': settings.COMPANY_FIELD_ID,
            'values': [
                {
                    "value": sum_of_leads
                }
            ]
        }]
    }
    async with session.patch(url, headers=headers, data=json.dumps(fields_data)) as response:
        r = await response.json()
        logger.info(f"Response: {r}")
    logger.info(f"COMPANY UPDATED {company_id}, value {sum_of_leads}")

async def update_contact_leads_amount_field(contact_id, amount: int, session: aiohttp.ClientSession):
    headers= await prepare_headers()

    url = settings.API_URL + f"/contacts/{contact_id}"
    fields_data = {
        "custom_fields_values": [{
            'field_id': settings.CONTACTS_FIELD_ID,
            'values': [
                {
                    "value": amount
                }
            ]
        }]
    }
    async with session.patch(url, headers=headers, data=json.dumps(fields_data)) as response:
        r = await response.json()
        logger.info(f"Response: {r}")
    logger.info(f"CONTACT UPDATED {contact_id}, value {amount}")

async def update_active_lead_main_contact_amount(lead_id, amount: int, session: aiohttp.ClientSession):
    
    lead_link = settings.API_URL + f"/leads/{lead_id}"

    check_lead_result = await check_lead(lead_link, session, months=6)
    if check_lead_result == "Open Lead":
        headers= await prepare_headers()
        fields_data = {
            "custom_fields_values": [{
                'field_id': settings.LEADS_FIELD_ID,
                'values': [
                    {
                        "value": amount
                    }
                ]
            }]
        }
        async with session.patch(lead_link, headers=headers, data=json.dumps(fields_data)) as response:
            r = await response.json()
            logger.info(f"Response: {r}")
        logger.info(f"OPEN LEAD UPDATED {lead_id}, value {amount}")


async def handle_hook(data, session: aiohttp.ClientSession):
    main_contact_id, company_id = await get_lead_main_contact_and_company(data, session)
    main_contact_results = await get_main_contacts_success_leads(main_contact_id, session)
    # print(main_contact_results)
    if company_id is not None:
        company_results = await get_company_success_leads(company_id, session)

        while "Open Lead" in company_results:
            company_results.remove("Open Lead")

        company_results_sum = sum(company_results)
        await update_company_leads_sum_field(company_id, company_results_sum, session)

    await update_contact_leads_amount_field(main_contact_id, len(main_contact_results), session)


    lead_id = get_lead_id(data)
    await update_active_lead_main_contact_amount(lead_id, len(main_contact_results), session)