from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./cases.db"
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8080,http://localhost:5173"
    
    # Google Calendar API
    GOOGLE_CREDENTIALS_FILE: str = "credentials.json"
    GOOGLE_TOKEN_FILE: str = "token.json"
    GOOGLE_CALENDAR_ID: str = "primary"
    
    # eCourt settings
    ECOURT_MAX_RETRIES: int = 3
    ECOURT_TIMEOUT: int = 30
    
    # Background tasks
    SCHEDULER_ENABLED: bool = True
    REFRESH_HOUR: int = 3  # 3 AM
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated origins string to list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"

settings = Settings()