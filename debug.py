import discord
from discord import app_commands
import os
from dotenv import load_dotenv

load_dotenv()

class DebugBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.command_count = {}

    async def on_ready(self):
        print(f'✅ {self.user} conectado UNA VEZ')
        
        @self.tree.command(name="test")
        async def test(interaction: discord.Interaction):
            # Contar ejecuciones
            self.command_count[interaction.id] = self.command_count.get(interaction.id, 0) + 1
            count = self.command_count[interaction.id]
            
            print(f"🔧 Comando /test ejecutado {count} veces para {interaction.id}")
            await interaction.response.send_message(f"✅ Test ejecutado (vez #{count})")

        await self.tree.sync()
        print("🔧 Comando /test registrado")

bot = DebugBot()
bot.run(os.getenv("TOKEN"))