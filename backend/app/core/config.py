from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://nova:nova@localhost:5432/nova"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    demo_auth_enabled: bool = True
    geocoding_provider: str = "nominatim"
    nominatim_base_url: str = "https://nominatim.openstreetmap.org"
    geocoding_user_agent: str = "NOVA-Vendor-Coverage/0.1 (service-area location search)"
    auth_secret: str = "local-only-change-me-before-deployment"
    access_token_expire_minutes: int = 480

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
