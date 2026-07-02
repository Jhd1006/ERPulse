from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379"
    PUBLIC_API_KEY: str
    PUBLIC_API_BASE_URL: str = "https://apis.data.go.kr/B552657/ErmctInfoInqireService"
    REDIS_TTL: int = 900  # 15분


settings = Settings()
