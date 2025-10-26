import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os
import sys
import platform
import psutil
from datetime import datetime
from utils.rate_limiter import safe_interaction_response, safe_send_message
from utils.database import db

# ============================
# CONFIGURACIÓN DEL DESARROLLADOR
# ============================
DEVELOPER_IDS = [719366657558052944]  # <-- Tu ID
DEV_GUILD_ID = 819246949122834453     # <-- ID de tu servidor de desarrollo

class Developer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._synced = False  # Bandera para controlar sincronización

    async def is_developer(interaction: discord.Interaction) -> bool:
        """Verifica si el usuario es desarrollador"""
        return interaction.user.id in DEVELOPER_IDS

    # ====== COMANDOS DE SISTEMA ======
    @app_commands.command(name="dev_status", description="📊 Estado detallado del bot (Solo Desarrollador)")
    @app_commands.check(is_developer)
    @app_commands.guilds(discord.Object(id=DEV_GUILD_ID))
    async def dev_status(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🤖 Estado del Sistema - Developer", color=0x00ff00)

        embed.add_field(
            name="📊 Bot Info",
            value=f"**Servidores:** {len(self.bot.guilds)}\n"
                  f"**Usuarios:** {sum(g.member_count for g in self.bot.guilds)}\n"
                  f"**Shard:** {self.bot.shard_id or 'N/A'}\n"
                  f"**Latencia:** {round(self.bot.latency * 1000)}ms",
            inline=True
        )

        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent()

        embed.add_field(
            name="💻 Sistema",
            value=f"**RAM:** {memory_usage:.2f} MB\n"
                  f"**CPU:** {cpu_percent}%\n"
                  f"**Uptime:** {self.get_uptime()}\n"
                  f"**Python:** {platform.python_version()}",
            inline=True
        )

        loaded_cogs = len(self.bot.extensions)
        slash_commands = len(self.bot.tree.get_commands())

        embed.add_field(
            name="🔧 Bot Interno",
            value=f"**Cogs:** {loaded_cogs}\n"
                  f"**Comandos Slash:** {slash_commands}\n"
                  f"**Emergency Mode:** {'🔴 ON' if getattr(self.bot, 'emergency_mode', False) else '🟢 OFF'}\n"
                  f"**Cache AFK:** {len(getattr(self.bot, 'cache', {}).get('afk', {}))}",
            inline=True
        )

        await safe_interaction_response(interaction, embed=embed)

    # ====== COMANDOS DE COGS ======
    @app_commands.command(name="dev_reloadall", description="⚡ Recargar todos los cogs (Solo Desarrollador)")
    @app_commands.check(is_developer)
    @app_commands.guilds(discord.Object(id=DEV_GUILD_ID))
    async def dev_reloadall(self, interaction: discord.Interaction):
        loaded_cogs = list(self.bot.extensions.keys())
        if not loaded_cogs:
            await safe_interaction_response(interaction, "📂 No hay cogs para recargar")
            return

        success_count = 0
        failed_cogs = []

        for cog in loaded_cogs:
            try:
                await self.bot.reload_extension(cog)
                success_count += 1
            except Exception as e:
                failed_cogs.append(f"{cog}: {str(e)}")

        embed = discord.Embed(title="🔄 Recarga Masiva de Cogs", color=0xFFA500)
        embed.add_field(name="✅ Recargados", value=success_count, inline=True)
        embed.add_field(name="❌ Fallidos", value=len(failed_cogs), inline=True)

        if failed_cogs:
            embed.add_field(name="Errores", value="\n".join(failed_cogs[:3]), inline=False)

        await safe_interaction_response(interaction, embed=embed)
        print(f"🔧 {interaction.user} recargó {success_count} cogs")

    # ====== COMANDOS DE DEBUG ======
    @app_commands.command(name="dev_eval", description="💻 Ejecutar código Python (Solo Desarrollador)")
    @app_commands.describe(code="Código Python a ejecutar")
    @app_commands.check(is_developer)
    @app_commands.guilds(discord.Object(id=DEV_GUILD_ID))
    async def dev_eval(self, interaction: discord.Interaction, code: str):
        try:
            env = {
                'bot': self.bot,
                'interaction': interaction,
                'channel': interaction.channel,
                'guild': interaction.guild,
                'author': interaction.user,
                'discord': discord,
                'asyncio': asyncio,
                'os': os,
                'sys': sys
            }

            exec(f"async def __eval():\n    {code}", env)
            result = await env['__eval']()
            output = str(result) if result is not None else "✅ Ejecutado sin errores"

            embed = discord.Embed(title="💻 Eval Result", color=0x00FF00)
            embed.add_field(name="📥 Input", value=f"```py\n{code}\n```", inline=False)
            embed.add_field(name="📤 Output", value=f"```\n{output}\n```", inline=False)
            await safe_interaction_response(interaction, embed=embed)

        except Exception as e:
            embed = discord.Embed(title="❌ Eval Error", color=0xFF0000)
            embed.add_field(name="📥 Input", value=f"```py\n{code}\n```", inline=False)
            embed.add_field(name="💥 Error", value=f"```\n{str(e)}\n```", inline=False)
            await safe_interaction_response(interaction, embed=embed)

    # ====== COMANDO PARA LIMPIAR DUPLICADOS ======
    @app_commands.command(name="dev_clear_commands", description="🧹 Limpiar comandos duplicados (Solo Desarrollador)")
    @app_commands.check(is_developer)
    @app_commands.guilds(discord.Object(id=DEV_GUILD_ID))
    async def dev_clear_commands(self, interaction: discord.Interaction):
        """Comando para limpiar comandos duplicados"""
        try:
            # Limpiar comandos globales primero
            self.bot.tree.clear_commands(guild=None)
            await self.bot.tree.sync(guild=None)
            
            # Limpiar comandos del servidor de desarrollo
            dev_guild = discord.Object(id=DEV_GUILD_ID)
            self.bot.tree.clear_commands(guild=dev_guild)
            await self.bot.tree.sync(guild=dev_guild)
            
            # Sincronizar solo los comandos del cog Developer en el servidor de desarrollo
            self.bot.tree.copy_global_to(guild=dev_guild)
            await self.bot.tree.sync(guild=dev_guild)
            
            await safe_interaction_response(
                interaction, 
                "✅ Comandos duplicados limpiados y sincronizados correctamente"
            )
        except Exception as e:
            await safe_interaction_response(
                interaction, 
                f"❌ Error al limpiar comandos: {str(e)}"
            )

    # ====== UTILIDADES ======
    def get_uptime(self):
        delta = datetime.utcnow() - self.bot.start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds}s"

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await safe_interaction_response(
                interaction,
                "❌ **Acceso Denegado**\nEste comando es solo para el desarrollador del bot.",
                ephemeral=True
            )
        else:
            await safe_interaction_response(
                interaction,
                f"❌ Error: {str(error)}",
                ephemeral=True
            )


async def setup(bot):
    """Carga del Cog solo visible en el servidor del desarrollador"""
    if not hasattr(bot, 'start_time'):
        bot.start_time = datetime.utcnow()

    # Añadir el cog
    cog = Developer(bot)
    await bot.add_cog(cog)

    # Sincronizar SOLO UNA VEZ - usar bandera para evitar duplicados
    if not cog._synced:
        try:
            dev_guild = discord.Object(id=DEV_GUILD_ID)
            
            # Sincronizar comandos globales primero
            await bot.tree.sync()
            
            # Luego sincronizar solo en el servidor de desarrollo
            bot.tree.copy_global_to(guild=dev_guild)
            await bot.tree.sync(guild=dev_guild)
            
            cog._synced = True
            print(f"🧑‍💻 Comandos de desarrollo sincronizados en servidor {DEV_GUILD_ID}")
            
        except Exception as e:
            print(f"⚠️ Error sincronizando comandos de desarrollo: {e}")
    
    print("✅ Cog 'Developer' cargado correctamente.")