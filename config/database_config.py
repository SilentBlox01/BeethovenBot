import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class DatabaseConfig:
    # MongoDB
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "beethoven_bot")
    
    # PostgreSQL
    POSTGRES_URI: str = os.getenv("POSTGRES_URI", "postgresql://user:pass@localhost:5432/beethoven_bot")
    
    # SQLite
    SQLITE_PATH: str = os.getenv("SQLITE_PATH", "./data/beethoven_bot.db")
    
    # Estrategia de almacenamiento
    STORAGE_STRATEGY: str = os.getenv("STORAGE_STRATEGY", "hybrid")  # hybrid, mongo_only, sql_only
    
    # Configuración de caché
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 300  # 5 minutos

# Instancia global de configuración
db_config = DatabaseConfig()