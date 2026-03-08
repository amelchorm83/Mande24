from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "Mande24 Independent API"
    api_prefix: str = "/api/v1"
    environment: str = "local"
    database_url: str = "sqlite:///./mande24.db"
    auto_create_tables: bool = True
    jwt_secret_key: str = "change_me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    enable_commission_scheduler: bool = False
    commission_close_hour_utc: int = 1
    commission_close_minute_utc: int = 0
    commission_scheduler_run_on_startup: bool = False
    cors_allow_origins: str = "*"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
