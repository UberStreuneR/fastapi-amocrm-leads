from pydantic import BaseSettings


class Settings(BaseSettings):
    API_URL: str = "https://devks.amocrm.ru/api/v4"
    AUTH_ENDPOINT: str = "https://devks.amocrm.ru/oauth2/access_token"

settings = Settings()