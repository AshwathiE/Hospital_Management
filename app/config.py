from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Hospital Appointment System"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/hospital_db"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
