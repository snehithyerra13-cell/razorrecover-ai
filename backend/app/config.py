from pydantic_settings import BaseSettings
from pydantic import Field
import os

class Settings(BaseSettings):
    ENV: str = "development"
    PORT: int = 8000
    DATABASE_URL: str = "sqlite:///./razorrecover.db"
    
    # AI API Config
    GEMINI_API_KEY: str = Field(default="")
    
    # Razorpay Config
    RAZORPAY_KEY_ID: str = Field(default="")
    RAZORPAY_KEY_SECRET: str = Field(default="")
    RAZORPAY_WEBHOOK_SECRET: str = Field(default="")
    
    # Policies Config
    MAX_RETRIES: int = 3
    MIN_RECOVERY_PROBABILITY: float = 0.50
    MIN_RETRY_INTERVAL_MINUTES: int = 15

    class Config:
        # Load from .env file if it exists
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
