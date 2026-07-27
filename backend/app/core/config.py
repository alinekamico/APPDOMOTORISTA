from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "mysql+pymysql://kami:kami@localhost:3306/kami_romaneios"
    # Caminho do bundle de CA da AWS (ex: global-bundle.pem) — necessário quando o RDS exige
    # SSL verificado. Deixe vazio em dev local (SQLite/MySQL sem TLS).
    database_ssl_ca: str = ""

    jwt_secret: str = "changeme"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    password_reset_expire_minutes: int = 30
    app_base_url: str = "http://localhost:3000"

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_name: str = "KAMI CO. Romaneios"

    google_maps_api_key: str = ""

    tms_webhook_token: str = "changeme"
    integration_adapter_maps: str = "fake"
    integration_adapter_uno: str = "stub"
    integration_adapter_nps: str = "stub"

    # Fonte de romaneios enquanto o TMS não existe: "manual" (tela de simulação) ou
    # "uno_replica" (busca na réplica do UNO hospedada no Supabase/Postgres).
    integration_adapter_romaneio_source: str = "manual"
    uno_replica_database_url: str = ""

    upload_dir: str = "./uploads"


@lru_cache
def get_settings() -> Settings:
    return Settings()
