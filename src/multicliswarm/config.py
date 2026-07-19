import os
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Core
    APP_NAME: str = "MultiCliSwarm"
    VERSION: str = "2.0.0"
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"
    
    # Storage
    DB_PATH: str = os.path.expanduser("~/.multicliswarm.db")
    STORAGE_DIR: str = os.path.expanduser("~/.multicliswarm")
    INDEX_DIR: str = os.path.join(STORAGE_DIR, "index")
    CACHE_DIR: str = os.path.join(STORAGE_DIR, "cache")
    TOOLS_DIR: str = os.path.join(STORAGE_DIR, "tools")
    
    # API / Servers
    UI_PORT: int = 8080
    UI_HOST: str = "0.0.0.0"
    BRIDGE_PORT: int = 9999
    MCP_PORT: int = 8000
    
    # AI Defaults
    DEFAULT_ARCHITECT_ENGINE: str = "claude,gemini"
    DEFAULT_DEVELOPER_ENGINES: str = "gemini,codex"
    DEFAULT_REVIEWER_ENGINE: str = "claude,gemini"
    
    # Security
    USE_DOCKER_BY_DEFAULT: bool = False
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Telemetry
    OTLP_ENDPOINT: Optional[str] = None
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()

# Ensure directories exist
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
os.makedirs(settings.INDEX_DIR, exist_ok=True)
os.makedirs(settings.CACHE_DIR, exist_ok=True)
os.makedirs(settings.TOOLS_DIR, exist_ok=True)
