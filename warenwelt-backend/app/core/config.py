from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "WarenWelt"
    API_V1_STR: str = "/api/v1"

    # Database settings
    DATABASE_URL: str = "sqlite:///./test.db" # Default to SQLite for simplicity in MVP

    # JWT Settings
    SECRET_KEY: str = "a_very_secret_key" # CHANGE THIS!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
