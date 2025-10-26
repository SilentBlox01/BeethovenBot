import json
import os
import asyncio
import random
from datetime import datetime, timedelta
import aiosqlite
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from typing import Dict, Any, Optional, List
import logging

# Configuración de logging
logger = logging.getLogger("utils.database")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class DatabaseConfig:
    def __init__(self):
        self.MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
        self.MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "beethoven_bot")
        self.SQLITE_PATH = os.getenv("SQLITE_PATH", "./data/beethoven_bot.db")
        os.makedirs(os.path.dirname(self.SQLITE_PATH), exist_ok=True)
        os.makedirs("./data/backup", exist_ok=True)

db_config = DatabaseConfig()

class DatabaseManager:
    def __init__(self, sqlite_path: str):
        self.sqlite_path = sqlite_path
        self.sqlite_conn = None

    async def check_table_structure(self, table_name: str, expected_columns: List[str]) -> bool:
        """Verifica si la tabla tiene las columnas esperadas."""
        try:
            async with self.sqlite_conn.execute(f"PRAGMA table_info({table_name})") as cursor:
                columns = [row["name"] for row in await cursor.fetchall()]
                return all(col in columns for col in expected_columns)
        except Exception as e:
            logger.error(f"❌ Error verificando estructura de {table_name}: {e}")
            return False

    async def migrate_table(self, table_name: str, create_sql: str, expected_columns: List[str]):
        """Migra una tabla antigua a la nueva estructura."""
        try:
            async with self.sqlite_conn.cursor() as cursor:
                # Verificar si la tabla existe
                await cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                exists = await cursor.fetchone()
                if exists:
                    # Verificar estructura
                    if not await self.check_table_structure(table_name, expected_columns):
                        logger.warning(f"⚠️ Tabla {table_name} tiene estructura antigua. Migrando...")
                        # Renombrar tabla antigua
                        await cursor.execute(f"ALTER TABLE {table_name} RENAME TO {table_name}_old")
                        # Crear nueva tabla
                        await cursor.execute(create_sql)
                        # Intentar migrar datos (solo para columnas compatibles)
                        common_columns = await self.get_common_columns(table_name, f"{table_name}_old")
                        if common_columns:
                            columns_str = ", ".join(common_columns)
                            await cursor.execute(
                                f"INSERT INTO {table_name} ({columns_str}) SELECT {columns_str} FROM {table_name}_old"
                            )
                        # Eliminar tabla antigua
                        await cursor.execute(f"DROP TABLE {table_name}_old")
                        logger.info(f"✅ Tabla {table_name} migrada")
                else:
                    # Crear tabla si no existe
                    await cursor.execute(create_sql)
            await self.sqlite_conn.commit()
        except Exception as e:
            logger.error(f"❌ Error migrando tabla {table_name}: {e}")
            raise

    async def get_common_columns(self, new_table: str, old_table: str) -> List[str]:
        """Obtiene columnas comunes entre la tabla nueva y antigua."""
        try:
            async with self.sqlite_conn.execute(f"PRAGMA table_info({new_table})") as cursor:
                new_columns = {row["name"] for row in await cursor.fetchall()}
            async with self.sqlite_conn.execute(f"PRAGMA table_info({old_table})") as cursor:
                old_columns = {row["name"] for row in await cursor.fetchall()}
            return list(new_columns & old_columns)
        except Exception as e:
            logger.error(f"❌ Error obteniendo columnas comunes: {e}")
            return []

    async def init_db(self):
        """Inicializa la base de datos SQLite y migra tablas si es necesario."""
        try:
            self.sqlite_conn = await aiosqlite.connect(self.sqlite_path, isolation_level=None)  # Autocommit
            self.sqlite_conn.row_factory = aiosqlite.Row  # Filas como diccionarios
            async with self.sqlite_conn.cursor() as cursor:
                # Definir estructuras de tablas
                tables = {
                    "achievements": {
                        "sql": """
                            CREATE TABLE IF NOT EXISTS achievements (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id TEXT NOT NULL,
                                achievement_name TEXT NOT NULL,
                                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                UNIQUE(user_id, achievement_name)
                            )
                        """,
                        "columns": ["id", "user_id", "achievement_name", "unlocked_at"]
                    },
                    "users": {
                        "sql": """
                            CREATE TABLE IF NOT EXISTS users (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id TEXT UNIQUE NOT NULL,
                                username TEXT,
                                coins INTEGER DEFAULT 0,
                                last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """,
                        "columns": ["id", "user_id", "username", "coins", "last_login"]
                    },
                    "pets": {
                        "sql": """
                            CREATE TABLE IF NOT EXISTS pets (
                                user_id TEXT NOT NULL,
                                pet_name TEXT NOT NULL,
                                pet_data TEXT NOT NULL,
                                PRIMARY KEY (user_id, pet_name)
                            )
                        """,
                        "columns": ["user_id", "pet_name", "pet_data"]
                    },
                    "afk_users": {
                        "sql": """
                            CREATE TABLE IF NOT EXISTS afk_users (
                                user_id TEXT PRIMARY KEY,
                                reason TEXT,
                                afk_since TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """,
                        "columns": ["user_id", "reason", "afk_since"]
                    },
                    "blacklist": {
                        "sql": """
                            CREATE TABLE IF NOT EXISTS blacklist (
                                user_id TEXT PRIMARY KEY,
                                reason TEXT,
                                banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """,
                        "columns": ["user_id", "reason", "banned_at"]
                    },
                    "guilds": {
                        "sql": """
                            CREATE TABLE IF NOT EXISTS guilds (
                                guild_id TEXT PRIMARY KEY,
                                guild_data TEXT NOT NULL,
                                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """,
                        "columns": ["guild_id", "guild_data", "last_updated"]
                    }
                }

                # Migrar o crear cada tabla
                for table_name, table_info in tables.items():
                    await self.migrate_table(table_name, table_info["sql"], table_info["columns"])

                # Crear índices
                for table_name, table_info in tables.items():
                    if "user_id" in table_info["columns"]:
                        await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_user_id ON {table_name} (user_id)")
                    if table_name == "guilds":
                        await cursor.execute("CREATE INDEX IF NOT EXISTS idx_guilds_guild_id ON guilds (guild_id)")
            await self.sqlite_conn.commit()
            logger.info("✅ Tablas SQLite creadas/migradas y optimizadas")
        except Exception as e:
            logger.error(f"❌ Error inicializando SQLite: {e}")
            raise

    async def cleanup_old_cache(self, days: int = 30):
        """Elimina datos antiguos para mantener la base ligera."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            async with self.sqlite_conn.cursor() as cursor:
                await cursor.execute(
                    "DELETE FROM achievements WHERE unlocked_at < ?",
                    (cutoff_date,)
                )
                await cursor.execute(
                    "DELETE FROM afk_users WHERE afk_since < ?",
                    (cutoff_date,)
                )
                await cursor.execute(
                    "DELETE FROM blacklist WHERE banned_at < ?",
                    (cutoff_date,)
                )
            await self.sqlite_conn.commit()
            logger.info(f"🧹 Cache antiguo eliminado (antes de {days} días)")
        except Exception as e:
            logger.error(f"❌ Error limpiando cache: {e}")

    async def close(self):
        """Cierra la conexión a SQLite."""
        if self.sqlite_conn:
            await self.sqlite_conn.close()
            logger.info("✅ Conexión SQLite cerrada")

class HybridDatabase:
    def __init__(self, bot=None):
        self.bot = bot
        self.mongo_client = None
        self.mongo_db = None
        self.sqlite_manager = DatabaseManager(db_config.SQLITE_PATH)
        self.locks = {'mongo': asyncio.Lock(), 'sqlite': asyncio.Lock()}
        self.initialized = False
        self.item_cooldowns = {}
        self.mission_resets = {}

    async def initialize(self):
        """Inicializa MongoDB y SQLite."""
        try:
            # Inicializar SQLite
            await self.sqlite_manager.init_db()
            self.sqlite_conn = self.sqlite_manager.sqlite_conn

            # Inicializar MongoDB
            try:
                self.mongo_client = AsyncIOMotorClient(
                    db_config.MONGO_URI,
                    maxPoolSize=10,
                    minPoolSize=2,
                    serverSelectionTimeoutMS=5000
                )
                self.mongo_db = self.mongo_client[db_config.MONGO_DB_NAME]
                await self.mongo_db.command('ping')
                logger.info("✅ Conexión MongoDB establecida")
            except ConnectionFailure as e:
                logger.warning(f"⚠️ No se pudo conectar a MongoDB: {e}. Usando solo SQLite.")
                self.mongo_client = None
                self.mongo_db = None

            self.initialized = True
            logger.info("✅ Sistema de base de datos híbrido inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando bases de datos: {e}")
            raise

    async def close(self):
        """Cierra todas las conexiones."""
        try:
            await self.sqlite_manager.close()
            if self.mongo_client:
                self.mongo_client.close()
                logger.info("✅ Conexión MongoDB cerrada")
        except Exception as e:
            logger.error(f"❌ Error cerrando conexiones: {e}")

    async def get_user_pets(self, user_id: str) -> Dict[str, Any]:
        """Obtiene las mascotas de un usuario desde SQLite."""
        async with self.locks['sqlite']:
            try:
                async with self.sqlite_conn.execute(
                    "SELECT pet_name, pet_data FROM pets WHERE user_id = ?",
                    (user_id,)
                ) as cursor:
                    pets = await cursor.fetchall()
                    result = {"mascotas": {pet["pet_name"]: json.loads(pet["pet_data"]) for pet in pets}}
                    return result if pets else {"mascotas": {}, "coins": 0}
            except Exception as e:
                logger.error(f"❌ Error obteniendo mascotas para {user_id}: {e}")
                return {"mascotas": {}, "coins": 0}

    async def save_user_pets(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        """Guarda las mascotas de un usuario en SQLite y MongoDB."""
        try:
            user_data["user_id"] = user_id
            user_data["last_update"] = str(datetime.now())

            # Guardar en MongoDB si está disponible
            if self.mongo_db is not None:
                async with self.locks['mongo']:
                    collection = self.mongo_db.user_pets
                    await collection.replace_one(
                        {"user_id": user_id},
                        user_data,
                        upsert=True
                    )

            # Guardar en SQLite con transacción
            async with self.locks['sqlite']:
                await self.sqlite_conn.execute("BEGIN TRANSACTION")
                async with self.sqlite_conn.cursor() as cursor:
                    await cursor.execute("DELETE FROM pets WHERE user_id = ?", (user_id,))
                    for pet_name, pet_data in user_data.get("mascotas", {}).items():
                        await cursor.execute(
                            "INSERT OR REPLACE INTO pets (user_id, pet_name, pet_data) VALUES (?, ?, ?)",
                            (user_id, pet_name, json.dumps(pet_data))
                        )
                await self.sqlite_conn.commit()

            logger.debug(f"✅ Mascotas de usuario {user_id} guardadas")
            return True
        except Exception as e:
            logger.error(f"❌ Error guardando mascotas de usuario {user_id}: {e}")
            await self.sqlite_conn.rollback()
            return False

    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el perfil de usuario desde MongoDB."""
        if self.mongo_db is not None:
            logger.warning(f"⚠️ MongoDB no disponible para get_user_profile de {user_id}")
            return None
        try:
            async with self.locks['mongo']:
                collection = self.mongo_db.user_profiles
                result = await collection.find_one({"user_id": user_id})
                if result:
                    return {
                        "user_id": result["user_id"],
                        "username": result.get("username", ""),
                        "coins": result.get("coins", 0),
                        "total_xp": result.get("total_xp", 0),
                        "created_at": result.get("created_at", str(datetime.now())),
                        "last_active": result.get("last_active", str(datetime.now()))
                    }
                return None
        except Exception as e:
            logger.error(f"❌ Error obteniendo perfil de usuario {user_id}: {e}")
            return None

    async def update_user_coins(self, user_id: str, coins: int, username: str = None) -> bool:
        """Actualiza las monedas del usuario en MongoDB y SQLite."""
        try:
            if self.mongo_db is not None:
                async with self.locks['mongo']:
                    collection = self.mongo_db.user_profiles
                    update_data = {
                        "coins": coins,
                        "last_active": str(datetime.now())
                    }
                    if username:
                        update_data["username"] = username
                        update_data["created_at"] = str(datetime.now())
                    await collection.update_one(
                        {"user_id": user_id},
                        {"$set": update_data},
                        upsert=True
                    )

            async with self.locks['sqlite']:
                async with self.sqlite_conn.cursor() as cursor:
                    await cursor.execute(
                        "INSERT OR REPLACE INTO users (user_id, username, coins, last_login) VALUES (?, ?, ?, ?)",
                        (user_id, username or "", coins, datetime.now())
                    )
                await self.sqlite_conn.commit()

            logger.info(f"✅ Monedas actualizadas para usuario {user_id}: {coins}")
            return True
        except Exception as e:
            logger.error(f"❌ Error actualizando monedas de usuario {user_id}: {e}")
            return False

    async def get_user_achievements(self, user_id: str) -> Dict[str, bool]:
        """Obtiene los logros de un usuario desde SQLite."""
        async with self.locks['sqlite']:
            try:
                async with self.sqlite_conn.execute(
                    "SELECT achievement_name FROM achievements WHERE user_id = ?",
                    (user_id,)
                ) as cursor:
                    achievements = [row["achievement_name"] for row in await cursor.fetchall()]
                    return {ach: True for ach in achievements}
            except Exception as e:
                logger.error(f"❌ Error obteniendo logros para {user_id}: {e}")
                return {}

    async def update_user_achievements(self, user_id: str, achievement_key: str) -> bool:
        """Actualiza los logros del usuario en MongoDB y SQLite."""
        try:
            achievement_rewards = {
                "primer_mascota": {"coins": 50, "xp": 100},
                "coleccionista_novato": {"coins": 100, "xp": 200},
                "primer_raro": {"coins": 80, "xp": 150},
                "explorador_items": {"coins": 60, "xp": 120}
            }
            reward = achievement_rewards.get(achievement_key, {"coins": 0, "xp": 0})

            if self.mongo_db is not None:
                async with self.locks['mongo']:
                    collection = self.mongo_db.user_achievements
                    await collection.update_one(
                        {"user_id": user_id, "achievement_key": achievement_key},
                        {"$set": {
                            "user_id": user_id,
                            "achievement_key": achievement_key,
                            "reward_coins": reward["coins"],
                            "reward_xp": reward["xp"],
                            "unlocked_at": str(datetime.now())
                        }},
                        upsert=True
                    )

            async with self.locks['sqlite']:
                async with self.sqlite_conn.cursor() as cursor:
                    await cursor.execute(
                        "INSERT OR IGNORE INTO achievements (user_id, achievement_name, unlocked_at) VALUES (?, ?, ?)",
                        (user_id, achievement_key, datetime.now())
                    )
                await self.sqlite_conn.commit()

            logger.info(f"✅ Logro {achievement_key} actualizado para usuario {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error actualizando logros de usuario {user_id}: {e}")
            return False

    async def update_pet_stats(self, user_id: str, pet_name: str, updates: Dict[str, Any]) -> bool:
        """Actualiza estadísticas de una mascota específica."""
        try:
            user_data = await self.get_user_pets(user_id)
            if pet_name not in user_data["mascotas"]:
                logger.error(f"❌ Mascota {pet_name} no encontrada para usuario {user_id}")
                return False

            pet = user_data["mascotas"][pet_name]
            pet.update(updates)
            await self.save_user_pets(user_id, user_data)
            logger.debug(f"✅ Estadísticas actualizadas para mascota {pet_name} de usuario {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error actualizando estadísticas de mascota {pet_name} para {user_id}: {e}")
            return False

    async def use_item(self, user_id: str, pet_name: str, item_name: str, quantity: int = 1) -> Dict[str, Any]:
        """Usa un item en una mascota específica y aplica sus efectos."""
        try:
            from utils.constants import PET_SHOP_ITEMS, RARE_ITEMS
            item_data = PET_SHOP_ITEMS.get(item_name, RARE_ITEMS.get(item_name))
            if not item_data:
                return {"success": False, "error": "Item no encontrado"}

            cooldown_key = f"{user_id}.{pet_name}.{item_name}"
            if cooldown_key in self.item_cooldowns and self.item_cooldowns[cooldown_key] > datetime.now():
                remaining = (self.item_cooldowns[cooldown_key] - datetime.now()).total_seconds() / 60
                return {"success": False, "error": f"Item en cooldown por {remaining:.1f} minutos"}

            user_data = await self.get_user_pets(user_id)
            if pet_name not in user_data["mascotas"]:
                return {"success": False, "error": "Mascota no encontrada"}

            pet = user_data["mascotas"][pet_name]
            inventory = pet.get("inventario", [])
            item = next((i for i in inventory if i["name"] == item_name), None)
            if not item:
                return {"success": False, "error": "Item no encontrado en el inventario"}

            updates = {}
            if item_data["effect"] == "Restaura 50 de energía":
                updates["energía"] = min(pet["max_energía"], pet["energía"] + 50)
            elif item_data["effect"] == "Aumenta felicidad en 20":
                updates["felicidad"] = min(100, pet["felicidad"] + 20)
            elif item_data["effect"] == "Restaura 50 de salud":
                updates["salud"] = min(pet["max_salud"], pet["salud"] + 50)
            elif item_data["effect"] == "Aumenta experiencia en 100":
                updates["experiencia"] = pet["experiencia"] + 100
            elif item_data["effect"] == "Otorga 50 monedas":
                user_data["coins"] = user_data.get("coins", 0) + 50
            elif item_data["effect"] == "Aumenta la probabilidad de obtener una mascota rara":
                self.item_cooldowns[user_id] = datetime.now() + timedelta(hours=1)
                updates["ticket_raro"] = "activado"
            elif item_data["effect"] == "Cambia el elemento de la mascota":
                from utils.constants import PET_ELEMENTS
                updates["elemento"] = random.choice(list(PET_ELEMENTS.keys()))
            elif item_data["effect"] == "Otorga una mascota rara aleatoria":
                from utils.constants import PET_NAMES_BY_RARITY, PET_TYPES, PET_ELEMENTS
                rare_class = random.choice(["Raro", "Épico"])
                rare_names = PET_NAMES_BY_RARITY[rare_class]
                rare_name = random.choice(rare_names)
                if rare_name in user_data["mascotas"]:
                    rare_name = f"{rare_name}_{random.randint(1, 100)}"
                rare_pet = {
                    "tipo": random.choice(list(PET_TYPES.keys())),
                    "clase": rare_class,
                    "elemento": random.choice(list(PET_ELEMENTS.keys())),
                    "emoji": PET_TYPES[random.choice(list(PET_TYPES.keys()))]["emoji"],
                    "nivel": 1,
                    "experiencia": 0,
                    "hambre": 50,
                    "energía": 80,
                    "felicidad": 70,
                    "salud": 100,
                    "estado": "activo",
                    "última_interacción": str(datetime.now()),
                    "max_energía": 80,
                    "max_salud": 100,
                    "habilidades": [],
                    "inventario": []
                }
                user_data["mascotas"][rare_name] = rare_pet
                updates["mascota_rara"] = rare_name

            inventory.remove(item)
            pet["inventario"] = inventory
            await self.update_pet_stats(user_id, pet_name, updates)
            await self.save_user_pets(user_id, user_data)
            self.item_cooldowns[cooldown_key] = datetime.now() + timedelta(minutes=item_data.get("cooldown", 30))
            return {"success": True, "updates": updates}
        except Exception as e:
            logger.error(f"❌ Error al usar item {item_name} en mascota {pet_name} de usuario {user_id}: {e}")
            return {"success": False, "error": str(e)}

    async def update_mission_progress(self, user_id: str, mission_key: str, progress: int = 1) -> bool:
        """Actualiza el progreso de una misión en MongoDB."""
        if self.mongo_db is not None:
            logger.warning(f"⚠️ MongoDB no disponible para actualizar misión de {user_id}")
            return False
        try:
            collection = self.mongo_db.pets
            mission_type, mission_name = mission_key.split(".")
            await collection.update_one(
                {"user_id": user_id},
                {"$inc": {f"misiones.{mission_type}.{mission_name}.progreso": progress}},
                upsert=True
            )
            logger.info(f"✅ Progreso de misión {mission_key} actualizado para usuario {user_id}: +{progress}")
            return True
        except Exception as e:
            logger.error(f"❌ Error actualizando misión {mission_key} para {user_id}: {e}")
            return False

    async def set_afk(self, user_id: str, reason: str) -> bool:
        """Marca a un usuario como AFK en SQLite."""
        async with self.locks['sqlite']:
            try:
                async with self.sqlite_conn.cursor() as cursor:
                    await cursor.execute(
                        "INSERT OR REPLACE INTO afk_users (user_id, reason, afk_since) VALUES (?, ?, ?)",
                        (user_id, reason, datetime.now())
                    )
                await self.sqlite_conn.commit()
                logger.info(f"✅ Usuario {user_id} marcado como AFK: {reason}")
                return True
            except Exception as e:
                logger.error(f"❌ Error marcando usuario {user_id} como AFK: {e}")
                return False

    async def remove_afk(self, user_id: str) -> bool:
        """Elimina el estado AFK de un usuario."""
        async with self.locks['sqlite']:
            try:
                async with self.sqlite_conn.cursor() as cursor:
                    await cursor.execute(
                        "DELETE FROM afk_users WHERE user_id = ?",
                        (user_id,)
                    )
                await self.sqlite_conn.commit()
                logger.info(f"✅ Estado AFK eliminado para usuario {user_id}")
                return True
            except Exception as e:
                logger.error(f"❌ Error eliminando AFK para usuario {user_id}: {e}")
                return False

    async def get_afk_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene la información AFK de un usuario."""
        async with self.locks['sqlite']:
            try:
                async with self.sqlite_conn.execute(
                    "SELECT reason, afk_since FROM afk_users WHERE user_id = ?",
                    (user_id,)
                ) as cursor:
                    result = await cursor.fetchone()
                    if result:
                        return {
                            "reason": result["reason"],
                            "afk_since": result["afk_since"]
                        }
                    return None
            except Exception as e:
                logger.error(f"❌ Error obteniendo estado AFK para {user_id}: {e}")
                return None

    async def add_blacklist(self, user_id: str, reason: str) -> bool:
        """Añade un usuario a la lista negra en SQLite."""
        async with self.locks['sqlite']:
            try:
                async with self.sqlite_conn.cursor() as cursor:
                    await cursor.execute(
                        "INSERT OR REPLACE INTO blacklist (user_id, reason, banned_at) VALUES (?, ?, ?)",
                        (user_id, reason, datetime.now())
                    )
                await self.sqlite_conn.commit()
                logger.info(f"✅ Usuario {user_id} añadido a la lista negra: {reason}")
                return True
            except Exception as e:
                logger.error(f"❌ Error añadiendo usuario {user_id} a la lista negra: {e}")
                return False

    async def remove_blacklist(self, user_id: str) -> bool:
        """Elimina un usuario de la lista negra."""
        async with self.locks['sqlite']:
            try:
                async with self.sqlite_conn.cursor() as cursor:
                    await cursor.execute(
                        "DELETE FROM blacklist WHERE user_id = ?",
                        (user_id,)
                    )
                await self.sqlite_conn.commit()
                logger.info(f"✅ Usuario {user_id} eliminado de la lista negra")
                return True
            except Exception as e:
                logger.error(f"❌ Error eliminando usuario {user_id} de la lista negra: {e}")
                return False

    async def is_blacklisted(self, user_id: str) -> bool:
        """Verifica si un usuario está en la lista negra."""
        async with self.locks['sqlite']:
            try:
                async with self.sqlite_conn.execute(
                    "SELECT user_id FROM blacklist WHERE user_id = ?",
                    (user_id,)
                ) as cursor:
                    result = await cursor.fetchone()
                    return bool(result)
            except Exception as e:
                logger.error(f"❌ Error verificando lista negra para {user_id}: {e}")
                return False

    async def reset_missions(self, user_id: str) -> bool:
        """Reinicia las misiones de un usuario en MongoDB."""
        if self.mongo_db is not None:
            logger.warning(f"⚠️ MongoDB no disponible para reiniciar misiones de {user_id}")
            return False
        try:
            async with self.locks['mongo']:
                collection = self.mongo_db.pets
                await collection.update_one(
                    {"user_id": user_id},
                    {"$set": {"misiones": {}}},
                    upsert=True
                )
                logger.info(f"✅ Misiones reiniciadas para usuario {user_id}")
                return True
        except Exception as e:
            logger.error(f"❌ Error reiniciando misiones para {user_id}: {e}")
            return False

    async def update_all_pets_periodically(self):
        """Actualiza periódicamente las estadísticas de todas las mascotas."""
        try:
            async with self.locks['sqlite']:
                async with self.sqlite_conn.execute("SELECT user_id, pet_name, pet_data FROM pets") as cursor:
                    pets = await cursor.fetchall()
                    for pet in pets:
                        user_id = pet["user_id"]
                        pet_name = pet["pet_name"]
                        pet_data = json.loads(pet["pet_data"])
                        last_interaction = datetime.fromisoformat(pet_data.get("última_interacción", str(datetime.now())))
                        time_diff = (datetime.now() - last_interaction).total_seconds() / 3600  # Horas

                        if time_diff >= 1:
                            updates = {
                                "hambre": max(0, pet_data.get("hambre", 50) - int(time_diff * 5)),
                                "energía": max(0, pet_data.get("energía", 80) - int(time_diff * 3)),
                                "felicidad": max(0, pet_data.get("felicidad", 70) - int(time_diff * 4)),
                                "última_interacción": str(datetime.now())
                            }
                            pet_data.update(updates)
                            user_data = await self.get_user_pets(user_id)
                            user_data["mascotas"][pet_name] = pet_data
                            await self.save_user_pets(user_id, user_data)
                            logger.debug(f"✅ Actualizadas estadísticas de {pet_name} para {user_id}")
            logger.info("✅ Actualización periódica de mascotas completada")
        except Exception as e:
            logger.error(f"❌ Error en actualización periódica de mascotas: {e}")

    async def check_mission_resets(self):
        """Verifica y reinicia misiones diarias si es necesario."""
        try:
            # Intentar importar DAILY_RESET_HOUR, usar 0 (medianoche) como predeterminado
            try:
                from utils.constants import DAILY_RESET_HOUR
            except ImportError:
                logger.warning("⚠️ DAILY_RESET_HOUR no encontrado en utils.constants, usando 0 (medianoche)")
                DAILY_RESET_HOUR = 0

            current_time = datetime.now()
            reset_key = current_time.strftime("%Y-%m-%d")

            if self.mongo_db is not None and reset_key not in self.mission_resets:
                async with self.locks['mongo']:
                    collection = self.mongo_db.pets
                    cursor = collection.find()
                    async for user in cursor:
                        user_id = user["user_id"]
                        if user.get("misiones", {}).get("diarias"):
                            await self.reset_missions(user_id)
                    self.mission_resets[reset_key] = True
                    logger.info(f"✅ Misiones diarias reiniciadas para {reset_key}")
        except Exception as e:
            logger.error(f"❌ Error en verificación de reinicio de misiones: {e}")

    async def create_guild(self, guild_id: str, guild_data: Dict[str, Any]) -> bool:
        """Crea un nuevo gremio en SQLite y MongoDB."""
        try:
            guild_data["guild_id"] = guild_id
            guild_data["created_at"] = str(datetime.now())
            guild_data["last_updated"] = str(datetime.now())

            if self.mongo_db is not None:
                async with self.locks['mongo']:
                    collection = self.mongo_db.guilds
                    await collection.replace_one(
                        {"guild_id": guild_id},
                        guild_data,
                        upsert=True
                    )

            async with self.locks['sqlite']:
                async with self.sqlite_conn.cursor() as cursor:
                    await cursor.execute(
                        "INSERT OR REPLACE INTO guilds (guild_id, guild_data, last_updated) VALUES (?, ?, ?)",
                        (guild_id, json.dumps(guild_data), datetime.now())
                    )
                await self.sqlite_conn.commit()

            logger.info(f"✅ Gremio {guild_id} creado")
            return True
        except Exception as e:
            logger.error(f"❌ Error creando gremio {guild_id}: {e}")
            return False

    async def get_guild(self, guild_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene los datos de un gremio desde SQLite."""
        async with self.locks['sqlite']:
            try:
                async with self.sqlite_conn.execute(
                    "SELECT guild_data FROM guilds WHERE guild_id = ?",
                    (guild_id,)
                ) as cursor:
                    result = await cursor.fetchone()
                    if result:
                        return json.loads(result["guild_data"])
                    return None
            except Exception as e:
                logger.error(f"❌ Error obteniendo gremio {guild_id}: {e}")
                return None

    async def update_guild(self, guild_id: str, updates: Dict[str, Any]) -> bool:
        """Actualiza los datos de un gremio."""
        try:
            guild_data = await self.get_guild(guild_id)
            if not guild_data:
                logger.error(f"❌ Gremio {guild_id} no encontrado")
                return False

            guild_data.update(updates)
            guild_data["last_updated"] = str(datetime.now())

            if self.mongo_db is not None:
                async with self.locks['mongo']:
                    collection = self.mongo_db.guilds
                    await collection.replace_one(
                        {"guild_id": guild_id},
                        guild_data,
                        upsert=True
                    )

            async with self.locks['sqlite']:
                async with self.sqlite_conn.cursor() as cursor:
                    await cursor.execute(
                        "INSERT OR REPLACE INTO guilds (guild_id, guild_data, last_updated) VALUES (?, ?, ?)",
                        (guild_id, json.dumps(guild_data), datetime.now())
                    )
                await self.sqlite_conn.commit()

            logger.info(f"✅ Gremio {guild_id} actualizado")
            return True
        except Exception as e:
            logger.error(f"❌ Error actualizando gremio {guild_id}: {e}")
            return False

    async def update_all_guilds_periodically(self):
        """Actualiza periódicamente todos los gremios."""
        try:
            async with self.locks['sqlite']:
                async with self.sqlite_conn.execute("SELECT guild_id, guild_data FROM guilds") as cursor:
                    guilds = await cursor.fetchall()
                    for guild in guilds:
                        guild_id = guild["guild_id"]
                        guild_data = json.loads(guild["guild_data"])
                        guild_data["last_updated"] = str(datetime.now())
                        guild_data["activity_points"] = guild_data.get("activity_points", 0) + 1
                        await self.update_guild(guild_id, guild_data)
            logger.info("✅ Actualización periódica de gremios completada")
        except Exception as e:
            logger.error(f"❌ Error en actualización periódica de gremios: {e}")

# Funciones de compatibilidad
db = None

async def init_db(bot):
    global db
    try:
        db = HybridDatabase(bot)
        await db.initialize()
        return db
    except Exception as e:
        logger.error(f"❌ Error en init_db: {e}")
        raise

async def get_user_pets(user_id: str) -> Dict[str, Any]:
    if db is None:
        raise ValueError("Database not initialized")
    return await db.get_user_pets(user_id)

async def save_user_pets(user_id: str, user_data: Dict[str, Any]) -> bool:
    if db is None:
        raise ValueError("Database not initialized")
    return await db.save_user_pets(user_id, user_data)

async def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    if db is None:
        raise ValueError("Database not initialized")
    return await db.get_user_profile(user_id)

async def update_user_coins(user_id: str, amount: int, username: str = None) -> bool:
    if db is None:
        raise ValueError("Database not initialized")
    return await db.update_user_coins(user_id, amount, username)

async def get_user_achievements(user_id: str) -> Dict[str, bool]:
    if db is None:
        raise ValueError("Database not initialized")
    return await db.get_user_achievements(user_id)

async def update_user_achievements(user_id: str, achievement_key: str) -> bool:
    if db is None:
        raise ValueError("Database not initialized")
    return await db.update_user_achievements(user_id, achievement_key)

async def update_pet_stats(user_id: str, pet_name: str, updates: Dict[str, Any]) -> bool:
    if db is None:
        raise ValueError("Database not initialized")
    return await db.update_pet_stats(user_id, pet_name, updates)

async def use_item(user_id: str, pet_name: str, item_name: str, quantity: int = 1) -> Dict[str, Any]:
    if db is None:
        raise ValueError("Database not initialized")
    return await db.use_item(user_id, pet_name, item_name, quantity)

async def update_mission_progress(user_id: str, mission_key: str, progress: int = 1) -> bool:
    if db is None:
        raise ValueError("Database not initialized")
    return await db.update_mission_progress(user_id, mission_key, progress)

async def set_afk(user_id: str, reason: str) -> bool:
    if db is None:
        raise ValueError("Database not initialized")
    return await db.set_afk(user_id, reason)

async def remove_afk(user_id: str) -> bool:
    if db is None:
        raise ValueError("Database not initialized")
    return await db.remove_afk(user_id)

async def get_afk_user(user_id: str) -> Optional[Dict[str, Any]]:
    if db is None:
        raise ValueError("Database not initialized")
    return await db.get_afk_user(user_id)

async def add_blacklist(user_id: str, reason: str) -> bool:
    if db is None:
        raise ValueError("Database not initialized")
    return await db.add_blacklist(user_id, reason)

async def remove_blacklist(user_id: str) -> bool:
    if db is None:
        raise ValueError("Database not initialized")
    return await db.remove_blacklist(user_id)

async def is_blacklisted(user_id: str) -> bool:
    if db is None:
        raise ValueError("Database not initialized")
    return await db.is_blacklisted(user_id)

async def reset_missions(user_id: str) -> bool:
    if db is None:
        raise ValueError("Database not initialized")
    return await db.reset_missions(user_id)

async def create_guild(guild_id: str, guild_data: Dict[str, Any]) -> bool:
    if db is None:
        raise ValueError("Database not initialized")
    return await db.create_guild(guild_id, guild_data)

async def get_guild(guild_id: str) -> Optional[Dict[str, Any]]:
    if db is None:
        raise ValueError("Database not initialized")
    return await db.get_guild(guild_id)

async def update_guild(guild_id: str, updates: Dict[str, Any]) -> bool:
    if db is None:
        raise ValueError("Database not initialized")
    return await db.update_guild(guild_id, updates)

async def periodic_tasks(bot):
    """Tareas periódicas para mantenimiento de la base de datos."""
    while True:
        try:
            if bot.db and bot.db.initialized:
                await bot.db.sqlite_manager.cleanup_old_cache(7)
                await bot.db.update_all_pets_periodically()
                await bot.db.check_mission_resets()
                await bot.db.update_all_guilds_periodically()
                logger.info("✅ Tareas periódicas ejecutadas")
            await asyncio.sleep(24 * 60 * 60)  # Cada 24 horas
        except Exception as e:
            logger.error(f"❌ Error en tareas periódicas: {e}")
            await asyncio.sleep(60)  # Reintentar tras 1 minuto si falla