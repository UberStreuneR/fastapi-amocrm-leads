from functools import lru_cache
from pydantic import BaseSettings, PostgresDsn
from typing import List


class Settings(BaseSettings):

    database: PostgresDsn
    app_host: str
    client_secret: str
    lead_paid_field: int
    company_last_payment_field: int


@lru_cache
def get_settings():
    settings = Settings()
    return settings
