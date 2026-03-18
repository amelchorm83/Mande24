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
    enforce_security_in_local: bool = False
    cors_allow_credentials: bool = False
    auth_rate_limit_window_seconds: int = 60
    auth_register_rate_limit: int = 10
    auth_login_rate_limit: int = 15
    public_rate_limit_window_seconds: int = 60
    public_contact_rate_limit: int = 10
    public_quote_rate_limit: int = 30
    public_tracking_rate_limit: int = 60
    national_same_state_factor: float = 1.0
    national_cross_state_factor: float = 1.1
    national_cross_region_factor: float = 1.12
    national_cross_zone_factor: float = 1.06
    national_station_handoff_factor: float = 1.04
    enable_commission_scheduler: bool = False
    commission_close_hour_utc: int = 1
    commission_close_minute_utc: int = 0
    commission_scheduler_run_on_startup: bool = False
    cors_allow_origins: str = "*"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_to_email: str = ""
    smtp_use_tls: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()


def validate_runtime_security() -> None:
    environment = settings.environment.strip().lower()
    enforce = settings.enforce_security_in_local or environment not in {"local", "dev", "development", "test"}
    if not enforce:
        return

    weak_secrets = {"", "change_me", "changeme", "dev", "secret", "test"}
    secret = (settings.jwt_secret_key or "").strip()
    if len(secret) < 32 or secret.lower() in weak_secrets:
        raise RuntimeError("JWT_SECRET_KEY is too weak for this environment. Use a strong secret with at least 32 chars.")

    raw_origins = [item.strip() for item in settings.cors_allow_origins.split(",") if item.strip()]
    if settings.cors_allow_credentials and ("*" in raw_origins or not raw_origins):
        raise RuntimeError("CORS configuration invalid: allow_credentials=true requires explicit CORS_ALLOW_ORIGINS values.")
