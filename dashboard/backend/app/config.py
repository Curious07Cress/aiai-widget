"""
Dashboard Backend Configuration

Environment-based configuration for the dashboard backend service.
"""

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "AI Operations Dashboard Backend"
    app_version: str = "0.1.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8080

    # CORS
    cors_origins: str = "*"

    # Jaeger Configuration
    jaeger_base_url: str = "https://eu2-supstg-disttracing.3dx-staging.3ds.com"
    jaeger_service_name: str = "AIAssistantInfra/aiai-api"

    # MLI Configuration
    mli_base_url: str = "https://euw1-devprol50-mlinference.3dx-staging.3ds.com"

    # AIAI API Configuration
    aiai_base_url: str = "http://localhost:8000"

    # MCP Proxy Configuration
    mcp_proxy_url: Optional[str] = None

    # 3DPassport Authentication (optional, for accessing SSO-protected AIAI)
    passport_username: Optional[str] = None
    passport_password: Optional[str] = None

    # Timeouts (in seconds)
    health_check_timeout: int = 10
    trace_fetch_timeout: int = 30

    class Config:
        env_file = ".env"
        env_prefix = "DASHBOARD_"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
