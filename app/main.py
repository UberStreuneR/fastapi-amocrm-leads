from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from utils import get_count_success_leads, update_or_set_token


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
    await update_or_set_token()


@app.get("/successful-leads/{id}")
async def successful_leads(id: int, is_company: bool, months):
    """Path-function для выведения количества успешных лидов контакта или компании за последние n месяцев"""

    results = await get_count_success_leads(id, is_company, months)
    return {f"amount": len(results), "sum": sum(results), "id": id, "is_company": is_company}
