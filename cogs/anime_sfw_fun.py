# cogs/anime_sfw_fun.py
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio
import random

class AnimeSFWFUN(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # The command group will be registered on the bot.tree in setup()
        self.actions = {
            "Dance": "dance", "Dab": "dab", "Cheer": "cheer", "Tickle": "tickle", "Laugh": "laugh",
            "Pat": "pat", "Wave": "wave", "Hi": "wave", "Smile": "happy", "Yes": "happy"
        }
        self.phrases = {
            "Dance": ["¡Baila como si nadie viera... pero todos miran!", "¡Movimientos de pro gamer!", "¡Al ritmo del corazón!", "¡Dance floor on fire!", "¡Bailando como en TikTok!"],
            "Dab": ["¡Dab master 3000!", "¡Dab legendario, épico!", "¡Dab time, dab life!", "¡Dab en la cara del enemigo!", "¡Dab como si fuera 2016!"],
            "Cheer": ["¡Animo total, equipo!", "¡Yay! ¡Vamos!", "¡Cheer up, buttercup!", "¡Pompones volando!", "¡Ánimo, campeón!"],
            "Tickle": ["¡Cosquillas infinitas, ja ja ja!", "¡No pares, no puedo más!", "¡Tickle attack level 99!", "¡Risa garantizada!", "¡Cosquillas ninja!"],
            "Laugh": ["¡Risa contagiosa como virus!", "¡Ja ja ja ja ja!", "¡Me muero de risa!", "¡Laugh out loud!", "¡Risa de villano!"],
            "Pat": ["¡Pat pat, buen chico!", "¡Bien hecho, campeón!", "¡Pat en la cabeza!", "¡Pat pat, no llores!", "¡Pat de orgullo!"],
            "Wave": ["¡Hola hola, adiós adiós!", "¡Saludo animado como en anime!", "¡Wave wave!", "¡Adiós con la mano!", "¡Saludo de amigo!"],
            "Hi": ["¡Hola amigo del alma!", "¡Hey there, cutie!", "¡Hola mundo!", "¡Hi five!", "¡Hola, ¿qué tal?"],
            "Smile": ["¡Sonrisa radiante como sol!", "¡Cheese! ¡Foto!", "¡Sonríe, es gratis!", "¡Smile mode on!", "¡Sonrisa de oreja a oreja!"],
            "Yes": ["¡Sí señor, afirmativo!", "¡Claro que sí!", "¡Yes yes yes!", "¡Aprobado!", "¡Sí, capitán!"]
        }
        self.reactions = ["PARTY", "LAUGHING", "DANCER", "WAVE", "SMILE"]
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
        e = discord.Embed(description=f"{i.user.mention} {phrase} a {t}!", color=0x00ff00)
        e.set_image(url=url)
        e.add_field(name="¡Tip divertido!", value=random.choice([
            "¡La risa es la mejor medicina!",
            "¡Baila como si nadie viera!",
            "¡Alegría total, siempre!"
        ]), inline=False)
        e.set_footer(text=f"Acción: {a} | Por BeethovenBot", icon_url=i.user.avatar.url)
        msg = await i.followup.send(embed=e)
        await msg.add_reaction(random.choice(self.reactions))

    fun_group = app_commands.Group(name="fun", description="Comandos de diversión y alegría")
    
    @commands.cooldown(1, 5, commands.BucketType.user)
    @fun_group.command(name="emote")
    @app_commands.describe(
        action="Elige la acción divertida que quieres realizar",
        user="El usuario al que quieres dirigir la acción (opcional)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Bailar 💃", value="Dance"),
        app_commands.Choice(name="Dab 🕺", value="Dab"),
        app_commands.Choice(name="Animar 📣", value="Cheer"),
        app_commands.Choice(name="Hacer cosquillas 😆", value="Tickle"),
        app_commands.Choice(name="Reír 😂", value="Laugh"),
        app_commands.Choice(name="Palmadita 👋", value="Pat"),
        app_commands.Choice(name="Saludar 👋", value="Wave"),
        app_commands.Choice(name="Hola 🤗", value="Hi"),
        app_commands.Choice(name="Sonreír 😊", value="Smile"),
        app_commands.Choice(name="¡Sí! 👍", value="Yes")
    ])
    async def fun_emote(self, interaction: discord.Interaction, action: str, user: discord.Member = None):
        """¡Expresa tu diversión y alegría con reacciones anime!"""
        await self.send(interaction, action, user)

async def setup(bot):
    cog = AnimeSFWFUN(bot)
    await bot.add_cog(cog)
    try:
        bot.tree.add_command(cog.fun_group)
    except Exception:
        pass