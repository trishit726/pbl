"""Environment-based configuration shared by backend services."""

from functools import lru_cache
import os
from dataclasses import dataclass


def _csv_env(name: str, default: str = "") -> tuple[str, ...]:
    return tuple(value.strip() for value in os.getenv(name, default).split(",") if value.strip())


@dataclass(frozen=True)
class Settings:
    """Service settings; secrets and deployment-specific values come from env."""

    service_name: str
    environment: str
    aws_region: str
    dynamodb_endpoint_url: str | None
    s3_endpoint_url: str | None
    cors_origins: tuple[str, ...]
    jwt_issuer: str
    jwt_audience: str
    jwt_signing_key: str
    access_token_minutes: int
    refresh_token_days: int
    service_token_minutes: int
    mfa_dev_code: str
    audit_log_table: str
    resources_config_path: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings once per process. Production must provide a strong key."""
    return Settings(
        service_name=os.getenv("SERVICE_NAME", "lms-service"),
        environment=os.getenv("APP_ENV", "development"),
        aws_region=os.getenv("AWS_REGION", "us-east-1"),
        dynamodb_endpoint_url=os.getenv("DYNAMODB_ENDPOINT_URL") or None,
        s3_endpoint_url=os.getenv("S3_ENDPOINT_URL") or None,
        cors_origins=_csv_env("CORS_ALLOWED_ORIGINS"),
        jwt_issuer=os.getenv("JWT_ISSUER", "lms-backend"),
        jwt_audience=os.getenv("JWT_AUDIENCE", "lms-frontend"),
        jwt_signing_key=os.getenv("JWT_SIGNING_KEY", "development-only-change-me"),
        access_token_minutes=int(os.getenv("ACCESS_TOKEN_MINUTES", "15")),
        refresh_token_days=int(os.getenv("REFRESH_TOKEN_DAYS", "7")),
        service_token_minutes=int(os.getenv("SERVICE_TOKEN_MINUTES", "5")),
        mfa_dev_code=os.getenv("MFA_DEV_CODE", "000000"),
        audit_log_table=os.getenv("AUDIT_LOG_TABLE", "AuditLog"),
        resources_config_path=os.getenv("RESOURCES_CONFIG_PATH", "config/resources.yaml"),
    )

