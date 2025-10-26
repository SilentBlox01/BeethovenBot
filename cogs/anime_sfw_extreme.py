# cogs/anime_sfw_extreme.py
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio
import random

class AnimeSFWExtreme(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # The command group will be registered on the bot.tree in setup()
        self.actions = {
            "Kill": "kill", "Stab": "stab", "Shoot": "shoot", "Triggered": "triggered", "Die": "die",
            "Facepalm": "facepalm", "Cringe": "cringe", "Panic": "panic", "Nope": "nope"
        }
        self.phrases = {
            "Kill": ["¡K.O. total, fin del juego!", "¡Muere, villano!", "¡Fin, game over!", "¡Kill shot!", "¡Eliminado!"],
            "Stab": ["¡Puñalada traicionera!", "¡Stab stab, directo al corazón!", "¡Atravesado como en anime!", "¡Puñalada épica!", "¡Stab de traición!"],
            "Shoot": ["¡Bang! ¡Tiro certero!", "¡Pum pum, directo!", "¡Shoot shoot!", "¡Disparo de precisión!", "¡Bang bang!"],
            "Triggered": ["¡Activado, modo furia!", "¡Trigger total, cuidado!", "¡Explosión inminente!", "¡Triggered como loco!", "¡No me toques!"],
            "Die": ["¡Muerto, R.I.P.!", "¡Fin del camino!", "¡Die die die!", "¡Adiós mundo cruel!", "¡Game over!"],
            "Facepalm": ["¡Facepalm épico, no puede ser!", "¡Qué error, facepalm!", "¡No lo creo, facepalm!", "¡Facepalm de vergüenza!", "¡Qué tontería!"],
            "Cringe": ["¡Cringe total, eww!", "¡Qué vergüenza ajena!", "¡Cringe level 1000!", "¡No puedo mirar!", "¡Cringe máximo!"],
            "Panic": ["¡Pánico total, ayuda!", "¡Terror, auxilio!", "¡Panic mode on!", "¡Corriendo en círculos!", "¡Ayuda, socorro!"],
            "Nope": ["¡Nope nope nope!", "¡No way, José!", "¡Rechazado total!", "¡Nope, fuera!", "¡Ni loco, nope!"]
        }
        self.reactions = ["SKULL", "DAGGER", "GUN", "SCREAM", "NO_ENTRY"]
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8))

    async def cog_unload(self):
        await self.session.close()

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
        e = discord.Embed(description=f"{i.user.mention} {phrase} a {t}!", color=0x8b0000)
        e.set_image(url=url)
        e.add_field(name="¡Extremo!", value=random.choice([
            "¡Wow, intenso!",
            "¡Cuidado, bro!",
            "¡Esto es serio!"
        ]), inline=False)
        e.set_footer(text=f"Acción: {a} | Por BeethovenBot", icon_url=i.user.avatar.url)
        msg = await i.followup.send(embed=e)
        await msg.add_reaction(random.choice(self.reactions))

    extreme_group = app_commands.Group(name="extreme", description="Comandos de acciones extremas")
    
    @commands.cooldown(1, 5, commands.BucketType.user)
    @extreme_group.command(name="emote")
    @app_commands.describe(
        action="Elige la acción extrema que quieres realizar",
        user="El usuario al que quieres dirigir la acción (opcional)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Matar ☠️", value="Kill"),
        app_commands.Choice(name="Apuñalar 🔪", value="Stab"),
        app_commands.Choice(name="Disparar 🔫", value="Shoot"),
        app_commands.Choice(name="Enfurecer 😡", value="Triggered"),
        app_commands.Choice(name="Morir 💀", value="Die"),
        app_commands.Choice(name="Facepalm 🤦", value="Facepalm"),
        app_commands.Choice(name="Cringe 😫", value="Cringe"),
        app_commands.Choice(name="Pánico 😱", value="Panic"),
        app_commands.Choice(name="Nope ❌", value="Nope")
    ])
    async def extreme_emote(self, interaction: discord.Interaction, action: str, user: discord.Member = None):
        """¡Realiza acciones extremas con reacciones anime!"""
        await self.send(interaction, action, user)

async def setup(bot):
    cog = AnimeSFWExtreme(bot)
    await bot.add_cog(cog)
    try:
        bot.tree.add_command(cog.extreme_group)
    except Exception:
        pass