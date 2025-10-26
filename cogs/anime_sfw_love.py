# cogs/anime_sfw_love.py
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio
import random

class AnimeSFWLove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # The command group will be registered on the bot.tree in setup()
        self.actions = {
            "Hug": "hug", "Cuddle": "cuddle", "Glomp": "hug", "Nuzzle": "cuddle", "Hold": "hug",
            "Kiss": "kiss", "Love": "love", "Blush": "blush", "Peck": "kiss", "Wink": "wink"
        }
        self.phrases = {
            "Hug": ["¡Abrazo calentito como sopa en invierno!", "¡Un abrazo que derrite glaciares!", "¡Abrazo de oso... con amor!", "¡Hug incoming, prepárate!", "¡Abrazo grupal? Nah, solo para ti!"],
            "Cuddle": ["¡Acurrucados como gatos en caja!", "¡Momento tierno, no pestañees!", "¡Calor humano al máximo!", "¡Cuddle time, zero drama!", "¡Abrazos infinitos incoming!"],
            "Glomp": ["¡Abrazo sorpresa como ninja!", "¡Ataque de cariño level 9000!", "¡Glomp épico, nadie escapa!", "¡Salto abrazo incoming!", "¡Glomp: el superpoder del amor!"],
            "Nuzzle": ["¡Rojitos de cariño como tomate!", "¡Nuzzle dulce como caramelo!", "¡Frotadita amorosa pro!", "¡Nuzzle alert: modo cute on!", "¡Cara a cara con amor loco!"],
            "Hold": ["¡Mano en mano, corazón con corazón!", "¡Sosteniendo con amor eterno!", "¡No te suelto ni con pegamento!", "¡Hold tight, adventure ahead!", "¡Agárrate fuerte, bro!"],
            "Kiss": ["¡Beso apasionado como en novela!", "¡Chu chu train coming!", "¡Beso volador a máxima velocidad!", "¡Kiss kiss bang bang!", "¡Beso robado... con permiso!"],
            "Love": ["¡Amor eterno como pizza infinita!", "¡Corazones volando por todos lados!", "¡Te amo más que a mi WiFi!", "¡Love bomb explosion!", "¡Amor loco mode activated!"],
            "Blush": ["¡Sonrojo total, modo tomate on!", "¡Qué vergüenza, pero cute!", "¡Rojo como luz de stop!", "¡Blush alert: hide face!", "¡Sonrojo épico incoming!"],
            "Peck": ["¡Piquito rápido como flash!", "¡Beso ligero, impacto heavy!", "¡Chu rápido, corazón lento!", "¡Peck peck revolution!", "¡Beso ninja style!"],
            "Wink": ["¡Guiño pícaro como pirata!", "¡Ojo guiñado, corazón conquistado!", "¡Wink coqueto level 100!", "¡Guiño mágico incoming!", "¡Yo sé algo que tú no... wink!"]
        }
        self.reactions = ["HEART", "HEART_HANDS", "KISS", "HEART_EYES", "SPARKLING_HEART"]
        # create session lazily in cog_load to avoid creating aiohttp sessions outside an event loop
        self.session = None

    async def cog_unload(self):
        if self.session:
            await self.session.close()

    async def cog_load(self):
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8))

    async def fetch(self, tag):
        for url in [f"https://api.waifu.pics/sfw/{tag}", f"https://api.waifu.im/sfw/{tag}?many=false"]:
            try:
                async with self.session.get(url) as r:
                    if r.status == 200:
                        d = await r.json()
                        return d.get("url") or (d.get("images") or [{}])[0].get("url")
            except: pass
        return None

    async def send(self, i, a, u):
        await i.response.defer()
        url = await self.fetch(self.actions[a])
        if not url:
            await i.followup.send(f"No hay imagen de **{a}**... Intenta de nuevo!", ephemeral=True)
            return
        t = u.mention if u and u != i.user else "a sí mismo"
        phrase = random.choice(self.phrases[a])
        e = discord.Embed(description=f"{i.user.mention} {phrase} a {t}!", color=0xff69b4)
        e.set_image(url=url)
        e.add_field(name="¡Tip romántico!", value=random.choice([
            "El amor es como WiFi: invisible pero conecta corazones",
            "Un abrazo cura más que mil palabras",
            "¡Besa como si fuera el último día!"
        ]), inline=False)
        e.set_footer(text=f"Acción: {a} | Por BeethovenBot", icon_url=i.user.avatar.url)
        msg = await i.followup.send(embed=e)
        await msg.add_reaction(random.choice(self.reactions))

    love_group = app_commands.Group(name="love", description="Comandos de amor y afecto")
    
    @commands.cooldown(1, 5, commands.BucketType.user)
    @love_group.command(name="emote")
    @app_commands.describe(
        emotion="Elige la expresión de amor o afecto que quieres mostrar",
        user="El usuario al que quieres dirigir la acción (opcional)"
    )
    @app_commands.choices(emotion=[
        app_commands.Choice(name="Abrazar 🤗", value="Hug"),
        app_commands.Choice(name="Acurrucarse 🥰", value="Cuddle"),
        app_commands.Choice(name="Abrazo sorpresa 💝", value="Glomp"),
        app_commands.Choice(name="Acariciar 💕", value="Nuzzle"),
        app_commands.Choice(name="Sostener 🤝", value="Hold"),
        app_commands.Choice(name="Besar 💋", value="Kiss"),
        app_commands.Choice(name="Amar ❤️", value="Love"),
        app_commands.Choice(name="Sonrojar 😊", value="Blush"),
        app_commands.Choice(name="Piquito 😘", value="Peck"),
        app_commands.Choice(name="Guiñar 😉", value="Wink")
    ])
    async def love_emote(self, interaction: discord.Interaction, emotion: str, user: discord.Member = None):
        """¡Expresa tu amor y afecto con reacciones anime!"""
        await self.send(interaction, emotion, user)

async def setup(bot):
    cog = AnimeSFWLove(bot)
    await bot.add_cog(cog)
    try:
        bot.tree.add_command(cog.love_group)
    except Exception:
        pass