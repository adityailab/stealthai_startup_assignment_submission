# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "BK Platform"
    ENV: str = "dev"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    DATABASE_URL: str = "sqlite:///./bk.db"

    OLLAMA_HOST: str | None = None
    OLLAMA_MODEL: str | None = None
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str | None = None
    EMBED_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # NEW: Hugging Face
    HF_TOKEN: str | None = None
    HF_MODEL_ID: str | None = None
    HF_API_BASE: str | None = "https://api-inference.huggingface.co/models"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
