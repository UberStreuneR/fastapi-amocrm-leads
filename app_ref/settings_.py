from pydantic import BaseSettings, PostgresDsn


class Settings(BaseSettings):

    database: PostgresDsn
    app_host: str
    client_secret: str


settings = Settings()
