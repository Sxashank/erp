"""Application configuration using Pydantic Settings."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "SMFC ERP"
    APP_ENV: str = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT Authentication
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Security
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 30
    PASSWORD_EXPIRY_DAYS: int = 90
    PORTAL_DEFAULT_ORGANIZATION_ID: str | None = None

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            if v.startswith("["):
                import json

                return json.loads(v)
            return [origin.strip() for origin in v.split(",")]
        return v

    # Logging
    LOG_LEVEL: str = "INFO"

    # SMTP / Email Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "SMFC ERP"
    SMTP_USE_TLS: bool = True
    SMTP_ENABLED: bool = False  # Disable email by default

    # Workflow Configuration
    WORKFLOW_ESCALATION_CHECK_MINUTES: int = 15
    WORKFLOW_DIGEST_HOUR: int = 9  # Daily digest at 9 AM

    # -------------------------------------------------------------------
    # Vendor integration — PLATFORM-LEVEL endpoint knobs.
    #
    # These are URLs + timeouts that are the SAME for every NBFC tenant.
    # Tenant-specific credentials (API keys, passwords, merchant IDs,
    # signing secrets) NEVER go here — they live in IntegrationConfig
    # keyed by organization_id. See CLAUDE.md §6.8 and §12.24.
    #
    # Defaults below point at sandbox URLs so a misconfigured deploy
    # hits the vendor's sandbox (which fails loudly) rather than prod.
    # -------------------------------------------------------------------
    # GSTN
    GSTN_BASE_URL: str = "https://api.sandbox.gstn.gov.in"
    # e-Invoice IRP
    EINVOICE_BASE_URL: str = "https://einv-apisandbox.nic.in"
    # e-Waybill
    EWAYBILL_BASE_URL: str = "https://ewaybillapi-sandbox.nic.in"
    # TRACES / e-filing for TDS
    TRACES_BASE_URL: str = "https://contents.tdscpc.gov.in"
    EFILING_BASE_URL: str = "https://uat.incometax.gov.in"
    # CKYC Registry
    CKYC_BASE_URL: str = "https://test.ckycindia.in"
    # Credit bureaus
    CIBIL_BASE_URL: str = "https://api.cibil.com/sandbox"
    EXPERIAN_BASE_URL: str = "https://api-sandbox.experian.in"
    CRIF_BASE_URL: str = "https://api-uat.crifhighmark.com"
    # Comms
    MSG91_BASE_URL: str = "https://api.msg91.com/api/v5"
    FCM_BASE_URL: str = "https://fcm.googleapis.com/v1"
    # CERSAI
    CERSAI_BASE_URL: str = "https://www.cersai.org.in/CERSAI/sandbox"
    # NeSL
    NESL_BASE_URL: str = "https://uat.nesl.co.in"
    # e-Sign ESP
    ESIGN_BASE_URL: str = "https://esignuat.nsdl.co.in/esignservice/v1"
    # CRILC SFTP
    CRILC_SFTP_HOST: str = "sftp.crilc.rbi.org.in"
    # Shared HTTP timeouts (seconds) for the integration base client
    INTEGRATION_CONNECT_TIMEOUT: float = 5.0
    INTEGRATION_READ_TIMEOUT: float = 30.0
    INTEGRATION_WRITE_TIMEOUT: float = 10.0

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.APP_ENV == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.APP_ENV == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
