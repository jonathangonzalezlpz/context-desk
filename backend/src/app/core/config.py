from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "ContextDesk API"
    ENVIRONMENT: str = "local"
    
    DATABASE_URL: str
    QDRANT_URL: str
    OPENAI_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
