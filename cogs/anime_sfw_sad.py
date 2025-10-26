# cogs/anime_sfw_sad.py
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio
import random

class AnimeSFWSad(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # The command group will be registered on the bot.tree in setup()
        self.actions = {
            "Cry": "cry", "Sad": "cry", "Pout": "pout", "Bored": "bored", "Sleepy": "sleep",
            "Think": "think", "Shrug": "shrug", "Stare": "stare", "Nervous": "nervous"
        }
        self.phrases = {
            "Cry": ["¡Lágrimas caen como lluvia torrencial!", "¡Buuuu, qué tristeza!", "¡Llorando ríos!", "¡Sniff sniff, no puedo más!", "¡Lágrimas de cocodrilo!"],
            "Sad": ["¡Qué tristeza infinita!", "¡Sniff sniff, todo mal!", "¡Tristeza nivel dios!", "¡Modo emo on!", "¡Día gris, corazón gris!"],
            "Pout": ["¡Puchero épico, hmpf!", "¡Cara de enojo cute!", "¡Pout pout, no me mires!", "¡Labios fruncidos!", "¡Puchero de campeón!"],
            "Bored": ["¡Aburrimiento máximo, zzz!", "¡Nada que hacer, todo aburrido!", "¡Bored to death!", "¡Zzz... despiértame!", "¡Aburrido como lunes!"],
            "Sleepy": ["¡Sueñito, zzz!", "¡Bostezo épico!", "¡A dormir ya!", "¡Ojos cerrados, modo sueño!", "¡Sleepy time, buenas noches!"],
            "Think": ["¡Pensando profundo como filósofo!", "¡Hmm... interesante!", "¡Reflexionando vida!", "¡Think think!", "¡Cerebro en llamas!"],
            "Shrug": ["¡No sé, meh!", "¡Shrug, qué más da!", "¡Ni idea, bro!", "¡Shrug life!", "¡No me importa!"],
            "Stare": ["¡Mirada fija como láser!", "¡Observando todo!", "¡Stare intensivo!", "¡Mirada de 1000 yardas!", "¡Te miro fijo!"],
            "Nervous": ["¡Nervios de acero... temblando!", "¡Temblando como gelatina!", "¡Ansiedad level 99!", "¡Nervous breakdown!", "¡Calma, respira!"]
        }
        self.reactions = ["CRYING", "SAD", "SLEEPING", "THINKING", "SWEAT_NERVOUS"]
        # create session lazily in cog_load to avoid creating aiohttp sessions outside an event loop
        self.session = None

    async def cog_unload(self):
        if self.session:
            await self.session.close()

    async def cog_load(self):
        # called when the cog is loaded into a running bot; create session here
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
        e = discord.Embed(description=f"{i.user.mention} {phrase} a {t}!", color=0x4682b4)
        e.set_image(url=url)
        e.add_field(name="¡Ánimo!", value=random.choice([
            "¡Todo pasará, bro!",
            "¡Anímate, mañana es otro día!",
            "¡Un abrazo virtual!"
        ]), inline=False)
        e.set_footer(text=f"Acción: {a} | Por BeethovenBot", icon_url=i.user.avatar.url)
        msg = await i.followup.send(embed=e)
        await msg.add_reaction(random.choice(self.reactions))

    sad_group = app_commands.Group(name="sad", description="Comandos de emociones tristes y estados de ánimo")
    
    @commands.cooldown(1, 5, commands.BucketType.user)
    @sad_group.command(name="emote")
    @app_commands.describe(
        emotion="Elige la emoción o estado de ánimo que quieres expresar",
        user="El usuario al que quieres dirigir la acción (opcional)"
    )
    @app_commands.choices(emotion=[
        app_commands.Choice(name="Llorar 😢", value="Cry"),
        app_commands.Choice(name="Triste 😔", value="Sad"),
        app_commands.Choice(name="Puchero 😤", value="Pout"),
        app_commands.Choice(name="Aburrido 😑", value="Bored"),
        app_commands.Choice(name="Somnoliento 😴", value="Sleepy"),
        app_commands.Choice(name="Pensativo 🤔", value="Think"),
        app_commands.Choice(name="Encogerse de hombros 🤷", value="Shrug"),
        app_commands.Choice(name="Mirada fija 👀", value="Stare"),
        app_commands.Choice(name="Nervioso 😰", value="Nervous")
    ])
    async def sad_emote(self, interaction: discord.Interaction, emotion: str, user: discord.Member = None):
        """Expresa tus emociones tristes o estados de ánimo con reacciones anime!"""
        await self.send(interaction, emotion, user)

async def setup(bot):
    cog = AnimeSFWSad(bot)
    await bot.add_cog(cog)
    # register the group on the global tree to keep commands global
    try:
        bot.tree.add_command(cog.sad_group)
    except Exception:
        # if it's already registered or something else fails, ignore to avoid crashing load
        pass