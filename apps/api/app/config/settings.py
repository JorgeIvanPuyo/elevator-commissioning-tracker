from functools import cached_property

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Megapolis Elevator Traceability"
    environment: str = "local"
    database_url: str = "postgresql+asyncpg://megapolis:megapolis@localhost:5432/megapolis"
    cors_origins: str = "http://localhost:3000"
    gcs_bucket_name: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @cached_property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
