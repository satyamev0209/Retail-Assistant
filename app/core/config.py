"""Configuration management using pydantic-settings."""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings."""
    
    # API Keys
    google_api_key: str = "AIzaSyDlcQzu3IzSIyP7OyvfN_2Qfl3f8YEwxnw"
    
    # Database paths
    chroma_db_path: str = "./data/kb/chroma"
    duckdb_path: str = "./data/kb/retail.duckdb"
    
    # Temporary storage
    temp_data_path: str = "./data/temp"
    
    # Model settings
    model_name: str = "gemini-3-flash-preview"
    temperature: float = 0.1
    
    # Vector DB settings
    embedding_model: str = "models/embedding-001"
    top_k_results: int = 3
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()

# Ensure directories exist
Path(settings.chroma_db_path).mkdir(parents=True, exist_ok=True)
Path(settings.temp_data_path).mkdir(parents=True, exist_ok=True)
Path(settings.duckdb_path).parent.mkdir(parents=True, exist_ok=True)
