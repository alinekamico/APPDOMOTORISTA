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
    refresh_token_expire_days: int = 7

    password_reset_expire_minutes: int = 30
    app_base_url: str = "http://localhost:3000"

    # Lista separada por vírgula. Same-origin (nginx serve front+back no mesmo domínio em
    # produção) já protege por padrão, mas mantemos a lista restrita por governança.
    cors_allowed_origins: str = "http://localhost:3000,http://localhost:3002"

    rate_limit_por_minuto: int = 100

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_name: str = "KAMI CO. Romaneios"

    openrouteservice_api_key: str = ""

    tms_webhook_token: str = "changeme"
    integration_adapter_maps: str = "fake"
    integration_adapter_uno: str = "stub"
    integration_adapter_nps: str = "stub"

    # Fonte de romaneios enquanto o TMS não existe: "manual" (tela de simulação) ou
    # "uno_replica" (busca na réplica do UNO hospedada no Supabase/Postgres).
    integration_adapter_romaneio_source: str = "manual"
    uno_replica_database_url: str = ""

    upload_dir: str = "./uploads"

    @property
    def cors_allowed_origins_lista(self) -> list[str]:
        return [origem.strip() for origem in self.cors_allowed_origins.split(",") if origem.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
