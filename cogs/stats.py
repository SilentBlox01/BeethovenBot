# cogs/stats.py
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from aiohttp import web
import json
import os
from pathlib import Path

STATS_FILE = Path("stats.json")
WEB_FOLDER = Path("web")

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stats = self.load_stats()
        self.web_app = web.Application()
        # Ensure the web folder exists so aiohttp.web.static won't raise on init
        try:
            if not WEB_FOLDER.exists():
                WEB_FOLDER.mkdir(parents=True, exist_ok=True)
                # create a minimal index.html so the dashboard has something to serve
                index_file = WEB_FOLDER / "index.html"
                if not index_file.exists():
                    index_file.write_text("<html><body><h1>BeethovenBot Stats Dashboard</h1><p>No data yet.</p></body></html>", encoding='utf-8')
        except Exception:
            # If filesystem is not writable for some reason, continue and only expose /stats.json
            pass

        self.web_app.add_routes([web.static('/', WEB_FOLDER), web.get('/stats.json', self.serve_stats)])
        self.runner = None

    def load_stats(self):
        if STATS_FILE.exists():
            try:
                with open(STATS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def save_stats(self):
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)

    async def serve_stats(self, request):
        return web.json_response(self.stats)

    def increment(self, action: str):
        self.stats[action] = self.stats.get(action, 0) + 1
        self.save_stats()

    async def cog_load(self):
        self.runner = web.AppRunner(self.web_app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, '0.0.0.0', 8000)
        await site.start()
        print("Dashboard web iniciado en http://localhost:8000")

    async def cog_unload(self):
        if self.runner:
            await self.runner.cleanup()

    @app_commands.command(name="stats", description="Muestra las estadísticas del bot")
    async def stats_cmd(self, interaction: discord.Interaction):
        total = sum(self.stats.values())
        top = sorted(self.stats.items(), key=lambda x: x[1], reverse=True)[:5]
        
        desc = "\n".join([f"`{action}` → **{count}** veces" for action, count in top])
        if not desc:
            desc = "Aún no hay estadísticas..."

        embed = discord.Embed(
            title="Estadísticas de Interacciones",
            description=desc,
            color=0x00ff88
        )
        embed.add_field(name="Total", value=f"**{total}** interacciones", inline=False)
        embed.add_field(name="Dashboard", value="[Abrir en navegador](http://localhost:8000)", inline=False)
        embed.set_footer(text="Actualizado en tiempo real")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="reset_stats", description="Reinicia todas las estadísticas (solo admin)")
    @app_commands.default_permissions(administrator=True)
    async def reset_stats(self, interaction: discord.Interaction):
        self.stats = {}
        self.save_stats()
        await interaction.response.send_message("Estadísticas reiniciadas!", ephemeral=True)

async def setup(bot):
    cog = Stats(bot)
    await bot.add_cog(cog)
    
    # Inyectar `increment` en todos los cogs
    cog_classes = {
        "anime_sfw_love": "AnimeSFWLove",
        "anime_sfw_fun": "AnimeSFWFun",
        "anime_sfw_angry": "AnimeSFWAngry",
        "anime_sfw_sad": "AnimeSFWSad",
        "anime_sfw_action": "AnimeSFWAction",
        "anime_sfw_extreme": "AnimeSFWExtreme"
    }
    
    for cog_name, class_name in cog_classes.items():
        c = bot.get_cog(class_name)
        if c and hasattr(c, 'send'):
            original_send = c.send
            # bind original_send to the wrapper to avoid late-binding closure issues
            def make_wrapped(orig):
                async def wrapped(self, i, a, u):
                    cog.increment(a)
                    return await orig(self, i, a, u)
                return wrapped

            c.send = make_wrapped(original_send).__get__(c)