from pydantic import BaseSettings
import os

class Settings(BaseSettings):
    API_URL: str = os.environ.get("API_URL")
    AUTH_ENDPOINT: str = "https://devks.amocrm.ru/oauth2/access_token"
    HOST_URL: str = os.environ.get("HOST_URL")
    LEADS_FIELD_ID: int = os.environ.get("LEADS_FIELD_ID")
    CONTACTS_FIELD_ID: int = os.environ.get("CONTACTS_FIELD_ID")
    COMPANY_FIELD_ID: int = os.environ.get("COMPANY_FIELD_ID")
    pipeline_id: int = None
    success_stage_id: int = None


settings = Settings()