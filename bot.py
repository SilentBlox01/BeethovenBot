from dotenv import load_dotenv  # Importar primero
load_dotenv()  # Cargar .env antes de cualquier import que use os.getenv

import os
import logging
import sys
import asyncio
import discord
from discord.ext import commands
from aiohttp import ClientTimeout, TCPConnector
import aiohttp
from pymongo import MongoClient
from collections import Counter
from flask import Flask
from threading import Thread

# Importar el sistema de base de datos híbrido
from utils.database import init_db, periodic_tasks
from utils.database import DatabaseManager
from utils.cache_manager import cache_manager
from utils.rate_limiter import GlobalRateLimiter, safe_send_message

# ====== CONFIG ======
TOKEN = os.getenv("TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
POSTGRES_URI = os.getenv("POSTGRES_URI")
SQLITE_PATH = os.getenv("SQLITE_PATH", "./data/beethoven_bot.db")

if not TOKEN:
    print("❌ ERROR: TOKEN no encontrado en variables de entorno.")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('beethoven_bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# ====== LOGGING ======
logger = logging.getLogger("BeethovenBot")
logger.info("Logging inicializado")

# ====== CONEXIÓN MONGODB (Legacy - para compatibilidad) ======
mongo_client = None
db_legacy = None
usuarios_col = None

try:
    if MONGO_URI:
        mongo_client = MongoClient(MONGO_URI)
        db_legacy = mongo_client["beethoven_db"]
        usuarios_col = db_legacy["usuarios"]
        logger.info("✅ Conexión a MongoDB legacy establecida")
    else:
        logger.warning("⚠️ MONGO_URI no configurado - sistema legacy deshabilitado")
except Exception as e:
    logger.error(f"❌ Error conectando a MongoDB legacy: {e}")

# ====== BOT CONFIG ======
class BeethovenBot(commands.AutoShardedBot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            case_insensitive=True,
            help_command=None,
            shard_count=5,
            chunk_guilds_at_startup=False
        )

        self.logger = logging.getLogger("BeethovenBot")
        self.cache = {"blacklist": set(), "afk": {}}
        self.emergency_mode = False
        self.http_session = None
        self.rate_limiter = GlobalRateLimiter()
        self.db_legacy = db_legacy
        self.db = None
        self._ready_once = False
        self.command_count = {}
        self.primary_shard_id = 0
        self.active_shards = set()
        self.failover_mode = False

        self.logger.info("BeethovenBot inicializado")

    async def setup_hook(self):
        """Hook de configuración que se ejecuta al iniciar el bot"""
        try:
            self.db = await init_db(self)
            self.logger.info("✅ Sistema de base de datos inicializado")
        except Exception as e:
            self.logger.error(f"❌ Error inicializando sistema de base de datos: {e}")
            raise

        # Start periodic tasks
        self.loop.create_task(periodic_tasks(self))

        # Cargar cogs
        cogs = [
            'cogs.events', 'cogs.moderation', 'cogs.utility', 'cogs.fun',
            'cogs.aniinfo', 'cogs.afk', 'cogs.calculator',
            'cogs.misc', 'cogs.report', 'cogs.help', 'cogs.pet_system',
            'cogs.pet_tuto', 'cogs.anime_sfw', 'cogs.dev', 'cogs.anime_nsfw',
            'cogs.anime_trivia', 'cogs.anime_sfw_extreme', 'cogs.anime_sfw_action', 'cogs.anime_sfw_angry',
            'cogs.anime_sfw_fun', 'cogs.anime_sfw_love', 'cogs.anime_sfw_sad', 'cogs.stats', 'cogs.stats_logger',
        ]
        
        loaded_cogs = []
        failed_cogs = []
        
        for cog in cogs:
            try:
                await self.load_extension(cog)
                loaded_cogs.append(cog)
                self.logger.info(f"✅ Cog cargado: {cog}")
            except Exception as e:
                failed_cogs.append(f"{cog}: {str(e)}")
                self.logger.error(f"❌ Error cargando {cog}: {str(e)}", exc_info=True)

        self.logger.info(f"📊 Resumen de cogs: {len(loaded_cogs)} cargados, {len(failed_cogs)} fallidos")
        if failed_cogs:
            self.logger.warning(f"⚠️ Cogs fallados: {', '.join([cog.split(':')[0] for cog in failed_cogs])}")

        # VERIFICACIÓN AUTOMÁTICA DE COMANDOS DUPLICADOS EN DISCORD
        try:
            await asyncio.sleep(3)
            global_commands = await self.tree.fetch_commands()
            command_names = [cmd.name for cmd in global_commands]
            duplicates = [name for name in set(command_names) if command_names.count(name) > 1]
            
            if duplicates:
                self.logger.warning(f"🚨 Comandos duplicados detectados en Discord: {duplicates}")
                self.logger.info("💡 Usa !hard_reset para limpiarlos")
            else:
                self.logger.info("✅ No se detectaron comandos duplicados en Discord")
                
        except Exception as e:
            self.logger.error(f"❌ Error en verificación automática: {e}")

        # Sincronizar comandos globales con reintentos
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                await asyncio.sleep(1)
                synced = await self.tree.sync()
                self.logger.info(f"🔄 {len(synced)} comandos sincronizados globalmente (intento {attempt + 1}/{max_attempts})")
                break
            except Exception as e:
                self.logger.error(f"❌ Error sincronizando comandos globales (intento {attempt + 1}/{max_attempts}): {e}")
                if attempt == max_attempts - 1:
                    self.logger.error("❌ Falló la sincronización de comandos después de todos los intentos")

    async def on_shard_ready(self, shard_id):
        """Se ejecuta cuando un shard específico está listo"""
        self.active_shards.add(shard_id)
        self.logger.info(f"🔌 Shard {shard_id} conectado - Shards activos: {self.active_shards}")

    async def on_shard_disconnect(self, shard_id):
        """Se ejecuta cuando un shard se desconecta"""
        if shard_id in self.active_shards:
            self.active_shards.remove(shard_id)
        self.logger.warning(f"🔴 Shard {shard_id} desconectado - Shards activos: {self.active_shards}")

    async def should_process_command(self, ctx_or_interaction):
        """Determina si este shard debe procesar el comando"""
        if hasattr(ctx_or_interaction, 'guild') and ctx_or_interaction.guild:
            shard_id = (ctx_or_interaction.guild.id >> 22) % self.shard_count
            return shard_id == self.primary_shard_id
        elif hasattr(ctx_or_interaction, 'guild') and ctx_or_interaction.guild is None:
            return True
        return False

    async def on_ready(self):
        """Se ejecuta cuando CADA SHARD se conecta"""
        if not self._ready_once:
            self._ready_once = True
            
            if self.http_session is None:
                try:
                    connector = TCPConnector(limit=10, limit_per_host=2)
                    timeout = ClientTimeout(total=30)
                    self.http_session = aiohttp.ClientSession(connector=connector, timeout=timeout)
                    self.logger.info("✅ Sesión HTTP inicializada")
                except Exception as e:
                    self.logger.error(f"❌ Error inicializando sesión HTTP: {e}")

# Crear el objeto bot antes de los comandos decorados
bot = BeethovenBot()

# Decorador para comandos que solo deben ejecutarse en el shard primario
def primary_shard_only():
    async def predicate(ctx):
        if await ctx.bot.should_process_command(ctx):
            return True
        return False
    return commands.check(predicate)

# Comandos de administración
@bot.command()
@commands.is_owner()
@primary_shard_only()
async def reload_cogs(ctx):
    """Recarga todos los cogs"""
    success_count = 0
    failed_cogs = []
    cogs = [
        'cogs.events', 'cogs.moderation', 'cogs.utility', 'cogs.fun',
        'cogs.aniinfo', 'cogs.afk', 'cogs.calculator',
        'cogs.misc', 'cogs.report', 'cogs.help', 'cogs.pet_system',
        'cogs.pet_tuto', 'cogs.dev', 'cogs.anime_nsfw',
        'cogs.anime_trivia',
    ]
    for cog in cogs:
        try:
            await bot.reload_extension(cog)
            success_count += 1
            bot.logger.info(f"✅ Cog recargado: {cog}")
        except Exception as e:
            failed_cogs.append(f"{cog}: {str(e)}")
            bot.logger.error(f"❌ Error recargando {cog}: {str(e)}", exc_info=True)
    embed = discord.Embed(title="🔄 Recarga Masiva de Cogs", color=discord.Color.gold())
    embed.add_field(name="✅ Recargados", value=success_count, inline=True)
    embed.add_field(name="❌ Fallidos", value=len(failed_cogs), inline=True)
    if failed_cogs:
        embed.add_field(name="Errores", value="\n".join(failed_cogs[:5]), inline=False)
    await safe_send_message(ctx.channel, embed=embed)

@bot.command()
@commands.is_owner()
@primary_shard_only()
async def sync(ctx, guild_id: str = None):
    try:
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            await bot.tree.clear_commands(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            await safe_send_message(ctx.channel, f"✅ {len(synced)} comandos sincronizados en el servidor {guild_id}")
        else:
            await bot.tree.clear_commands(guild=None)
            synced = await bot.tree.sync()
            await safe_send_message(ctx.channel, f"✅ {len(synced)} comandos sincronizados globalmente")
    except Exception as e:
        await safe_send_message(ctx.channel, f"❌ Error sincronizando: {str(e)}")

@bot.command()
@commands.is_owner()
@primary_shard_only()
async def status(ctx):
    embed = discord.Embed(title="🤖 Estado del Bot", color=discord.Color.green())
    embed.add_field(name="🏓 Latencia", value=f"{round(bot.latency * 1000)}ms", inline=True)
    embed.add_field(name="📊 Servidores", value=len(bot.guilds), inline=True)
    embed.add_field(name="📂 Cogs Cargados", value=len(bot.extensions), inline=True)
    emergency_status = "🔴 ACTIVO" if bot.emergency_mode else "🟢 INACTIVO"
    embed.add_field(name="🚨 Emergency Mode", value=emergency_status, inline=True)
    db_status = []
    if mongo_client:
        try:
            mongo_client.admin.command('ping')
            db_status.append("MongoDB Legacy: ✅")
        except:
            db_status.append("MongoDB Legacy: ❌")
    if bot.db and bot.db.initialized:
        db_status.append("Sistema Híbrido: ✅")
    else:
        db_status.append("Sistema Híbrido: ❌")
    embed.add_field(name="💾 Bases de Datos", value=" | ".join(db_status), inline=False)
    cache_stats = f"Entradas: {len(cache_manager.cache)} | Hits: {sum(item['hits'] for item in cache_manager.cache.values())}"
    embed.add_field(name="🔄 Caché", value=cache_stats, inline=True)
    await safe_send_message(ctx.channel, embed=embed)

@bot.command()
@commands.is_owner()
@primary_shard_only()
async def shard_status(ctx):
    """Muestra el estado de los shards"""
    embed = discord.Embed(title="🔌 Estado de Shards", color=discord.Color.blue())
    
    embed.add_field(name="🎯 Shard Primario", value=bot.primary_shard_id, inline=True)
    embed.add_field(name="🔌 Shards Activos", value=len(bot.active_shards), inline=True)
    embed.add_field(name="🛡️ Modo Failover", value="✅ ACTIVO" if bot.failover_mode else "❌ INACTIVO", inline=True)
    
    shards_list = ", ".join([f"Shard {s}" for s in sorted(bot.active_shards)])
    embed.add_field(name="📋 Shards Conectados", value=shards_list or "Ninguno", inline=False)
    
    embed.add_field(name="📊 Total Servidores", value=len(bot.guilds), inline=True)
    embed.add_field(name="🏓 Latencia", value=f"{round(bot.latency * 1000)}ms", inline=True)
    
    await safe_send_message(ctx.channel, embed=embed)

@bot.command()
@commands.is_owner()
@primary_shard_only()
async def debug_commands(ctx):
    """Comando de debug para verificar comandos duplicados"""
    all_commands = []
    for cmd in bot.tree.get_commands():
        if hasattr(cmd, 'commands'):
            all_commands.extend(cmd.commands)
        else:
            all_commands.append(cmd)
    
    command_names = [cmd.name for cmd in all_commands]
    duplicates = []
    for name in set(command_names):
        if command_names.count(name) > 1:
            duplicates.append(name)
    
    embed = discord.Embed(title="🔧 Debug - Comandos", color=discord.Color.blue())
    embed.add_field(name="Total comandos", value=len(all_commands), inline=True)
    embed.add_field(name="Comandos únicos", value=len(set(command_names)), inline=True)
    embed.add_field(name="Duplicados encontrados", value=len(duplicates), inline=True)
    
    if duplicates:
        embed.add_field(name="🚨 Comandos duplicados", value=", ".join(duplicates), inline=False)
        embed.color = discord.Color.red()
    else:
        embed.add_field(name="✅ Estado", value="No hay comandos duplicados", inline=False)
        embed.color = discord.Color.green()
    
    commands_list = "\n".join([f"`/{cmd.name}`" for cmd in all_commands[:20]])
    if len(all_commands) > 20:
        commands_list += f"\n... y {len(all_commands) - 20} más"
    
    embed.add_field(name="📋 Comandos registrados", value=commands_list, inline=False)
    
    await safe_send_message(ctx.channel, embed=embed)

@bot.command()
@commands.is_owner()
@primary_shard_only()
async def db_cleanup(ctx, days: int = 7):
    try:
        await bot.db.cleanup_old_cache(days)
        cache_manager.clear()
        embed = discord.Embed(
            title="🧹 Limpieza de Base de Datos",
            description=f"Limpieza completada correctamente",
            color=discord.Color.green()
        )
        embed.add_field(name="Caché limpiado", value="✅", inline=True)
        embed.add_field(name="Días conservados", value=f"{days} días", inline=True)
        await safe_send_message(ctx.channel, embed=embed)
    except Exception as e:
        await safe_send_message(ctx.channel, f"❌ Error en limpieza: {e}")

# ====== MANEJO DE ERRORES GLOBALES ======
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.NotOwner):
        await safe_send_message(ctx.channel, "❌ Este comando es solo para el dueño del bot.")
    elif isinstance(error, commands.MissingPermissions):
        await safe_send_message(ctx.channel, "❌ No tienes permisos para ejecutar este comando.")
    elif isinstance(error, commands.BotMissingPermissions):
        await safe_send_message(ctx.channel, "❌ Me faltan permisos para ejecutar este comando.")
    elif "predicate" in str(error):
        return
    else:
        bot.logger.error(f"Error no manejado en comando {ctx.command}: {error}", exc_info=True)
        await safe_send_message(ctx.channel, "❌ Ocurrió un error inesperado al ejecutar el comando.")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"¡Calma! Espera {round(error.retry_after, 1)}s para usar eso de nuevo.")

app = Flask("")

@app.route("/")
def home():
    return "BeethovenBot activo en Render 🚀"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ====== EJECUCIÓN ======
if __name__ == "__main__":
    # Ejecutar Flask en hilo separado
    Thread(target=run_flask).start()
    os.makedirs('./data', exist_ok=True)
    try:
        bot.run(TOKEN)
    except discord.errors.LoginFailure:
        logger.error("❌ TOKEN inválido")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("👋 Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}", exc_info=True)
        sys.exit(1)