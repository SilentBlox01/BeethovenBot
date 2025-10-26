# cogs/utility.py
import discord
from discord import app_commands
from discord.ext import commands
from utils.rate_limiter import safe_followup_send  # ✅ Cambiado por safe_followup_send
from datetime import datetime
from utils.database import db

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def make_embed(self, title: str, description: str = None, color: int = 0x2F3136):
        embed = discord.Embed(title=title, description=description or "", color=color)
        embed.timestamp = datetime.utcnow()
        return embed

    @app_commands.command(name="serverinfo", description="Muestra la información del servidor.")
    @app_commands.checks.has_permissions(administrator=True)
    async def serverinfo(self, interaction: discord.Interaction):
        await interaction.response.defer()  # ✅ Añadido para usar safe_followup_send
        guild = interaction.guild
        
        embed = self.make_embed("Información del servidor", color=discord.Color.blurple().value)
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
            
        embed.add_field(name="Nombre", value=guild.name, inline=True)
        embed.add_field(name="ID", value=guild.id, inline=True)
        embed.add_field(name="Propietario", value=f"{guild.owner} ({guild.owner.id})", inline=True)
        embed.add_field(name="Miembros", value=guild.member_count, inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Canales", value=len(guild.channels), inline=True)
        embed.add_field(name="Creado el", value=guild.created_at.strftime("%d/%m/%Y"), inline=True)
        
        await safe_followup_send(interaction, embed=embed)  # ✅ Cambiado por safe_followup_send

    @app_commands.command(name="avatar", description="Muestra el avatar de un usuario")
    @app_commands.describe(member="El miembro (opcional, por defecto tú)")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None):
        await interaction.response.defer()  # ✅ Añadido para usar safe_followup_send
        member = member or interaction.user
        embed = self.make_embed(f"Avatar de {member}", color=discord.Color.purple().value)
        embed.set_image(url=member.avatar.url if member.avatar else member.default_avatar.url)
        await safe_followup_send(interaction, embed=embed)  # ✅ Cambiado por safe_followup_send

    @app_commands.command(name="ping", description="Muestra la latencia del bot")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.defer()  # ✅ Añadido para usar safe_followup_send
        latency = round(self.bot.latency * 1000)
        await safe_followup_send(interaction, f"🏓 Pong! Latencia: {latency}ms")  # ✅ Cambiado por safe_followup_send

async def setup(bot):
    await bot.add_cog(Utility(bot))