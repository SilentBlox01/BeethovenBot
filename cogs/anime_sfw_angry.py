# cogs/anime_sfw_angry.py
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio
import random

class AnimeSFWAngry(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # The command group will be registered on the bot.tree in setup()
        self.actions = {
            "Angry": "angry", "Slap": "slap", "Punch": "punch", "Kick": "kick", "Bonk": "bonk",
            "Baka": "baka", "Bully": "bully", "Smug": "smug", "Tease": "tease", "Disgust": "disgust"
        }
        self.phrases = {
            "Angry": ["¡Me enojo como volcán!", "¡Grrrr, modo bestia on!", "¡Furia total, cuidado!", "¡Angry face activated!", "¡No me hables, estoy enojado!"],
            "Slap": ["¡Cachetada épica como en anime!", "¡Toma eso, bobo!", "¡Slap en 4K!", "¡Cachetada de realidad!", "¡Slap con estilo!"],
            "Punch": ["¡Puñetazo fuerte como Goku!", "¡Bam! ¡Directo!", "¡Punch en la cara!", "¡Golpe de justicia!", "¡Puñetazo de amor!"],
            "Kick": ["¡Patada voladora nivel dios!", "¡Kick out, fuera!", "¡Patada de karate!", "¡Kick en el ego!", "¡Fuera de mi vista!"],
            "Bonk": ["¡Bonk en la cabeza, tonto!", "¡Toma bonk, perdedor!", "¡Bonk bonk, a dormir!", "¡Bonk de corrección!", "¡Bonk con amor!"],
            "Baka": ["¡Baka! ¡Idiota total!", "¡Eres un baka supremo!", "¡Baka baka baka!", "¡Tonto del año!", "¡Baka mode on!"],
            "Bully": ["¡Molestando como pro!", "¡Bully time, ja ja!", "¡Te molesto porque puedo!", "¡Bully de barrio!", "¡Molestando con cariño!"],
            "Smug": ["¡Cara de superior, ja!", "¡Smug face level 100!", "¡Yo soy mejor, punto!", "¡Smug como villano!", "¡Cara de 'te gané'!"],
            "Tease": ["¡Te provoco, ¿qué?", "¡Je je je, te piqué!", "¡Tease tease, ja ja!", "¡Provocación máxima!", "¡Te hago enojar!"],
            "Disgust": ["¡Qué asco, eww!", "¡Disgustado total!", "¡Eww, qué feo!", "¡Cara de asco pro!", "¡No puedo ni mirarlo!"]
        }
    self.reactions = ["ANGRY", "FIST", "RAGE", "BOOM", "SWEAT"]
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
            await i.followup.send(f"No hay imagen de **{a}**...", ephemeral=True)
            return
        t = u.mention if u and u != i.user else "a sí mismo"
        phrase = random.choice(self.phrases[a])
        e = discord.Embed(description=f"{i.user.mention} {phrase} a {t}!", color=0xff4500)
        e.set_image(url=url)
        e.add_field(name="¡Consejo enojado!", value=random.choice([
            "¡Respira profundo, calma!",
            "¡No te enojes, no vale la pena!",
            "¡Paz interior, bro!"
        ]), inline=False)
        e.set_footer(text=f"Acción: {a} | Por BeethovenBot", icon_url=i.user.avatar.url)
        msg = await i.followup.send(embed=e)
        await msg.add_reaction(random.choice(self.reactions))

    angry_group = app_commands.Group(name="angry", description="Comandos de enojo y confrontación")
    
    @commands.cooldown(1, 5, commands.BucketType.user)
    @angry_group.command(name="emote")
    @app_commands.describe(
        emotion="Elige la emoción o acción de enojo que quieres expresar",
        user="El usuario al que quieres dirigir la acción (opcional)"
    )
    @app_commands.choices(emotion=[
        app_commands.Choice(name="Enfadarse 😠", value="Angry"),
        app_commands.Choice(name="Cachetada 👋", value="Slap"),
        app_commands.Choice(name="Puñetazo 👊", value="Punch"),
        app_commands.Choice(name="Patada 🦶", value="Kick"),
        app_commands.Choice(name="Bonk 🔨", value="Bonk"),
        app_commands.Choice(name="Baka! 😤", value="Baka"),
        app_commands.Choice(name="Molestar 😈", value="Bully"),
        app_commands.Choice(name="Presumir 😏", value="Smug"),
        app_commands.Choice(name="Provocar 😝", value="Tease"),
        app_commands.Choice(name="Asco 🤢", value="Disgust")
    ])
    async def angry_emote(self, interaction: discord.Interaction, emotion: str, user: discord.Member = None):
        """¡Expresa tu enojo o molestia con reacciones anime!"""
        await self.send(interaction, emotion, user)

async def setup(bot):
    cog = AnimeSFWAngry(bot)
    await bot.add_cog(cog)
    try:
        bot.tree.add_command(cog.angry_group)
    except Exception:
        pass