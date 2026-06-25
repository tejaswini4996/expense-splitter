"""Application Configuration"""
from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache
import os

class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Database
    database_url: str = "sqlite:///./expense_splitter.db"
    mssql_database_url: Optional[str] = None
    
    # API Settings
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
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
    
    def __init__(self, **data):
        super().__init__(**data)
        # Load from environment variables if present
        if os.getenv("SECRET_KEY"):
            self.secret_key = os.getenv("SECRET_KEY")
        if os.getenv("DATABASE_URL"):
            self.database_url = os.getenv("DATABASE_URL")
        if os.getenv("ALGORITHM"):
            self.algorithm = os.getenv("ALGORITHM")
        if os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"):
            self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings"""
    return Settings()
