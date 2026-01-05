from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PulsarEstate"
    environment: str = "dev"
    debug: bool = True

    api_version: str = "v1"

    log_level: str = "INFO"

    ollama_base_url: str = "http://localhost:11434"

    scheduler_timezone: str = "UTC"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DPP_",
        case_sensitive=False,
    )


settings = Settings()
