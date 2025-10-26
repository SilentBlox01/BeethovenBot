# cogs/moderation.py
import discord
import logging
from discord import app_commands
from discord.ext import commands
from utils.rate_limiter import safe_interaction_response, safe_send_message
from utils.database import add_blacklist, remove_blacklist, is_blacklisted, db, logger

logger = logging.getLogger(__name__)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ctx_menu = app_commands.ContextMenu(
            name='userinfo',  # Cambiado de 'User Info' a 'userinfo'
            callback=self.user_info_context
        )
        self.bot.tree.add_command(self.ctx_menu)

    async def cog_load(self):
        """Carga datos de moderación al iniciar el cog"""
        try:
            logger.info("🔄 Inicializando sistema de moderación con BD híbrida...")
            # El sistema de blacklist se carga automáticamente en el bot.cache
            logger.info("✅ Sistema de moderación inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando sistema de moderación: {e}")

    async def cog_check(self, ctx):
        """Check global para todos los comandos del cog"""
        return not getattr(self.bot, 'emergency_mode', False)

    # ====== COMANDOS DE MODERACIÓN ======
    @app_commands.command(name="ban", description="Banea a un miembro del servidor.")
    @app_commands.describe(member="El miembro a banear", reason="La razón del ban (opcional)")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Sin razón establecida."):
        """Banea a un usuario del servidor"""
        try:
            # Verificar si el usuario está en blacklist global
            is_global_blacklisted = await is_blacklisted(member.id)
            if is_global_blacklisted:
                embed = discord.Embed(
                    title="🔨 Usuario Baneado",
                    description=f"**{member.display_name}** ha sido baneado del servidor",
                    color=0xe74c3c
                )
                embed.add_field(name="Razón", value=reason, inline=True)
                embed.add_field(name="Estado", value="✅ En lista negra global", inline=True)
            else:
                embed = discord.Embed(
                    title="🔨 Usuario Baneado",
                    description=f"**{member.display_name}** ha sido baneado del servidor",
                    color=0xe74c3c
                )
                embed.add_field(name="Razón", value=reason, inline=True)

            await member.ban(reason=reason)
            await safe_interaction_response(interaction, embed=embed)
            logger.info(f"✅ Usuario {member.id} baneado por {interaction.user.id} - Razón: {reason}")
            
        except discord.Forbidden:
            await safe_interaction_response(
                interaction, 
                "❌ No tengo permisos para banear a este usuario.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"❌ Error banenado usuario {member.id}: {e}")
            await safe_interaction_response(
                interaction, 
                f"❌ Error al banear: {str(e)}", 
                ephemeral=True
            )

    @app_commands.command(name="kick", description="Expulsa a un miembro del servidor.")
    @app_commands.describe(member="El miembro a expulsar", reason="La razón del kick (opcional)")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Sin razón establecida."):
        """Expulsa a un usuario del servidor"""
        try:
            await member.kick(reason=reason)
            
            embed = discord.Embed(
                title="👢 Usuario Expulsado",
                description=f"**{member.display_name}** ha sido expulsado del servidor",
                color=0xf39c12
            )
            embed.add_field(name="Razón", value=reason, inline=True)
            
            await safe_interaction_response(interaction, embed=embed)
            logger.info(f"✅ Usuario {member.id} expulsado por {interaction.user.id} - Razón: {reason}")
            
        except discord.Forbidden:
            await safe_interaction_response(
                interaction,
                "❌ No tengo permisos para expulsar a este usuario.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"❌ Error expulsando usuario {member.id}: {e}")
            await safe_interaction_response(
                interaction,
                f"❌ Error al expulsar: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="purge", description="Elimina mensajes del canal.")
    @app_commands.describe(amount="Cantidad de mensajes a eliminar (1-100).")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, amount: int):
        """Elimina mensajes del canal actual"""
        if amount < 1 or amount > 100:
            await safe_interaction_response(
                interaction,
                "🚫 Debes ingresar un número entre 1 y 100.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        
        try:
            deleted = await interaction.channel.purge(limit=amount)
            
            embed = discord.Embed(
                title="🧹 Mensajes Eliminados",
                description=f"Se eliminaron **{len(deleted)}** mensajes del canal",
                color=0x2ecc71
            )
            embed.add_field(name="Canal", value=interaction.channel.mention, inline=True)
            embed.add_field(name="Moderador", value=interaction.user.mention, inline=True)
            
            await safe_interaction_response(interaction, embed=embed, ephemeral=True)
            logger.info(f"✅ {len(deleted)} mensajes eliminados por {interaction.user.id} en #{interaction.channel.name}")
            
        except Exception as e:
            logger.error(f"❌ Error purgando mensajes: {e}")
            await safe_interaction_response(
                interaction,
                f"❌ Error al eliminar mensajes: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="blacklistadd", description="Añade un usuario a la lista negra global.")
    @app_commands.describe(user_id="El ID del usuario")
    @app_commands.checks.has_permissions(administrator=True)
    async def blacklistadd(self, interaction: discord.Interaction, user_id: str):
        """Añade un usuario a la lista negra global usando BD híbrida"""
        try:
            user_id_int = int(user_id)
            
            # Validaciones de seguridad
            if user_id_int == self.bot.user.id:
                await safe_interaction_response(
                    interaction,
                    "❌ No puedes añadir al bot a la lista negra.",
                    ephemeral=True
                )
                return
                
            if user_id_int == interaction.user.id:
                await safe_interaction_response(
                    interaction,
                    "❌ No puedes añadirte a ti mismo a la lista negra.",
                    ephemeral=True
                )
                return
            
            # Verificar si el usuario existe en Discord
            try:
                user = await self.bot.fetch_user(user_id_int)
                username = user.display_name
            except discord.NotFound:
                username = "Usuario desconocido"
            except Exception:
                username = "Usuario desconocido"

            # Añadir a la lista negra usando BD híbrida
            success = await add_blacklist(user_id_int)
            
            if success:
                # Actualizar cache del bot
                self.bot.cache["blacklist"].add(str(user_id_int))
                
                embed = discord.Embed(
                    title="🚫 Usuario Añadido a Lista Negra",
                    description=f"El usuario ha sido añadido a la lista negra global",
                    color=0xe74c3c
                )
                embed.add_field(name="ID de Usuario", value=f"`{user_id}`", inline=True)
                embed.add_field(name="Nombre", value=username, inline=True)
                embed.add_field(name="¡Exito!", value="¡Usuario añadido a la lista negra! ✅", inline=True)
                embed.set_footer(text="El usuario no podrá usar comandos del bot")
                
                await safe_interaction_response(interaction, embed=embed)
                logger.info(f"✅ Usuario {user_id} añadido a blacklist por {interaction.user.id}")
                
            else:
                await safe_interaction_response(
                    interaction,
                    f"⚠️ El usuario `{user_id}` ya estaba en la lista negra global.",
                    ephemeral=True
                )
                
        except ValueError:
            await safe_interaction_response(
                interaction,
                "❌ Por favor, introduce un ID de usuario válido (solo números).",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"❌ Error añadiendo a blacklist usuario {user_id}: {e}")
            await safe_interaction_response(
                interaction,
                f"❌ Error al añadir a la lista negra: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="blacklistremove", description="Elimina un usuario de la lista negra global.")
    @app_commands.describe(user_id="El ID del usuario")
    @app_commands.checks.has_permissions(administrator=True)
    async def blacklistremove(self, interaction: discord.Interaction, user_id: str):
        """Elimina un usuario de la lista negra global usando BD híbrida"""
        try:
            user_id_int = int(user_id)
            
            # Eliminar de la lista negra usando BD híbrida
            success = await remove_blacklist(user_id_int)
            
            if success:
                # Actualizar cache del bot
                self.bot.cache["blacklist"].discard(str(user_id_int))
                
                embed = discord.Embed(
                    title="✅ Usuario Removido de Lista Negra",
                    description=f"El usuario ha sido removido de la lista negra global",
                    color=0x2ecc71
                )
                embed.add_field(name="ID de Usuario", value=f"`{user_id}`", inline=True)
                
                await safe_interaction_response(interaction, embed=embed)
                logger.info(f"✅ Usuario {user_id} removido de blacklist por {interaction.user.id}")
                
            else:
                await safe_interaction_response(
                    interaction,
                    f"⚠️ El usuario `{user_id}` no se encontró en la lista negra global.",
                    ephemeral=True
                )
                
        except ValueError:
            await safe_interaction_response(
                interaction,
                "❌ Por favor, introduce un ID de usuario válido (solo números).",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"❌ Error removiendo de blacklist usuario {user_id}: {e}")
            await safe_interaction_response(
                interaction,
                f"❌ Error al eliminar de la lista negra: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="blacklistview", description="Muestra los usuarios en la lista negra global.")
    @app_commands.checks.has_permissions(administrator=True)
    async def blacklistview(self, interaction: discord.Interaction):
        """Muestra la lista negra global desde la BD híbrida"""
        try:
            blacklisted_users = self.bot.cache["blacklist"]
            
            if not blacklisted_users:
                embed = discord.Embed(
                    title="📝 Lista Negra Global",
                    description="La lista negra está actualmente vacía",
                    color=0x95a5a6
                )
                embed.set_footer(text="Lista de usuarios en la lista negra global.")
                await safe_interaction_response(interaction, embed=embed, ephemeral=True)
                return
            
            # Crear embed con la lista
            embed = discord.Embed(
                title="📋 Lista Negra Global",
                description=f"Total de usuarios: **{len(blacklisted_users)}**",
                color=0xff6b6b
            )
            
            # Convertir a lista y dividir en chunks si es muy larga
            user_list = list(blacklisted_users)
            chunks = [user_list[i:i + 10] for i in range(0, len(user_list), 10)]
            
            for i, chunk in enumerate(chunks):
                embed.add_field(
                    name=f"Usuarios {i*10 + 1}-{i*10 + len(chunk)}" if len(chunks) > 1 else "Usuarios en Lista Negra",
                    value="\n".join([f"`{user_id}`" for user_id in chunk]),
                    inline=False
                )
            
            embed.add_field(
                name="🔄 Actualizado",
                value="Cache en tiempo real",
                inline=True
            )
            
            await safe_interaction_response(interaction, embed=embed, ephemeral=True)
            logger.info(f"📊 Lista negra visualizada por {interaction.user.id} - {len(blacklisted_users)} usuarios")
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo lista negra: {e}")
            await safe_interaction_response(
                interaction,
                f"❌ Error al obtener la lista negra: {str(e)}",
                ephemeral=True
            )

    # ====== CONTEXT MENU ======
    async def user_info_context(self, interaction: discord.Interaction, member: discord.Member):
        """Context menu para información de usuario"""
        try:
            # Verificar si el usuario está en lista negra global
            is_blacklisted_user = await is_blacklisted(member.id)
            
            embed = discord.Embed(
                title=f"👤 Información de {member.display_name}",
                color=0x00f549
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            embed.add_field(name="🆔 ID", value=f"`{member.id}`", inline=True)
            embed.add_field(name="📅 Cuenta creada", value=member.created_at.strftime("%d/%m/%Y"), inline=True)
            embed.add_field(name="🔰 Estado", value="🚫 Lista Negra" if is_blacklisted_user else "✅ Normal", inline=True)
            
            await safe_interaction_response(interaction, embed=embed)
            
        except Exception as e:
            logger.error(f"❌ Error en context menu userinfo: {e}")
            await safe_interaction_response(
                interaction,
                "❌ Error al obtener información del usuario.",
                ephemeral=True
            )

    # ====== MANEJO DE ERRORES ======
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Manejo de errores específico del cog"""
        try:
            if isinstance(error, app_commands.MissingPermissions):
                embed = discord.Embed(
                    title="🚫 Permisos Insuficientes",
                    description="No tienes los permisos necesarios para usar este comando.",
                    color=0xe74c3c
                )
                await safe_interaction_response(interaction, embed=embed, ephemeral=True)
                
            elif isinstance(error, app_commands.BotMissingPermissions):
                embed = discord.Embed(
                    title="🤖 Permisos del Bot Insuficientes",
                    description="No tengo los permisos necesarios para ejecutar este comando.",
                    color=0xe74c3c
                )
                await safe_interaction_response(interaction, embed=embed, ephemeral=True)
                
            else:
                logger.error(f"❌ Error no manejado en moderación: {error}")
                embed = discord.Embed(
                    title="❌ Error del Sistema",
                    description="Ocurrió un error inesperado. Los desarrolladores han sido notificados.",
                    color=0xe74c3c
                )
                await safe_interaction_response(interaction, embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"❌ Error en manejo de errores de moderación: {e}")

    async def cog_unload(self):
        """Limpia recursos al descargar el cog"""
        try:
            self.bot.tree.remove_command(self.ctx_menu.name, type=self.ctx_menu.type)
            logger.info("🧹 Comandos de moderación limpiados")
        except Exception as e:
            logger.error(f"❌ Error limpiando comandos de moderación: {e}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))