from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://wkpoule:wkpoule@localhost:5432/wkpoule"
    jwt_secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    weather_api_key: str = ""
    weather_api_url: str = "https://api.weatherapi.com/v1"
    football_data_api_key: str = ""
    football_data_api_url: str = "https://api.football-data.org/v4"
    # When false, this process does not run the background score poller (use on extra API replicas).
    score_poller_enabled: bool = True

    redis_url: str = "redis://redis:6379/0"
    redis_max_connections: int = 20
    redis_socket_timeout: int = 5
    redis_socket_connect_timeout: int = 5

    # Optional SMTP for subgroup invite emails (leave host empty to skip sending).
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True
    # Public browser URL (HTTPS on OpenShift). Used in subgroup invite emails; also added to CORS when CORS_ORIGINS is unset.
    public_app_url: str = "http://localhost:3000"
    # Public API URL (dedicated Route to wkpoule-api). Used in OpenAPI servers and CORS.
    public_api_url: str = "http://localhost:8000"
    # Optional comma-separated extra origins (e.g. alternate domains). If empty, CORS uses localhost dev URLs + public_app_url.
    cors_origins: str = ""
    # If set, on startup the `admin` user's password is set to this value (and they stay admin). Dev/local recovery only.
    bootstrap_admin_password: str = Field(
        default="",
        validation_alias=AliasChoices("WKPOULE_BOOTSTRAP_ADMIN_PASSWORD", "bootstrap_admin_password"),
    )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
