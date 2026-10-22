import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "BrainMint Software Website"
    API_V1_STR: str = "/api/v1"
    SITE_URL: str = os.getenv("SITE_URL", "https://brainmint.com")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="allow"
    )

settings = Settings()