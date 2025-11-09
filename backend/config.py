"""
Configuration management for the Grocery Management Agent.
Loads settings from environment variables and provides typed config access.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent

DEFAULT_ENV_PATHS = [BASE_DIR / ".env", Path(".env")]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=DEFAULT_ENV_PATHS, env_file_encoding="utf-8", case_sensitive=False
    )

    # MongoDB
    mongodb_uri: str = Field(
        default="mongodb://localhost:27017",
        alias="mongo_db_uri",
    )
    mongodb_db_name: str = Field(
        default="grocery_agent",
        alias="mongo_db_db_name",
    )
    mongodb_username: Optional[str] = Field(
        default=None,
        alias="mongo_db_username",
    )
    mongodb_password: Optional[str] = Field(
        default=None,
        alias="mongo_db_password",
    )

    # OpenAI
    openai_api_key: str
    openai_model: str = Field(default="gpt-5-mini")
    openai_base_url: Optional[str] = Field(
        default="",
        alias="openai_proxy_url",
    )

    # Splitwise
    splitwise_api_key: Optional[str] = None
    splitwise_consumer_key: Optional[str] = None
    splitwise_consumer_secret: Optional[str] = None
    splitwise_group_id: Optional[str] = None
    # Note: Callback URL is managed by frontend and Splitwise app settings, not backend

    # Thuisbezorgd
    thuisbezorgd_email: Optional[str] = None
    thuisbezorgd_password: Optional[str] = None
    thuisbezorgd_api_url: Optional[str] = None

    # WhatsApp (Twilio)
    whatsapp_account_sid: Optional[str] = None  # Twilio Account SID
    whatsapp_auth_token: Optional[str] = None  # Twilio Auth Token
    whatsapp_from_number: Optional[str] = None  # WhatsApp number from Twilio (format: whatsapp:+1234567890)
    whatsapp_webhook_url: Optional[str] = None  # Webhook URL for receiving messages

    # Discord
    discord_bot_token: Optional[str] = None  # Discord bot token from Discord Developer Portal
    discord_permission_id: Optional[str] = None  # Discord permission ID for the bot
    discord_webhook_url: Optional[str] = None  # Discord webhook URL for sending messages

    # Application
    app_env: str = "development"
    app_debug: bool = True
    log_level: str = "INFO"

    # Agent Settings
    auto_order_enabled: bool = False
    order_approval_required: bool = True
    low_stock_check_interval: int = 3600  # seconds

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"

    @property
    def normalized_openai_base_url(self) -> Optional[str]:
        """Normalized OpenAI base URL without trailing slash."""
        if not self.openai_base_url:
            return None
        return self.openai_base_url.rstrip("/")


# Global settings instance
settings = Settings()
