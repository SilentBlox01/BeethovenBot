# cogs/stats_logger.py
import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
from pathlib import Path
import logging

DB_PATH = Path("stats.db")  # <-- SE CREA AQUÍ

class StatsLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = None

    async def cog_load(self):
        # Crear DB si no existe
        self.db = await aiosqlite.connect(DB_PATH)
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await self.db.commit()
        print(f"Stats DB creada en: {DB_PATH.resolve()}")

        # Inyectar en todos los cogs
        self.inject_into_cogs()

    async def cog_unload(self):
        if self.db:
            await self.db.close()

    def inject_into_cogs(self):
        # Lista de todos tus cogs de acciones
        cog_names = [
            "AnimeSFWLove", "AnimeSFWFUN", "AnimeSFWAngry",
            "AnimeSFWSad", "AnimeSFWAction", "AnimeSFWExtreme"
        ]
        
        for name in cog_names:
            cog = self.bot.get_cog(name)
            if cog and hasattr(cog, 'send'):
                original = cog.send
                async def wrapped(self, interaction, action, user):
                    await self.log(action, interaction.user.id, interaction.user.name)
                    return await original(self, interaction, action, user)
                cog.send = wrapped.__get__(cog)

    async def log(self, action: str, user_id: int, username: str):
        try:
            async with self.db.execute(
                "INSERT INTO interactions (action, user_id, username) VALUES (?, ?, ?)",
                (action, user_id, username)
            ):
                await self.db.commit()
        except Exception as e:
            logging.error(f"Error en stats: {e}")

    # Comando opcional para ver si funciona
    @app_commands.command(name="stats_check")
    async def check(self, interaction: discord.Interaction):
        count = 0
        async with self.db.execute("SELECT COUNT(*) FROM interactions") as cursor:
            count = (await cursor.fetchone())[0]
        await interaction.response.send_message(
            f"Stats activas! Registros: **{count}** | DB: `{DB_PATH.name}`",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(StatsLogger(bot))