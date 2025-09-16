from pydantic import BaseSettings

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "a_very_secret_key"
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    DATABASE_URL: str = "sqlite:///./test.db"

    class Config:
        case_sensitive = True

settings = Settings()
