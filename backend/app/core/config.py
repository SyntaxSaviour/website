import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "BrainMint Software Website"
    API_V1_STR: str = "/api/v1"
    SITE_URL: str = os.getenv("SITE_URL", "https://brainmint.com")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # ---- Email ----
    EMAIL_ENABLED: bool = True
    EMAIL_PROVIDER: str = "smtp"          # smtp | sendgrid | mailgun
    EMAIL_FROM: str = "BrainMint Software <hello@brainmint.com>"
    EMAIL_TEAM_TO: str = ""               # Ashutosh's inbox

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True

    SENDGRID_API_KEY: str = ""
    MAILGUN_API_KEY: str = ""
    MAILGUN_DOMAIN: str = ""

    # ---- CAPTCHA ----
    CAPTCHA_ENABLED: bool = True
    CAPTCHA_PROVIDER: str = "hcaptcha"    # hcaptcha | recaptcha
    CAPTCHA_SECRET_KEY: str = ""
    RECAPTCHA_MIN_SCORE: float = 0.5

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="allow",
    )


settings = Settings()