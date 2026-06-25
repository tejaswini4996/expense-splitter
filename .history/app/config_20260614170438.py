"""Application Configuration"""
from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./expense_splitter.db")
    mssql_database_url: Optional[str] = None
    
    # API Settings
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings"""
    return Settings()
