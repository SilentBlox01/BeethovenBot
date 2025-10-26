# cogs/anime_nsfw.py
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio
import random

class AnimeNSFW(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.nsfw_actions = {
            "Bite": "bite", "Slap": "slap", "Kick": "kick", "Hug": "hug", 
            "Kiss": "kiss", "Waifu": "waifu", "Neko": "neko"
        }
        self.phrases = {
            "Bite": ["¡Mordisco travieso como vampiro sexy!", "¡Bite bite hot!", "¡Ouch, pero rico!", "¡Muerde con pasión!", "¡Bite de amor prohibido!"],
            "Slap": ["¡Cachetada hot, toma eso!", "¡Slap slap spicy!", "¡Te mereces esto... sexy!", "¡Slap con fuego!", "¡Cachetada ardiente!"],
            "Kick": ["¡Patada intensa, fuera!", "¡Kick kick hot!", "¡Patada voladora sexy!", "¡Kick de dominación!", "¡Fuera con estilo hot!"],
            "Hug": ["¡Abrazo apasionado, cerca!", "¡Hug hot como infierno!", "¡Abrazo que quema!", "¡Hug infinito!", "¡Abrazo de fuego!"],
            "Kiss": ["¡Beso ardiente, chu!", "¡Beso volador sexy!", "¡Kiss kiss boom!", "¡Beso robado hot!", "¡Beso que derrite!"],
            "Waifu": ["¡Mi waifu perfecta, hot!", "¡Waifu queen sexy!", "¡Waifu mia, solo mia!", "¡Waifu hot level 100!", "¡Waifu de mis sueños!"],
            "Neko": ["¡Neko miau hot!", "¡Gatita sexy, miau!", "¡Neko neko spicy!", "¡Miau miau hot!", "¡Neko con colita!"]
        }
        self.reactions = ["🔥", "😈", "💋", "🌶️", "😏"]
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8))

    async def cog_unload(self):
        await self.session.close()

    async def fetch_nsfw_image(self, tag: str) -> str | None:
        api_urls = [
            f"https://api.waifu.pics/nsfw/{tag}",
            f"https://api.waifu.im/nsfw/{tag}?many=false",
        ]
        for url in api_urls:
            try:
                async with self.session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if "images" in data and len(data["images"]) > 0:
                            return data["images"][0]["url"]
                        if "url" in data:
                            return data["url"]
            except Exception:
                continue
        return None

    @commands.cooldown(1, 5, commands.BucketType.user)
    @app_commands.command(name="nsfw_interact", description="Interactúa NSFW (solo canales permitidos)")
    @app_commands.describe(action="Selecciona la acción NSFW", user="Menciona a alguien (opcional)")
    async def nsfw_interact(self, interaction: discord.Interaction, action: str, user: discord.Member = None):
        if not getattr(interaction.channel, "is_nsfw", lambda: False)():
            embed = discord.Embed(title="Canal no permitido", description="Este comando solo puede usarse en canales marcados como NSFW.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        await interaction.response.defer()
        
        img_url = await self.fetch_nsfw_image(action.lower())
        if not img_url:
            await interaction.followup.send("No se pudo obtener la imagen NSFW. Intenta con otra acción.", ephemeral=True)
            return
            
        phrase = random.choice(self.phrases[action])
        description = f"{interaction.user.mention} {phrase} a {user.mention if user and user != interaction.user else 'sí mismo'}"
            
        embed = discord.Embed(description=description, color=discord.Color.dark_red())
        embed.set_image(url=img_url)
        embed.set_footer(text="Contenido solo para mayores de edad. | Por BeethovenBot", icon_url=interaction.user.avatar.url)
        embed.add_field(name="¡Hot tip!", value=random.choice([
            "¡Cuidado con el fuego!",
            "¡Intenso, bro!",
            "¡NSFW vibes total!"
        ]), inline=False)
        
        msg = await interaction.followup.send(embed=embed)
        await msg.add_reaction(random.choice(self.reactions))

async def setup(bot: commands.Bot):
    await bot.add_cog(AnimeNSFW(bot))
    print("Cog AnimeNSFW cargado")