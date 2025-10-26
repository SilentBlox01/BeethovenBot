# cogs/anime_sfw_action.py
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio
import random

class AnimeSFWAction(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # The command group will be registered on the bot.tree in setup()
        self.actions = {
            "Run": "run", "Chase": "chase", "Poke": "poke", "Highfive": "highfive", "Thumbsup": "thumbsup",
            "Feed": "feed", "Nom": "nom", "Sip": "sip", "Lick": "lick", "Bite": "bite"
        }
        self.phrases = {
            "Run": ["¡Corre como Naruto!", "¡Huida épica, modo flash!", "¡Run run run!", "¡Corre por tu vida!", "¡Velocidad máxima!"],
            "Chase": ["¡Persiguiendo como en anime!", "¡Atrapado, ja ja!", "¡Chase time, no escapes!", "¡Corriendo detrás tuyo!", "¡Persecución nivel pro!"],
            "Poke": ["¡Poke poke, ¿estás ahí?", "¡Toquecito juguetón!", "¡Poke en el hombro!", "¡Poke divertido!", "¡Poke poke poke!"],
            "Highfive": ["¡Choca esos cinco, bro!", "¡Highfive épico!", "¡Bien hecho, equipo!", "¡Choca la mano!", "¡Highfive de victoria!"],
            "Thumbsup": ["¡Pulgar arriba, aprobadísimo!", "¡Aprobado con honores!", "¡Bien hecho, crack!", "¡Thumbs up!", "¡Perfecto!"],
            "Feed": ["¡Hora de comer, yum!", "¡Alimentando con amor!", "¡Toma, come!", "¡Feed time!", "¡Comida rica!"],
            "Nom": ["¡Nom nom nom, delicioso!", "¡Mordisco feliz!", "¡Nom nom, rico!", "¡Comiendo todo!", "¡Nom nom time!"],
            "Sip": ["¡Sorbo elegante, sip!", "¡Bebiendo como rey!", "¡Sip sip, refrescante!", "¡Sorbo de victoria!", "¡Bebiendo lento!"],
            "Lick": ["¡Lame lame, ja ja!", "¡Lengüetazo juguetón!", "¡Lick lick!", "¡Lamiendo todo!", "¡Lick de helado!"],
            "Bite": ["¡Mordisco fuerte, ouch!", "¡Bite bite, cuidado!", "¡Muerde muerde!", "¡Bite de amor!", "¡Mordisco juguetón!"]
        }
    self.reactions = ["RUNNER", "HAND_SHAKE", "THUMBS_UP", "FORK_KNIFE", "YUM"]
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
        e = discord.Embed(description=f"{i.user.mention} {phrase} a {t}!", color=0xffa500)
        e.set_image(url=url)
        e.add_field(name="¡Acción!", value=random.choice([
            "¡Full speed ahead!",
            "¡Go go go!",
            "¡Acción total!"
        ]), inline=False)
        e.set_footer(text=f"Acción: {a} | Por BeethovenBot", icon_url=i.user.avatar.url)
        msg = await i.followup.send(embed=e)
        await msg.add_reaction(random.choice(self.reactions))

    action_group = app_commands.Group(name="action", description="Comandos de acciones físicas")
    
    @commands.cooldown(1, 5, commands.BucketType.user)
    @action_group.command(name="emote")
    @app_commands.describe(
        action="Elige la acción física que quieres realizar",
        user="El usuario al que quieres dirigir la acción (opcional)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Correr 🏃", value="Run"),
        app_commands.Choice(name="Perseguir 🏃‍♂️", value="Chase"),
        app_commands.Choice(name="Tocar 👆", value="Poke"),
        app_commands.Choice(name="Chocar cinco ✋", value="Highfive"),
        app_commands.Choice(name="Pulgar arriba 👍", value="Thumbsup"),
        app_commands.Choice(name="Alimentar 🍽️", value="Feed"),
        app_commands.Choice(name="Comer 🍴", value="Nom"),
        app_commands.Choice(name="Beber 🥤", value="Sip"),
        app_commands.Choice(name="Lamer 👅", value="Lick"),
        app_commands.Choice(name="Morder 😬", value="Bite")
    ])
    async def action_emote(self, interaction: discord.Interaction, action: str, user: discord.Member = None):
        """¡Realiza acciones físicas con reacciones anime!"""
        await self.send(interaction, action, user)

async def setup(bot):
    cog = AnimeSFWAction(bot)
    await bot.add_cog(cog)
    try:
        bot.tree.add_command(cog.action_group)
    except Exception:
        pass