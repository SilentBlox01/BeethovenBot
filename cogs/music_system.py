import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import asyncio
import logging
from typing import Optional
import functools
import urllib.parse

# Configuración de logging
logger = logging.getLogger(__name__)

# Opciones de yt-dlp (CORREGIDO: eliminado extract_flat)
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': False,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'socket_timeout': 30,
    'force_generic_extractor': False,
}

# Opciones de FFmpeg para streaming (MEJORADO)
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -probesize 32M -analyzeduration 32M',
    'options': '-vn -b:a 128k -bufsize 512k -af volume=0.5'
}

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title', 'Título desconocido')
        self.url = data.get('url', '')
        self.duration = data.get('duration', 0)
        self.thumbnail = data.get('thumbnail', '')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        try:
            # Crear copia de opciones sin extract_flat
            ytdl_opts = YTDL_OPTIONS.copy()
            
            with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
                data = await loop.run_in_executor(
                    None, lambda: ydl.extract_info(url, download=False)
                )

                if 'entries' in data:
                    data = data['entries'][0]  # Tomar el primer video si es una lista

                # Verificar que tenemos la URL de audio
                if not data.get('url'):
                    # Si no hay URL directa, buscar en formats
                    if 'formats' in data:
                        # Buscar el mejor formato de audio
                        for fmt in data['formats']:
                            if fmt.get('acodec') != 'none' and fmt.get('vcodec') == 'none':
                                data['url'] = fmt['url']
                                break
                    
                    if not data.get('url'):
                        raise ValueError("No se pudo encontrar un formato de audio válido")

                filename = data['url']
                return cls(
                    discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS),
                    data=data
                )
        except Exception as e:
            logger.error(f"Error extrayendo URL {url}: {e}")
            raise

class MusicSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}  # guild_id: [YTDLSource]
        self.currently_playing = {}  # guild_id: YTDLSource
        self.logger = logger

    async def ensure_voice(self, interaction: discord.Interaction):
        """Asegura que el usuario esté en un canal de voz y el bot pueda unirse"""
        if not interaction.user.voice:
            await interaction.response.send_message(
                "¡Debes estar en un canal de voz para usar este comando!", ephemeral=True
            )
            return False

        voice_channel = interaction.user.voice.channel
        voice_client = interaction.guild.voice_client

        if voice_client is None:
            try:
                voice_client = await voice_channel.connect()
            except Exception as e:
                self.logger.error(f"Error conectando al canal de voz {voice_channel.id}: {e}")
                await interaction.response.send_message(
                    "❌ No pude unirme al canal de voz. Verifica mis permisos.", ephemeral=True
                )
                return False
        elif voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)

        return voice_client

    @app_commands.command(name="play", description="Reproduce una canción desde YouTube")
    @app_commands.describe(query="URL de YouTube o término de búsqueda")
    async def play(self, interaction: discord.Interaction, query: str):
        """Reproduce una canción o la añade a la cola"""
        await interaction.response.defer()

        voice_client = await self.ensure_voice(interaction)
        if not voice_client:
            return

        guild_id = interaction.guild_id
        if guild_id not in self.queues:
            self.queues[guild_id] = []

        # Convertir búsqueda en URL si no lo es
        processed_query = query
        if not query.startswith(('http://', 'https://', 'ytsearch:')):
            processed_query = f"ytsearch:{query}"

        try:
            # Verificar si el usuario está en la lista negra (si existe la DB)
            if hasattr(self.bot, 'db') and self.bot.db:
                if await self.bot.db.is_blacklisted(interaction.user.id):
                    await interaction.followup.send(
                        "❌ Estás en la lista negra y no puedes usar comandos.", ephemeral=True
                    )
                    return

            # Extraer información del video
            source = await YTDLSource.from_url(processed_query, loop=self.bot.loop, stream=True)

            # Formatear duración
            duration_str = "?:??"
            if source.duration > 0:
                duration_str = f"{source.duration//60}:{source.duration%60:02d}"

            # Añadir a la cola
            self.queues[guild_id].append(source)
            embed = discord.Embed(
                title="🎵 Canción añadida a la cola",
                description=f"**{source.title}** ({duration_str})",
                color=discord.Color.blue()
            )
            if source.thumbnail:
                embed.set_thumbnail(url=source.thumbnail)
            await interaction.followup.send(embed=embed)

            # Actualizar estadísticas en la base de datos (si existe)
            if hasattr(self.bot, 'db') and self.bot.db:
                try:
                    await self.bot.db.update_mission_progress(
                        str(interaction.user.id), "play_songs", 1
                    )
                except Exception as e:
                    logger.warning(f"No se pudo actualizar estadísticas: {e}")

            # Reproducir si no hay nada en reproducción
            if not voice_client.is_playing() and not voice_client.is_paused():
                await self.play_next(guild_id, voice_client, interaction.channel)

        except Exception as e:
            self.logger.error(f"Error en comando /play: {e}")
            await interaction.followup.send(
                f"❌ Error al procesar la canción: {str(e)}. Intenta con otra URL o verifica que el video sea accesible.",
                ephemeral=True
            )

    async def play_next(self, guild_id: int, voice_client: discord.VoiceClient, channel: discord.TextChannel):
        """Reproduce la siguiente canción en la cola"""
        try:
            if guild_id not in self.queues or not self.queues[guild_id]:
                self.currently_playing.pop(guild_id, None)
                if voice_client.is_connected():
                    await voice_client.disconnect()
                embed = discord.Embed(
                    title="🎵 Cola finalizada",
                    description="No hay más canciones en la cola.",
                    color=discord.Color.blue()
                )
                await channel.send(embed=embed)
                return

            source = self.queues[guild_id].pop(0)
            self.currently_playing[guild_id] = source

            def after_playing(error):
                if error:
                    self.logger.error(f"Error en after_playing: {error}")
                # Programar la siguiente canción
                coro = self.play_next(guild_id, voice_client, channel)
                asyncio.run_coroutine_threadsafe(coro, self.bot.loop)

            voice_client.play(source, after=after_playing)
            
            # Formatear duración
            duration_str = "?:??"
            if source.duration > 0:
                duration_str = f"{source.duration//60}:{source.duration%60:02d}"
                
            embed = discord.Embed(
                title="🎵 Ahora reproduciendo",
                description=f"**{source.title}** ({duration_str})",
                color=discord.Color.green()
            )
            if source.thumbnail:
                embed.set_thumbnail(url=source.thumbnail)
            await channel.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Error reproduciendo canción: {e}")
            await channel.send(f"❌ Error al reproducir la canción: {str(e)}")
            # Intentar con la siguiente canción
            await self.play_next(guild_id, voice_client, channel)

    @app_commands.command(name="skip", description="Salta la canción actual")
    async def skip(self, interaction: discord.Interaction):
        """Salta la canción actual y reproduce la siguiente"""
        voice_client = await self.ensure_voice(interaction)
        if not voice_client:
            return

        if not voice_client.is_playing():
            await interaction.response.send_message(
                "❌ No hay ninguna canción reproduciéndose.", ephemeral=True
            )
            return

        voice_client.stop()
        await interaction.response.send_message("⏭️ Canción saltada.")

    @app_commands.command(name="pause", description="Pausa la reproducción actual")
    async def pause(self, interaction: discord.Interaction):
        """Pausa la reproducción"""
        voice_client = interaction.guild.voice_client
        if not voice_client or not voice_client.is_playing():
            await interaction.response.send_message("❌ No hay música reproduciéndose.", ephemeral=True)
            return
        
        if voice_client.is_paused():
            await interaction.response.send_message("❌ La música ya está pausada.", ephemeral=True)
            return
            
        voice_client.pause()
        await interaction.response.send_message("⏸️ Reproducción pausada.")

    @app_commands.command(name="resume", description="Reanuda la reproducción")
    async def resume(self, interaction: discord.Interaction):
        """Reanuda la reproducción"""
        voice_client = interaction.guild.voice_client
        if not voice_client or not voice_client.is_paused():
            await interaction.response.send_message("❌ La música no está pausada.", ephemeral=True)
            return
        
        voice_client.resume()
        await interaction.response.send_message("▶️ Reproducción reanudada.")

    @app_commands.command(name="stop", description="Detiene la reproducción y limpia la cola")
    async def stop(self, interaction: discord.Interaction):
        """Detiene la reproducción y limpia la cola"""
        voice_client = interaction.guild.voice_client
        if not voice_client:
            await interaction.response.send_message("❌ No estoy conectado a ningún canal de voz.", ephemeral=True)
            return

        guild_id = interaction.guild_id
        self.queues.pop(guild_id, None)
        self.currently_playing.pop(guild_id, None)
        
        if voice_client.is_playing():
            voice_client.stop()
            
        await voice_client.disconnect()
        await interaction.response.send_message("⏹️ Reproducción detenida y cola limpiada.")

    @app_commands.command(name="queue", description="Muestra la cola de reproducción")
    async def queue(self, interaction: discord.Interaction):
        """Muestra las canciones en la cola"""
        guild_id = interaction.guild_id
        if guild_id not in self.queues or not self.queues[guild_id]:
            await interaction.response.send_message("📭 La cola está vacía.", ephemeral=True)
            return

        embed = discord.Embed(title="🎶 Cola de reproducción", color=discord.Color.blue())
        
        # Mostrar canción actual si hay una
        current = self.currently_playing.get(guild_id)
        if current:
            duration_str = "?:??"
            if current.duration > 0:
                duration_str = f"{current.duration//60}:{current.duration%60:02d}"
            embed.add_field(
                name="🎵 **Reproduciendo ahora:**",
                value=f"**{current.title}** ({duration_str})",
                inline=False
            )
            embed.add_field(name="‎", value="**Siguientes:**", inline=False)  # Separador

        # Mostrar hasta 10 canciones en cola
        for i, song in enumerate(self.queues[guild_id][:10], 1):
            duration_str = "?:??"
            if song.duration > 0:
                duration_str = f"{song.duration//60}:{song.duration%60:02d}"
            embed.add_field(
                name=f"{i}. {song.title}",
                value=f"Duración: {duration_str}",
                inline=False
            )
            
        if len(self.queues[guild_id]) > 10:
            embed.set_footer(text=f"Y {len(self.queues[guild_id]) - 10} más...")
            
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="nowplaying", description="Muestra la canción actual")
    async def nowplaying(self, interaction: discord.Interaction):
        """Muestra la canción actual"""
        guild_id = interaction.guild_id
        current = self.currently_playing.get(guild_id)
        
        if not current:
            await interaction.response.send_message("❌ No hay ninguna canción reproduciéndose.", ephemeral=True)
            return
        
        duration_str = "?:??"
        if current.duration > 0:
            duration_str = f"{current.duration//60}:{current.duration%60:02d}"
            
        embed = discord.Embed(
            title="🎵 Reproduciendo ahora",
            description=f"**{current.title}** ({duration_str})",
            color=discord.Color.green()
        )
        if current.thumbnail:
            embed.set_thumbnail(url=current.thumbnail)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="disconnect", description="Desconecta el bot del canal de voz")
    async def disconnect(self, interaction: discord.Interaction):
        """Desconecta el bot del canal de voz"""
        voice_client = interaction.guild.voice_client
        if not voice_client:
            await interaction.response.send_message("❌ No estoy conectado a ningún canal de voz.", ephemeral=True)
            return

        guild_id = interaction.guild_id
        self.queues.pop(guild_id, None)
        self.currently_playing.pop(guild_id, None)
        
        await voice_client.disconnect()
        await interaction.response.send_message("👋 Desconectado del canal de voz.")

async def setup(bot):
    await bot.add_cog(MusicSystem(bot))