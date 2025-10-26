import discord
from discord import app_commands
from discord.ext import commands
import qrcode
import io
from utils.rate_limiter import safe_interaction_response
from utils.database import db

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="qr", description="Genera un código QR a partir de un texto.")
    @app_commands.describe(text="El texto para el QR")
    async def qr_cmd(self, interaction: discord.Interaction, text: str):
        try:
            # Generar QR en memoria
            img = qrcode.make(text)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            
            file = discord.File(buf, filename="qr.png")
            await safe_interaction_response(interaction, file=file)
            
        except Exception as e:
            await safe_interaction_response(
                interaction, 
                f"❌ Error al generar QR: {e}", 
                ephemeral=True
            )

    @app_commands.command(name="morse", description="Convierte un texto a código Morse.")
    @app_commands.describe(message="El mensaje a convertir")
    async def morse(self, interaction: discord.Interaction, message: str):
        morse_code = {
            'a': '.-', 'b': '-...', 'c': '-.-.', 'd': '-..', 'e': '.', 'f': '..-.',
            'g': '--.', 'h': '....', 'i': '..', 'j': '.---', 'k': '-.-', 'l': '.-..',
            'm': '--', 'n': '-.', 'o': '---', 'p': '.--.', 'q': '--.-', 'r': '.-.',
            's': '...', 't': '-', 'u': '..-', 'v': '...-', 'w': '.--', 'x': '-..-',
            'y': '-.--', 'z': '--..', '0': '-----', '1': '.----', '2': '..---',
            '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...',
            '8': '---..', '9': '----.', '.': '.-.-.-', ',': '--..--', '?': '..--..',
            '!': '-.-.--', '-': '-....-', '/': '-..-.', '@': '.--.-.', '(': '-.--.',
            ')': '-.--.-', ' ': '/'
        }
        
        morse_message = ' '.join(morse_code.get(c.lower(), c) for c in message)
        await safe_interaction_response(interaction, f"`{morse_message}`")

    @app_commands.command(name="say", description="Haz que el bot diga lo que quieras.")
    @app_commands.describe(text="El texto que quieres que el bot diga.")
    @app_commands.checks.has_permissions(administrator=True)
    async def say(self, interaction: discord.Interaction, text: str):
        try:
            # Defer the response to prevent timeout
            await interaction.response.defer(ephemeral=True)
            # Send the public message immediately
            await interaction.channel.send(text)
            # Send ephemeral confirmation
            await interaction.followup.send("✅ Mensaje enviado.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error al enviar mensaje: {e}", 
                ephemeral=True
            )

    @app_commands.command(name="sobremi", description="Muestra información sobre el bot.")
    async def sobremi(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Acerca de mí", color=discord.Color.random())
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        
        embed.add_field(name="Nombre", value=self.bot.user.name, inline=True)
        embed.add_field(name="Creador", value="Beethoven", inline=True)
        embed.add_field(name="Lenguaje", value="Python 3.10+", inline=True)
        embed.add_field(name="Librería", value=f"discord.py {discord.__version__}", inline=True)
        embed.add_field(name="Servidores", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="Comandos", value=len(self.bot.tree.get_commands()), inline=True)
        
        embed.set_footer(text="¡Gracias por usar este software ^~^!")
        await safe_interaction_response(interaction, embed=embed)

    @app_commands.command(name="invite", description="Enlace para invitar al bot.")
    async def invite(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="¡Invítame!",
            description="Haz clic para invitarme a tu servidor.",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Enlace de invitación", 
            value="[Invitar](https://discord.com/oauth2/authorize?client_id=872866276232540190&scope=bot&permissions=2147483647)", 
            inline=False
        )
        await safe_interaction_response(interaction, embed=embed)

async def setup(bot):
    await bot.add_cog(Misc(bot))