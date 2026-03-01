from pydantic_settings import BaseSettings,SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5"
    # ollama_embedding_model: str = "nomic-embed-text"
    chroma_path: str = "./chroma_db"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_results: int = 4
    max_history: int = 10

    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # class Config:
    #     env_file = ".env"


settings = Settings()