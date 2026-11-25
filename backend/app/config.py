import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Hệ thống đặt phòng khách sạn"
    API_V1_STR: str = "/api/v1"
    
    # Oracle Database configuration (NFR-26)
    ORA_USER: str = "hotel_app"
    ORA_PASSWORD: str = "HotelApp123#"
    ORA_DSN: str = "localhost:1521/FREEPDB1"
    ORA_SCHEMA: str = "HOTEL_OWNER"
    ORA_POOL_MIN: int = 2
    ORA_POOL_MAX: int = 20
    
    # Security & JWT (NFR-11, NFR-12)
    JWT_SECRET: str = "hotel_jwt_secret_key_change_in_production_2026_super_secure"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours
    
    # API Key for Integration (AC-18)
    API_KEY_INTEGRATION: str = "demo-integration-api-key-2026"

    # Rate Limiting & CAPTCHA (F21, NFR-16)
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_LOGIN_PER_MIN: int = 15
    RATE_LIMIT_API_PER_MIN: int = 120
    CAPTCHA_ENABLED: bool = False
    CAPTCHA_TEST_SECRET: str = "test-captcha-pass"
    
    # SMTP
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: str = "noreply@hotel.com"
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
