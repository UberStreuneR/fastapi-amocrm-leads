import aiohttp, aiofiles
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from utils import (prepare_hook,
                   get_json_from_hook,
                   delete_hook,
                   handle_hook)
from auth import set_token


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


@app.on_event("startup")
async def on_startup():
    await set_token()
    await prepare_hook()


#TODO: Функция удаляет хук как должно, проверено. Не работает shutdown event для FastAPI в Докере
@app.on_event("shutdown")
async def on_shutdown():
    await delete_hook()


# @app.get("/successful-leads/{id}")
# async def successful_leads(id: int, is_company: bool, months):
#     """Path-function для выведения количества успешных лидов контакта или компании за последние n месяцев"""
#     async with aiohttp.ClientSession() as session:
#         try:
#             results = await get_count_success_leads(id, is_company, months, session)
#         except TypeError:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity with such parameters was not found")
#         return {f"amount": len(results), "sum": sum(results), "id": id, "is_company": is_company}

@app.post("/")
async def receive_hook(request: Request):
    async with aiohttp.ClientSession() as session:
        data = await get_json_from_hook(request)
        await handle_hook(data, session)
        return {"result": "Success"}
