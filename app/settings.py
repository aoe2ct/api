from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    database_url: str
    secret_key: str
    discord_client_id: str
    discord_client_secret: str
    frontend_base_url: str


settings = Settings()
