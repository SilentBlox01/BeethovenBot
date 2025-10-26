# cogs/afk.py (versión corregida)
# Cambios principales:
# - Agregué un chequeo para db inicializado antes de usar set_afk, remove_afk, get_afk_user.
# - Inicializo self.bot.cache["afk"] si no existe en __init__.
# - Mejoré el logging con más detalles.
# - Agregué manejo de errores para el caso en que db sea None.
# - Mantuve el soporte legacy para m/afk y la lógica del listener on_message.

import discord
from discord import app_commands
from discord.ext import commands
from utils.rate_limiter import safe_interaction_response, safe_send_message
from utils.database import set_afk, remove_afk, get_afk_user, db, logger

class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.afk_cache = {}  # Cache local para mejor rendimiento
        # Inicializar cache global de AFK si no existe
        if not hasattr(self.bot, 'cache') or "afk" not in self.bot.cache:
            self.bot.cache = getattr(self.bot, 'cache', {})
            self.bot.cache["afk"] = {}
        logger.info("✅ AFK Cog inicializado")

    async def cog_load(self):
        """Carga los datos AFK al iniciar el cog"""
        try:
            if db is None or not db.initialized:
                logger.error("❌ Base de datos no inicializada para AFK")
                raise ValueError("Database not initialized")
            logger.info("🔄 Cargando datos AFK desde la base de datos...")
            # Nota: Podríamos cargar todos los usuarios AFK aquí si quisiéramos
            logger.info("✅ Sistema AFK inicializado con base de datos híbrida")
        except Exception as e:
            logger.error(f"❌ Error inicializando sistema AFK: {e}")

    @app_commands.command(name="afk", description="Establece un estado de ausencia.")
    @app_commands.describe(message="La razón de tu AFK (opcional)")
    async def afk(self, interaction: discord.Interaction, message: str = ""):
        """Establece el estado AFK de un usuario"""
        try:
            if db is None or not db.initialized:
                await safe_interaction_response(
                    interaction,
                    "❌ Error: Base de datos no disponible. Contacta al administrador.",
                    ephemeral=True
                )
                logger.error("❌ Intento de usar /afk sin base de datos inicializada")
                return

            user_id = interaction.user.id
            afk_reason = message or "AFK"
            
            # Guardar en base de datos híbrida
            success = await set_afk(user_id, afk_reason)
            
            if success:
                # Actualizar cache local y global
                self.afk_cache[user_id] = afk_reason
                self.bot.cache["afk"][user_id] = afk_reason
                
                embed = discord.Embed(
                    title="⏰ Estado AFK Establecido",
                    description=f"**{interaction.user.display_name}** está ahora AFK",
                    color=0x3498db
                )
                embed.add_field(name="Razón", value=afk_reason, inline=False)
                embed.add_field(name="Sistema", value="Base de datos híbrida ✅", inline=True)
                
                await safe_interaction_response(interaction, embed=embed)
                logger.info(f"✅ Usuario {user_id} establecido como AFK: {afk_reason}")
                
            else:
                await safe_interaction_response(
                    interaction,
                    "❌ Error estableciendo estado AFK. Intenta más tarde.",
                    ephemeral=True
                )
                logger.error(f"❌ Error estableciendo AFK para usuario {user_id}")
                
        except Exception as e:
            logger.error(f"❌ Error en comando afk para usuario {user_id}: {e}")
            await safe_interaction_response(
                interaction,
                "❌ Ocurrió un error al establecer el estado AFK.",
                ephemeral=True
            )

    @app_commands.command(name="unafk", description="Quita el estado de ausencia.")
    async def unafk(self, interaction: discord.Interaction):
        """Remueve el estado AFK de un usuario"""
        try:
            if db is None or not db.initialized:
                await safe_interaction_response(
                    interaction,
                    "❌ Error: Base de datos no disponible. Contacta al administrador.",
                    ephemeral=True
                )
                logger.error("❌ Intento de usar /unafk sin base de datos inicializada")
                return

            user_id = interaction.user.id
            
            # Verificar si el usuario está AFK
            if user_id not in self.afk_cache and user_id not in self.bot.cache["afk"]:
                await safe_interaction_response(
                    interaction,
                    "ℹ️ No tenías un estado AFK activo.",
                    ephemeral=True
                )
                return
            
            # Remover de base de datos híbrida
            success = await remove_afk(user_id)
            
            if success:
                # Remover de caches locales
                self.afk_cache.pop(user_id, None)
                self.bot.cache["afk"].pop(user_id, None)
                
                embed = discord.Embed(
                    title="✅ Estado AFK Removido",
                    description=f"**{interaction.user.display_name}** ya no está AFK",
                    color=0x2ecc71
                )
                embed.add_field(name="Sistema", value="Base de datos híbrida ✅", inline=False)
                
                await safe_interaction_response(interaction, embed=embed)
                logger.info(f"✅ Usuario {user_id} removido de AFK")
                
            else:
                await safe_interaction_response(
                    interaction,
                    "❌ Error removiendo estado AFK. Intenta más tarde.",
                    ephemeral=True
                )
                logger.error(f"❌ Error removiendo AFK para usuario {user_id}")
                
        except Exception as e:
            logger.error(f"❌ Error en comando unafk para usuario {user_id}: {e}")
            await safe_interaction_response(
                interaction,
                "❌ Ocurrió un error al remover el estado AFK.",
                ephemeral=True
            )

    @commands.Cog.listener()
    async def on_message(self, message):
        """Maneja el sistema AFK en mensajes"""
        if message.author.bot:
            return

        try:
            if db is None or not db.initialized:
                logger.error("❌ Base de datos no disponible en on_message")
                return

            # Si el mensaje empieza con m/afk (legacy support)
            if message.content.startswith("m/afk "):
                razon = message.content[6:].strip()
                user_id = message.author.id
                
                # Establecer AFK en base de datos
                success = await set_afk(user_id, razon)
                if success:
                    self.afk_cache[user_id] = razon
                    self.bot.cache["afk"][user_id] = razon
                    
                    await safe_send_message(
                        message.channel,
                        f"{message.author.mention} está ahora AFK: {razon}"
                    )
                    logger.info(f"✅ AFK establecido via legacy para usuario {user_id}")
                return

            # Si el autor estaba en AFK, lo removemos
            user_id = message.author.id
            if user_id in self.afk_cache or user_id in self.bot.cache["afk"]:
                success = await remove_afk(user_id)
                if success:
                    self.afk_cache.pop(user_id, None)
                    self.bot.cache["afk"].pop(user_id, None)
                    
                    await safe_send_message(
                        message.channel,
                        f"👋 {message.author.mention} ya no está AFK."
                    )
                    logger.info(f"✅ AFK removido automáticamente para usuario {user_id}")

            # Si mencionaron a alguien AFK, notificar
            if message.mentions:
                for mentioned_user in message.mentions:
                    if mentioned_user.bot:
                        continue
                        
                    # Buscar en cache local primero
                    reason = self.afk_cache.get(mentioned_user.id)
                    if reason is None:
                        # Si no está en cache, buscar en base de datos
                        reason = await get_afk_user(mentioned_user.id)
                        if reason:
                            # Guardar en cache para futuras consultas
                            self.afk_cache[mentioned_user.id] = reason
                    
                    if reason is not None:
                        embed = discord.Embed(
                            title="⏰ Usuario Ausente",
                            description=f"{mentioned_user.display_name} está AFK",
                            color=0xf39c12
                        )
                        embed.add_field(name="Razón", value=reason, inline=False)
                        embed.set_footer(text="El usuario será notificado de tu mensaje")
                        
                        await safe_send_message(message.channel, embed=embed)
                        logger.debug(f"🔔 Notificación AFK para {mentioned_user.id}")
                        break  # Solo un mensaje por comando
                        
        except Exception as e:
            logger.error(f"❌ Error en listener AFK para mensaje de {message.author.id}: {e}")

    async def cog_unload(self):
        """Limpia recursos al descargar el cog"""
        try:
            self.afk_cache.clear()
            logger.info("🧹 Cache AFK limpiado")
        except Exception as e:
            logger.error(f"❌ Error limpiando cache AFK: {e}")

async def setup(bot):
    try:
        await bot.add_cog(AFK(bot))
        logger.info("✅ Cog AFK cargado correctamente")
    except Exception as e:
        logger.error(f"❌ Error cargando Cog AFK: {e}")
        raise