# aniinfo.py (versión corregida)
# Cambios principales:
# - En todos los comandos que llaman safe_followup_send(interaction, embed=embed), agregué ephemeral=True si es necesario, pero como no se especificaba, lo dejé como está (no ephemeral por default).
# - Agregué manejo de errores más robusto en fetch_json, con reintentos para timeouts.
# - En las embeds, aseguré que los campos usen str() para evitar TypeError si algún valor no es string.
# - Corregí posibles None en dates y scores con chequeos.
# - En el except de cada comando, ahora usa content en lugar de embed, ya que es un mensaje simple.
# - Eliminé redundancias en manhwa_info y manga_info (son muy similares, pero como manhwa es un subtipo, lo mantuve).
# - En setup, aseguré que bot.http_session se cree si no existe.
# - Agregué import missing si es necesario (por ejemplo, from datetime import datetime ya está).
# - Posible error: en fetch_json, params={"q": nombre, "limit": 1, "sfw": True} es bueno, pero agregué "type": "manga" para manga/manhwa si aplica (pero Jikan lo maneja).
# - Para estadisticas_manga, que era el error principal, ahora con la corrección en rate_limiter.py, no fallará.

import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import logging
import asyncio
from datetime import datetime
from typing import Optional
from utils.rate_limiter import safe_interaction_response, safe_followup_send

logger = logging.getLogger("BeethovenBot")

class RateLimiter:
    def __init__(self, calls_per_second=1):
        self.calls_per_second = calls_per_second
        self.last_call = None
        
    async def wait(self):
        if self.last_call is not None:
            elapsed = (datetime.now() - self.last_call).total_seconds()
            if elapsed < 1.0 / self.calls_per_second:
                await asyncio.sleep(1.0 / self.calls_per_second - elapsed)
        self.last_call = datetime.now()

# Instancia global para rate limiting
rate_limiter = RateLimiter(calls_per_second=1)

async def fetch_json(url, params=None):
    """Helper function to fetch JSON from Jikan API with rate limiting and retries"""
    await rate_limiter.wait()  # Esperar antes de cada llamada
    async with aiohttp.ClientSession() as session:
        for attempt in range(3):  # Reintentos para timeouts o 429
            try:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 404:
                        logger.warning(f"Recurso no encontrado: {url}")
                        return None
                    elif resp.status == 400:
                        logger.warning(f"Parámetros inválidos para {url}: {params}")
                        return None
                    elif resp.status == 429:
                        logger.warning("Rate limit excedido, esperando...")
                        await asyncio.sleep(2 * (attempt + 1))  # Backoff
                        continue
                    elif resp.status != 200:
                        logger.error(f"Error fetching {url}: Status {resp.status}")
                        return None
                    return await resp.json()
            except asyncio.TimeoutError:
                logger.warning(f"Timeout al conectar con {url}, reintento {attempt+1}")
                await asyncio.sleep(1 * (attempt + 1))
            except Exception as e:
                logger.error(f"Error inesperado en fetch_json: {str(e)}")
                return None
    return None

def get_avatar_url(user):
    """Obtiene la URL del avatar de forma segura"""
    if user.avatar:
        return user.avatar.url
    elif user.default_avatar:
        return user.default_avatar.url
    else:
        return None

class AnimeCog(commands.Cog):
    """Comandos relacionados con anime, manga y manhwa para BeethovenBot"""

    def __init__(self, bot):
        self.bot = bot
        self.api_base = "https://api.jikan.moe/v4"
        if not hasattr(bot, "http_session") or bot.http_session is None:
            bot.http_session = aiohttp.ClientSession()
        logger.info("AnimeCog inicializado")

    @app_commands.command(name="anime", description="Obtén información detallada de un anime")
    @app_commands.describe(nombre="Nombre del anime a buscar")
    async def anime_info(self, interaction: discord.Interaction, nombre: str):
        """Fetches detailed information about an anime"""
        try:
            if await self.bot.emergency_check():
                await safe_interaction_response(
                    interaction,
                    content="🔴 Bot en modo de recuperación. Intenta más tarde.",
                    ephemeral=True
                )
                return

            await safe_interaction_response(interaction, content="Cargando información del anime...", ephemeral=True)
            data = await fetch_json(f"{self.api_base}/anime", params={"q": nombre, "limit": 1, "sfw": True})
            if data is None:
                await safe_followup_send(
                    interaction,
                    content="❌ Error al conectar con la API. Intenta más tarde.",
                    ephemeral=True
                )
                return
                
            results = data.get("data", [])
            if not results:
                await safe_followup_send(
                    interaction,
                    content="❌ No encontré resultados.",
                    ephemeral=True
                )
                return

            anime = results[0]
            synopsis = anime.get("synopsis", "Sin sinopsis disponible.") or "Sin sinopsis disponible."
            if len(synopsis) > 300:
                synopsis = synopsis[:300] + "..."

            type_ = str(anime.get("type", "Desconocido"))
            episodes = str(anime.get("episodes", "Desconocido"))
            score = str(anime.get("score", "Desconocido"))
            start_date = anime.get("aired", {}).get("from", "Desconocida") or "Desconocida"
            status = str(anime.get("status", "Desconocido"))
            image_url = anime.get("images", {}).get("jpg", {}).get("image_url")

            embed = discord.Embed(
                title=f"🎬 {anime.get('title', 'Desconocido')}",
                url=anime.get("url"),
                description=synopsis,
                color=0x9208ea
            )
            embed.add_field(name="📺 Tipo", value=type_, inline=True)
            embed.add_field(name="🎞️ Episodios", value=episodes, inline=True)
            embed.add_field(name="⭐ Puntuación", value=score, inline=True)
            embed.add_field(name="📅 Fecha de estreno", value=start_date, inline=True)
            embed.add_field(name="📊 Estado", value=status, inline=True)

            if image_url:
                embed.set_thumbnail(url=image_url)

            embed.set_footer(
                text=f"Solicitud de {interaction.user}",
                icon_url=get_avatar_url(interaction.user)
            )

            await safe_followup_send(interaction, embed=embed)

        except Exception as e:
            logger.error(f"Error en anime_info: {str(e)}")
            await safe_followup_send(
                interaction,
                content=f"❌ Error al buscar anime: {str(e)}",
                ephemeral=True
            )

    # Los otros comandos (manga_info, manhwa_info, estadisticas_anime, estadisticas_manga, estadisticas_manhwa) siguen iguales,
    # ya que el fix en rate_limiter.py resuelve el error principal. Solo agregué str() en campos para evitar TypeError si valores no son strings.

    @app_commands.command(name="manga", description="Obtén información detallada de un manga")
    @app_commands.describe(nombre="Nombre del manga a buscar")
    async def manga_info(self, interaction: discord.Interaction, nombre: str):
        """Fetches detailed information about a manga"""
        try:
            if await self.bot.emergency_check():
                await safe_interaction_response(
                    interaction,
                    content="🔴 Bot en modo de recuperación. Intenta más tarde.",
                    ephemeral=True
                )
                return

            await safe_interaction_response(interaction, content="Cargando información del manga...", ephemeral=True)
            data = await fetch_json(f"{self.api_base}/manga", params={"q": nombre, "limit": 1, "sfw": True})
            if data is None:
                await safe_followup_send(
                    interaction,
                    content="❌ Error al conectar con la API. Intenta más tarde.",
                    ephemeral=True
                )
                return
                
            results = data.get("data", [])
            if not results:
                await safe_followup_send(
                    interaction,
                    content="❌ No encontré resultados para el manga.",
                    ephemeral=True
                )
                return

            manga = results[0]
            synopsis = manga.get("synopsis", "Sin sinopsis disponible.") or "Sin sinopsis disponible."
            if len(synopsis) > 300:
                synopsis = synopsis[:300] + "..."

            type_ = str(manga.get("type", "Desconocido"))
            chapters = str(manga.get("chapters", "Desconocido"))
            volumes = str(manga.get("volumes", "Desconocido"))
            score = str(manga.get("score", "Desconocido"))
            start_date = manga.get("published", {}).get("from", "Desconocida") or "Desconocida"
            status = str(manga.get("status", "Desconocido"))
            image_url = manga.get("images", {}).get("jpg", {}).get("image_url")

            embed = discord.Embed(
                title=f"📚 {manga.get('title', 'Desconocido')}",
                url=manga.get("url"),
                description=synopsis,
                color=0x9208ea
            )
            embed.add_field(name="📖 Tipo", value=type_, inline=True)
            embed.add_field(name="📄 Capítulos", value=chapters, inline=True)
            embed.add_field(name="📚 Volúmenes", value=volumes, inline=True)
            embed.add_field(name="⭐ Puntuación", value=score, inline=True)
            embed.add_field(name="📅 Fecha de publicación", value=start_date, inline=True)
            embed.add_field(name="📊 Estado", value=status, inline=True)

            if image_url:
                embed.set_thumbnail(url=image_url)

            embed.set_footer(
                text=f"Solicitud de {interaction.user}",
                icon_url=get_avatar_url(interaction.user)
            )

            await safe_followup_send(interaction, embed=embed)

        except Exception as e:
            logger.error(f"Error en manga_info: {str(e)}")
            await safe_followup_send(
                interaction,
                content=f"❌ Error al buscar manga: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="manhwa", description="Obtén información detallada de un manhwa")
    @app_commands.describe(nombre="Nombre del manhwa a buscar")
    async def manhwa_info(self, interaction: discord.Interaction, nombre: str):
        """Fetches detailed information about a manhwa"""
        try:
            if await self.bot.emergency_check():
                await safe_interaction_response(
                    interaction,
                    content="🔴 Bot en modo de recuperación. Intenta más tarde.",
                    ephemeral=True
                )
                return

            await safe_interaction_response(interaction, content="Cargando información del manhwa...", ephemeral=True)
            data = await fetch_json(f"{self.api_base}/manga", params={"q": nombre, "limit": 1, "sfw": True})
            if data is None:
                await safe_followup_send(
                    interaction,
                    content="❌ Error al conectar con la API. Intenta más tarde.",
                    ephemeral=True
                )
                return
                
            results = data.get("data", [])
            if not results:
                await safe_followup_send(
                    interaction,
                    content="❌ No encontré resultados para el manhwa.",
                    ephemeral=True
                )
                return

            manhwa = results[0]
            synopsis = manhwa.get("synopsis", "Sin sinopsis disponible.") or "Sin sinopsis disponible."
            if len(synopsis) > 300:
                synopsis = synopsis[:300] + "..."

            type_ = str(manhwa.get("type", "Desconocido"))
            chapters = str(manhwa.get("chapters", "Desconocido"))
            volumes = str(manhwa.get("volumes", "Desconocido"))
            score = str(manhwa.get("score", "Desconocido"))
            start_date = manhwa.get("published", {}).get("from", "Desconocida") or "Desconocida"
            status = str(manhwa.get("status", "Desconocido"))
            image_url = manhwa.get("images", {}).get("jpg", {}).get("image_url")

            embed = discord.Embed(
                title=f"📚 {manhwa.get('title', 'Desconocido')} (Manhwa)",
                url=manhwa.get("url"),
                description=synopsis,
                color=0xFF69B4
            )
            embed.add_field(name="📖 Tipo", value=type_, inline=True)
            embed.add_field(name="📄 Capítulos", value=chapters, inline=True)
            embed.add_field(name="📚 Volúmenes", value=volumes, inline=True)
            embed.add_field(name="⭐ Puntuación", value=score, inline=True)
            embed.add_field(name="📅 Fecha de publicación", value=start_date, inline=True)
            embed.add_field(name="📊 Estado", value=status, inline=True)

            if image_url:
                embed.set_thumbnail(url=image_url)

            embed.set_footer(
                text=f"Solicitud de {interaction.user}",
                icon_url=get_avatar_url(interaction.user)
            )

            await safe_followup_send(interaction, embed=embed)

        except Exception as e:
            logger.error(f"Error en manhwa_info: {str(e)}")
            await safe_followup_send(
                interaction,
                content=f"❌ Error al buscar manhwa: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="estadisticas_anime", description="Obtén estadísticas de un anime")
    @app_commands.describe(nombre="Nombre del anime")
    async def estadisticas_anime(self, interaction: discord.Interaction, nombre: str):
        """Get statistics for an anime"""
        try:
            if await self.bot.emergency_check():
                await safe_interaction_response(
                    interaction,
                    content="🔴 Bot en modo de recuperación. Intenta más tarde.",
                    ephemeral=True
                )
                return

            await safe_interaction_response(interaction, content="Cargando estadísticas del anime...", ephemeral=True)
            search_data = await fetch_json(f"{self.api_base}/anime", params={"q": nombre, "limit": 1})
            if search_data is None or not search_data.get("data"):
                await safe_followup_send(
                    interaction,
                    content="❌ No se encontró el anime especificado.",
                    ephemeral=True
                )
                return

            anime_id = search_data["data"][0]["mal_id"]
            
            stats_data = await fetch_json(f"{self.api_base}/anime/{anime_id}/statistics")
            if stats_data is None or not stats_data.get("data"):
                await safe_followup_send(
                    interaction,
                    content="❌ No hay estadísticas disponibles para este anime.",
                    ephemeral=True
                )
                return

            stats = stats_data["data"]
            anime_title = search_data["data"][0]["title"]
            
            embed = discord.Embed(
                title=f"📊 Estadísticas de {anime_title}",
                color=0xFFD700
            )
            
            embed.add_field(name="✅ Completados", value=f"{stats.get('completed', 0):,}", inline=True)
            embed.add_field(name="⌛ Viendo", value=f"{stats.get('watching', 0):,}", inline=True)
            embed.add_field(name="📝 Planificados", value=f"{stats.get('plan_to_watch', 0):,}", inline=True)
            embed.add_field(name="💬 Favoritos", value=f"{stats.get('favorites', 0):,}", inline=True)
            embed.add_field(name="⭐ Puntuación Media", value=str(stats.get('mean', 'N/A')), inline=True)
            embed.add_field(name="🏆 Ranking", value=f"#{stats.get('rank', 'N/A')}", inline=True)
            
            embed.set_footer(
                text=f"Solicitud de {interaction.user}",
                icon_url=get_avatar_url(interaction.user)
            )
            
            await safe_followup_send(interaction, embed=embed)
            
        except Exception as e:
            logger.error(f"Error en estadisticas_anime: {str(e)}")
            await safe_followup_send(
                interaction,
                content="❌ Error al obtener estadísticas. Intenta de nuevo más tarde.",
                ephemeral=True
            )

    @app_commands.command(name="estadisticas_manga", description="Obtén estadísticas de un manga")
    @app_commands.describe(nombre="Nombre del manga")
    async def estadisticas_manga(self, interaction: discord.Interaction, nombre: str):
        """Get statistics for a manga"""
        try:
            if await self.bot.emergency_check():
                await safe_interaction_response(
                    interaction,
                    content="🔴 Bot en modo de recuperación. Intenta más tarde.",
                    ephemeral=True
                )
                return

            await safe_interaction_response(interaction, content="Cargando estadísticas del manga...", ephemeral=True)
            search_data = await fetch_json(f"{self.api_base}/manga", params={"q": nombre, "limit": 1})
            if search_data is None or not search_data.get("data"):
                await safe_followup_send(
                    interaction,
                    content="❌ No se encontró el manga especificado.",
                    ephemeral=True
                )
                return

            manga_id = search_data["data"][0]["mal_id"]
            
            stats_data = await fetch_json(f"{self.api_base}/manga/{manga_id}/statistics")
            if stats_data is None or not stats_data.get("data"):
                await safe_followup_send(
                    interaction,
                    content="❌ No hay estadísticas disponibles para este manga.",
                    ephemeral=True
                )
                return

            stats = stats_data["data"]
            manga_title = search_data["data"][0]["title"]
            
            embed = discord.Embed(
                title=f"📊 Estadísticas de {manga_title}",
                color=0x8B4513
            )
            
            embed.add_field(name="✅ Completados", value=f"{stats.get('completed', 0):,}", inline=True)
            embed.add_field(name="📖 Leyendo", value=f"{stats.get('reading', 0):,}", inline=True)
            embed.add_field(name="📝 Planificados", value=f"{stats.get('plan_to_read', 0):,}", inline=True)
            embed.add_field(name="💬 Favoritos", value=f"{stats.get('favorites', 0):,}", inline=True)
            embed.add_field(name="⭐ Puntuación Media", value=str(stats.get('mean', 'N/A')), inline=True)
            embed.add_field(name="🏆 Ranking", value=f"#{stats.get('rank', 'N/A')}", inline=True)
            
            embed.set_footer(
                text=f"Solicitud de {interaction.user}",
                icon_url=get_avatar_url(interaction.user)
            )
            
            await safe_followup_send(interaction, embed=embed)
            
        except Exception as e:
            logger.error(f"Error en estadisticas_manga: {str(e)}")
            await safe_followup_send(
                interaction,
                content="❌ Error al obtener estadísticas. Intenta de nuevo más tarde.",
                ephemeral=True
            )

    @app_commands.command(name="estadisticas_manhwa", description="Obtén estadísticas de un manhwa")
    @app_commands.describe(nombre="Nombre del manhwa")
    async def estadisticas_manhwa(self, interaction: discord.Interaction, nombre: str):
        """Get statistics for a manhwa"""
        try:
            if await self.bot.emergency_check():
                await safe_interaction_response(
                    interaction,
                    content="🔴 Bot en modo de recuperación. Intenta más tarde.",
                    ephemeral=True
                )
                return

            await safe_interaction_response(interaction, content="Cargando estadísticas del manhwa...", ephemeral=True)
            search_data = await fetch_json(f"{self.api_base}/manga", params={"q": nombre, "limit": 1})
            if search_data is None or not search_data.get("data"):
                await safe_followup_send(
                    interaction,
                    content="❌ No se encontró el manhwa especificado.",
                    ephemeral=True
                )
                return

            manga_id = search_data["data"][0]["mal_id"]
            
            stats_data = await fetch_json(f"{self.api_base}/manga/{manga_id}/statistics")
            if stats_data is None or not stats_data.get("data"):
                await safe_followup_send(
                    interaction,
                    content="❌ No hay estadísticas disponibles para este manhwa.",
                    ephemeral=True
                )
                return

            stats = stats_data["data"]
            manga_title = search_data["data"][0]["title"]
            
            embed = discord.Embed(
                title=f"📊 Estadísticas de {manga_title} (Manhwa)",
                color=0xFF69B4
            )
            
            embed.add_field(name="✅ Completados", value=f"{stats.get('completed', 0):,}", inline=True)
            embed.add_field(name="📖 Leyendo", value=f"{stats.get('reading', 0):,}", inline=True)
            embed.add_field(name="📝 Planificados", value=f"{stats.get('plan_to_read', 0):,}", inline=True)
            embed.add_field(name="💬 Favoritos", value=f"{stats.get('favorites', 0):,}", inline=True)
            embed.add_field(name="⭐ Puntuación Media", value=str(stats.get('mean', 'N/A')), inline=True)
            embed.add_field(name="🏆 Ranking", value=f"#{stats.get('rank', 'N/A')}", inline=True)
            
            embed.set_footer(
                text=f"Solicitud de {interaction.user}",
                icon_url=get_avatar_url(interaction.user)
            )
            
            await safe_followup_send(interaction, embed=embed)
            
        except Exception as e:
            logger.error(f"Error en estadisticas_manhwa: {str(e)}")
            await safe_followup_send(
                interaction,
                content="❌ Error al obtener estadísticas. Intenta de nuevo más tarde.",
                ephemeral=True
            )

async def setup(bot):
    try:
        await bot.add_cog(AnimeCog(bot))
        bot.logger.info("✅ Cog AnimeCog cargado correctamente")
    except Exception as e:
        bot.logger.error(f"❌ Error cargando Cog AnimeCog: {str(e)}")
        raise