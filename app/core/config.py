from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    OPEN_METEO_URL: str = "https://api.open-meteo.com/v1/forecast"
    RAIN_WATCH_MM: float = 50
    RAIN_WARNING_MM: float = 100

    OPEN_METEO_DAILY_LIMIT: int = 10_000
    OPEN_METEO_MONTHLY_LIMIT: int = 300_000
    OPEN_METEO_DAILY_BUDGET: float = 8_000

    SECRET_KEY: str

    @property
    def database_url(self) -> URL:
        return URL.create(
            "postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        )


settings = Settings()  # type: ignore[call-arg]
