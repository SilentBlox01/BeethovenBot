import asyncio
import time
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, ttl: int = 300):
        self.ttl = ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cleanup_task = None
        
    async def start_cleanup(self):
        """Inicia tarea de limpieza automática"""
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        
    async def stop_cleanup(self):
        """Detiene la limpieza automática"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            
    async def _cleanup_loop(self):
        """Loop de limpieza automática"""
        while True:
            await asyncio.sleep(60)  # Ejecutar cada minuto
            self._cleanup_expired()
            
    def _cleanup_expired(self):
        """Limpia entradas expiradas"""
        current_time = time.time()
        expired_keys = [
            key for key, data in self.cache.items()
            if current_time - data['timestamp'] > self.ttl
        ]
        
        for key in expired_keys:
            del self.cache[key]
            
        if expired_keys:
            logger.debug(f"🧹 Limpiadas {len(expired_keys)} entradas de caché expiradas")
            
    def get(self, key: str) -> Optional[Any]:
        """Obtiene valor del caché"""
        if key in self.cache:
            data = self.cache[key]
            if time.time() - data['timestamp'] <= self.ttl:
                data['hits'] += 1
                return data['value']
            else:
                del self.cache[key]
        return None
        
    def set(self, key: str, value: Any):
        """Establece valor en el caché"""
        self.cache[key] = {
            'value': value,
            'timestamp': time.time(),
            'hits': 0
        }
        
    def delete(self, key: str):
        """Elimina valor del caché"""
        if key in self.cache:
            del self.cache[key]
            
    def clear(self):
        """Limpia todo el caché"""
        self.cache.clear()

# Instancia global del gestor de caché
cache_manager = CacheManager()
async def initialize_cache_manager():
    await cache_manager.start_cleanup()
    asyncio.get_event_loop().create_task(cache_manager.start_cleanup())

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        self.cache = {}

    def get(self, key: str) -> Any:
        item = self.cache.get(key)
        if item:
            item['hits'] = item.get('hits', 0) + 1
            logger.debug(f"Cache hit: {key}")
            return item.get('data')
        return None

    def set(self, key: str, value: Any):
        self.cache[key] = {'data': value, 'hits': 0}
        logger.debug(f"Cache set: {key}")

    def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"Cache deleted: {key}")

    def clear(self):
        self.cache.clear()
        logger.info("Cache cleared")

    async def start_cleanup(self):
        logger.info("Cache cleanup started (no-op)")

    async def stop_cleanup(self):
        logger.info("Cache cleanup stopped (no-op)")

cache_manager = CacheManager()