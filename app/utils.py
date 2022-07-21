import aiohttp
import aiofiles
import asyncio
from datetime import datetime, timedelta
import json
from fastapi import Request, Depends
from exceptions import HTTP401Exception
from settings import settings
from auth import update_token
from querystring_parser import parser
from prepare import prepare_headers
from request_template import request_or_retry
from logger import logger


async def delete_hook():
    """Удаляет хук"""

    headers = await prepare_headers()
    host_url = settings.HOST_URL
    webhook_url = settings.API_URL + "/webhooks"
    webhook_post_data = {
        'destination': host_url,
    }
    async with aiohttp.ClientSession() as session:
        await session.delete(webhook_url, headers=headers, data=json.dumps(webhook_post_data))


async def get_leads(id: int, is_company: bool, session: aiohttp.ClientSession):
    """Получает информацию о контакте или компании и возвращает список лидов"""

    await asyncio.sleep(1)
    headers = await prepare_headers()
    params = {
        "with": "leads"
    }

    if is_company:
        addendum = f"/companies/{id}"
    else:
        addendum = f"/contacts/{id}"

    request_kwargs = {
        'url': settings.API_URL + addendum,
        'request_type': "GET",
        'session': session,
        'headers': headers,
        'params': params
    }
    response = await request_or_retry(**request_kwargs)
    return response['_embedded']['leads']


async def check_lead(lead_link, session, months):
    """Делает запрос по ссылке лида, проверяет, что создан не позже 6 месяцев назад.
       Возвращает сумму оплаты лида, если тот оплачен"""

    await asyncio.sleep(1)
    headers = await prepare_headers()
    request_kwargs = {
        'url': lead_link,
        'request_type': "GET",
        'session': session,
        'headers': headers,
    }

    content = await request_or_retry(**request_kwargs)
    created_at = content['created_at']
    date = datetime.fromtimestamp(created_at)
    if datetime.now() - date > timedelta(days=int(months)*30):
        return None
    try:
        if content['status_id'] == settings.success_stage_id and content['pipeline_id'] == settings.pipeline_id:
            return content['price']
        else:
            return "Open Lead"
    except TypeError:
        return None


async def get_count_success_leads(id: int, is_company: bool, months: int, session: aiohttp.ClientSession):
    """Возвращает список успешных и открытых лидов"""

    try:
        leads = await get_leads(id, is_company, session)
    except HTTP401Exception:
        await asyncio.create_task(update_token())
        leads = await asyncio.create_task(get_leads(id, is_company, session))

    tasks = []
    for lead in leads:
        tasks.append(check_lead(
            lead['_links']['self']['href'], session, months))

    results = await asyncio.gather(*tasks)

    while None in results:
        results.remove(None)
    return results


async def get_json_from_hook(request: Request):
    """Обрабатывает тело запроса вебхука"""

    if request.headers['Content-Type'] == 'application/x-www-form-urlencoded':
        data = await request.body()
        json_data = parser.parse(data, normalized=True)
        return json_data


def get_lead_id(data):
    lead_id = list(data['leads'].items())[0][1][0]['id']
    return lead_id


async def get_lead_main_contact_and_company(data, session: aiohttp.ClientSession):
    """Возвращает id основного контакта для лида и его компании, если она есть"""

    params = {
        'with': 'contacts'
    }

    lead_id = get_lead_id(data)
    lead_link = settings.API_URL + f"/leads/{lead_id}"

    headers = await prepare_headers()

    main_contact, company = None, None
    main_contact_link = None

    request_kwargs = {
        'url': lead_link,
        'request_type': 'GET',
        'session': session,
        'headers': headers,
        'params': params
    }

    content = await request_or_retry(**request_kwargs)

    contacts = content['_embedded']['contacts']
    for contact in contacts:
        if contact['is_main']:
            main_contact = contact['id']
            main_contact_link = contact['_links']['self']['href']

    contact_request_kwargs = {
        'url': main_contact_link,
        'request_type': 'GET',
        'headers': headers,
        'session': session
    }

    contact_data = await request_or_retry(**contact_request_kwargs)
    contact_companies = contact_data['_embedded']['companies']
    try:
        company = contact_companies[0]['id']
        return main_contact, company
    # company = content['_embedded']['companies']
    # try:
    #     company = company[0]
    #     return main_contact, company['id']
    except IndexError:
        return main_contact, None


async def get_main_contacts_success_leads(contact_id, session: aiohttp.ClientSession):
    """Возвращает список успешных и открытых лидов для контакта"""

    results = await get_count_success_leads(contact_id, is_company=False, months=6, session=session)
    return results


async def get_company_success_leads(company_id, session: aiohttp.ClientSession):
    """Возвращает список успешных и открытых лидов для компании"""

    results = await get_count_success_leads(company_id, is_company=True, months=6, session=session)
    return results


async def update_company_leads_sum_field(company_id, sum_of_leads: int, session: aiohttp.ClientSession):
    """Обновляет поле суммы сделок для компании"""

    headers = await prepare_headers()

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

    request_kwargs = {
        'url': url,
        'request_type': 'PATCH',
        'session': session,
        'headers': headers,
        'data': json.dumps(fields_data)
    }

    result = await request_or_retry(**request_kwargs)


async def update_contact_leads_amount_field(contact_id, amount: int, session: aiohttp.ClientSession):
    """Обновляет поле количества успешных сделок для контакта"""
    headers = await prepare_headers()

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

    request_kwargs = {
        'url': url,
        'request_type': 'PATCH',
        'session': session,
        'headers': headers,
        'data': json.dumps(fields_data)
    }

    result = await request_or_retry(**request_kwargs)


async def update_active_lead_main_contact_amount(lead_id, amount: int, session: aiohttp.ClientSession):
    """Обновляет поле количества успешных сделок основного контакта лида"""
    lead_link = settings.API_URL + f"/leads/{lead_id}"
    lead_result = await check_lead(lead_link=lead_link, session=session, months=6)
    if lead_result != "Open Lead":
        return
    headers = await prepare_headers()
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

    request_kwargs = {
        'url': lead_link,
        'request_type': 'PATCH',
        'session': session,
        'headers': headers,
        'data': json.dumps(fields_data),
        'add': "Called from lead updater"
    }
    result = await request_or_retry(**request_kwargs)


async def handle_hook(data, session: aiohttp.ClientSession):
    """Обрабатывает полученный вебхук, делает запросы на изменение полей"""

    logger.info("Handling a hook")

    main_contact_id, company_id = await get_lead_main_contact_and_company(data, session)
    main_contact_results = await get_main_contacts_success_leads(main_contact_id, session)
    if company_id is not None:
        company_results = await get_company_success_leads(company_id, session)

        while "Open Lead" in company_results:
            company_results.remove("Open Lead")

        company_results_sum = sum(company_results)
        await update_company_leads_sum_field(company_id, company_results_sum, session)

    while "Open Lead" in main_contact_results:
        main_contact_results.remove("Open Lead")
    await update_contact_leads_amount_field(main_contact_id, len(main_contact_results), session)

    lead_id = get_lead_id(data)
    await update_active_lead_main_contact_amount(lead_id, len(main_contact_results), session)


def get_value_and_label_from_list(items: list):
    result = []
    for item in items:
        id_and_name = {"value": str(item['id']), "label": item['name']}
        result.append(id_and_name)
    return result


async def return_entity_fields():
    headers = await prepare_headers()
    data = {}

    async with aiohttp.ClientSession() as session:
        request_kwargs = {
            'url': settings.API_URL + "/companies/custom_fields",
            'request_type': 'GET',
            'session': session,
            'headers': headers,
        }
        company_fields = await request_or_retry(**request_kwargs)
        company_fields = get_value_and_label_from_list(
            company_fields['_embedded']['custom_fields'])
        data.update({"companyFields": company_fields})

        request_kwargs['url'] = settings.API_URL + "/contacts/custom_fields"
        contact_fields = await request_or_retry(**request_kwargs)
        contact_fields = get_value_and_label_from_list(
            contact_fields['_embedded']['custom_fields'])
        data.update({"contactFields": contact_fields})

        request_kwargs['url'] = settings.API_URL + "/leads/custom_fields"
        lead_fields = await request_or_retry(**request_kwargs)
        lead_fields = get_value_and_label_from_list(
            lead_fields['_embedded']['custom_fields'])
        data.update({"leadFields": lead_fields})

        return data
