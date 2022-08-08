from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from starlette.middleware.cors import CORSMiddleware
from app.integrations.routes import router as integrations_router
from app.integrations.deps import get_amocrm_from_first_integration
from app.settings.routes import router as settings_router
from app.settings import services
from app.amocrm.settings import SettingsSetter
from sqlmodel import SQLModel, Session
from .database import engine

app = FastAPI(docs_url=None, redoc_url=None)
app.include_router(integrations_router)
app.include_router(settings_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    services.set_company_check_status(session, False)
    services.set_contact_check_status(session, False)
    session.commit()
    try:
        amocrm = get_amocrm_from_first_integration()
        SettingsSetter(amocrm)
    except HTTPException:
        pass


"""Для отображения docs, в силу того что дефолтный cdn не подгружается"""
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()
