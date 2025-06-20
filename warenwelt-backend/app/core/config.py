from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional # Added Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "WarenWelt"
    API_V1_STR: str = "/api/v1"

    # Database settings
    DATABASE_URL: str = "sqlite:///./test.db" # Default to SQLite for simplicity in MVP

    # JWT Settings
    SECRET_KEY: str = "a_very_secret_key" # CHANGE THIS!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Email settings for fastapi-mail
    MAIL_USERNAME: Optional[str] = None
    MAIL_PASSWORD: Optional[str] = None
    MAIL_FROM: Optional[str] = None # Default sender email
    MAIL_FROM_NAME: Optional[str] = None # Optional sender name
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.example.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    MAIL_VALIDATE_CERTS: bool = True # Set to False for local/dev if using self-signed certs
    MAIL_USE_CREDENTIALS: bool = True

    # For templates if used (e.g., HTML emails)
    # TEMPLATE_FOLDER: Optional[str] = None

    # Default due days for rental invoices
    RENTAL_INVOICE_DUE_DAYS_DEFAULT: int = 14


    class Config:
        env_file = ".env"
        extra = "ignore" # Allow other env vars not defined in Settings

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
