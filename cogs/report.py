import discord
from discord.ext import commands
from discord import app_commands
from utils.rate_limiter import safe_interaction_response
from utils.database import db

class Report(commands.Cog):
    """Comandos para reportar bugs y sugerencias"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Coloca aquí el ID de tu canal de reportes en el servidor de prueba
        self.report_channel_id = 1426008011318493268  # <-- reemplaza con tu canal

    @app_commands.command(name="reportbug", description="Reporta un bug o sugerencia al servidor de prueba")
    @app_commands.describe(
        tipo="Tipo de reporte: bug o sugerencia",
        descripcion="Describe detalladamente tu reporte"
    )
    async def report(self, interaction: discord.Interaction, tipo: str, descripcion: str):
        # Obtener canal de reportes
        channel = interaction.guild.get_channel(self.report_channel_id)
        if channel is None:
            await safe_interaction_response(interaction, "❌ Canal de reportes no encontrado. Contacta al administrador.")
            return

        # Crear embed
        embed = discord.Embed(
            title=f"Nuevo reporte: {tipo.capitalize()}",
            description=descripcion,
            color=discord.Color.orange(),
            timestamp=interaction.created_at
        )
        embed.set_footer(text=f"Reportado por {interaction.user} | ID: {interaction.user.id}")

        # Enviar al canal de reportes
        await channel.send(embed=embed)
        await safe_interaction_response(interaction, "✅ Tu reporte ha sido enviado correctamente. Gracias por tu feedback!")

# ====== SETUP ======
async def setup(bot: commands.Bot):
    await bot.add_cog(Report(bot))
