from urllib.parse import quote_plus

from pydantic import Field, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Metadata
    app_name: str = "PulsarEstate"
    environment: str = Field(default="dev", pattern="^(dev|staging|prod)$")
    debug: bool = True
    api_version: str = "v1"
    log_level: str = Field(
        default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"
    )

    # AI & Pipeline
    ollama_base_url: str = "http://localhost:11434"
    ollama_api_key: SecretStr = Field(default=SecretStr(""))

    # Auth & Security
    admin_api_key: SecretStr = Field(
        default=SecretStr(""), description="Required for admin endpoints"
    )
    jwt_secret_key: SecretStr = Field(
        default=SecretStr(""),
        description="Critical: Must be a strong secret in production",
    )

    # Scheduler
    scheduler_timezone: str = "UTC"

    # Database Components
    database_host: str = Field(default="db", description="Database hostname")
    database_port: int = Field(default=5432, description="Database port")
    database_user: str = Field(default="pulsar_user", description="Database username")
    database_password: SecretStr = Field(
        default=SecretStr("pulsar_password"), description="Database password"
    )
    database_name: str = Field(default="pulsar_estate", description="Database name")

    # RabbitMQ Components
    rabbitmq_host: str = Field(default="rabbitmq", description="RabbitMQ hostname")
    rabbitmq_port: int = Field(default=5672, description="RabbitMQ port")
    rabbitmq_management_port: int = Field(
        default=15672, description="RabbitMQ Management port"
    )
    rabbitmq_user: str = Field(default="guest", description="RabbitMQ username")
    rabbitmq_password: SecretStr = Field(
        default=SecretStr("guest"), description="RabbitMQ password"
    )

    # Computed URLs (Automatically built from components above)
    @computed_field
    @property
    def database_url(self) -> str:
        """Full async database URL for SQLAlchemy"""
        # quote_plus ensures special characters in passwords don't break the URL
        safe_pass = quote_plus(self.database_password.get_secret_value())
        return f"postgresql+asyncpg://{self.database_user}:{safe_pass}@{self.database_host}:{self.database_port}/{self.database_name}"

    @computed_field
    @property
    def celery_broker_url(self) -> str:
        """RabbitMQ broker URL for Celery"""
        safe_pass = quote_plus(self.rabbitmq_password.get_secret_value())
        return f"amqp://{self.rabbitmq_user}:{safe_pass}@{self.rabbitmq_host}:{self.rabbitmq_port}//"

    @computed_field
    @property
    def celery_result_backend(self) -> str:
        """Result backend URL (Must be sync for Celery)"""
        safe_pass = quote_plus(self.database_password.get_secret_value())
        return f"db+postgresql://{self.database_user}:{safe_pass}@{self.database_host}:{self.database_port}/{self.database_name}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DPP_",
        case_sensitive=False,
        env_ignore_empty=True,
        extra="ignore",
    )

    def model_post_init(self, __context):
        """Runtime validation after initialization"""
        if self.environment == "prod":
            if not self.jwt_secret_key.get_secret_value().strip():
                raise ValueError("JWT_SECRET_KEY must be set in production!")
            if not self.admin_api_key.get_secret_value().strip():
                raise ValueError("ADMIN_API_KEY must be set in production!")

            # Ensure default passwords aren't used in prod
            if self.database_password.get_secret_value() in ["pulsar_password", ""]:
                raise ValueError("DATABASE_PASSWORD must be changed in production!")
            if self.rabbitmq_password.get_secret_value() in ["guest", ""]:
                raise ValueError("RABBITMQ_PASSWORD must be changed in production!")


# Global settings instance
settings = Settings()
