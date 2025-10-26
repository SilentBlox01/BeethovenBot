import discord
from discord.ext import commands
import logging
from typing import Dict, Any
from utils.database import get_user_pets, save_user_pets, update_mission_progress, is_blacklisted, get_afk_user, get_guild, update_guild
from utils.constants import PET_CLASSES
import utils.database as database
from utils.database import is_blacklisted, update_mission_progress, get_afk_user, get_guild, update_guild, get_user_pets
import os

logger = logging.getLogger(__name__)

class Events(commands.Cog):
    """Maneja los eventos globales de BeethovenBot"""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Evento cuando el bot está listo"""
        self.bot.logger.info(f"Bot conectado como {self.bot.user}")
        await self.bot.change_presence(activity=discord.Game(name="Cuidando mascotas 🐾"))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Manejo global de mensajes"""
        # Ignorar mensajes del bot
        if message.author.bot:
            return
        
        # Evitar uso de DB si aún no está lista
        if database.db is None or not database.db.initialized:
            logger.warning("⚠️ Base de datos no inicializada, mensaje ignorado.")
            return


        # Comprobar si el usuario está en blacklist
        if await is_blacklisted(message.author.id):
            return

        user_id = str(message.author.id)
        
        # Verificar si el usuario está AFK
        afk_reason = await get_afk_user(message.author.id)
        if afk_reason:
            await message.channel.send(f"{message.author.mention} está AFK: {afk_reason}")
            return

        # Obtener datos del usuario
        user_data = await get_user_pets(user_id)
        if not user_data:
            logger.error(f"No se pudieron obtener datos del usuario {user_id}")
            return
        
        # Actualizar progreso de misiones
        await update_mission_progress(user_id, "diarias.send_message", 1)

        # Actualizar datos de gremio si aplica
        if user_data.get("guild_id"):
            guild_data = await get_guild(user_data["guild_id"])
            if guild_data:
                guild_data["bank"] = guild_data.get("bank", 0) + 1
                guild_data["xp"] = guild_data.get("xp", 0) + 5
                guild_data["last_update"] = str(discord.utils.utcnow())
                await update_guild(user_data["guild_id"], guild_data)
                if guild_data["xp"] >= guild_data["level"] * 1000:
                    guild_data["level"] += 1
                    guild_data["xp"] = 0
                    await update_guild(user_data["guild_id"], guild_data)
                    await message.channel.send(f"🎉 ¡El gremio **{guild_data['name']}** ha subido al nivel {guild_data['level']}!")
        
        await self.bot.process_commands(message)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        """Evento al completar un comando"""
        user_id = str(ctx.author.id)
        if database.db and database.db.initialized:
            await update_mission_progress(user_id, "diarias.use_command", 1)

async def setup(bot):
    try:
        await bot.add_cog(Events(bot))
        bot.logger.info("✅ Cog Events cargado correctamente")
    except Exception as e:
        bot.logger.error(f"❌ Error cargando Cog Events: {str(e)}")
        raise