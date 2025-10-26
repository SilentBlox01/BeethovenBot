# cogs/anime_trivia.py
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
import aiohttp
import random

class TriviaView(View):
    def __init__(self, user, options, answer):
        super().__init__(timeout=30)
        self.user = user
        self.answer = answer
        for opt in options:
            self.add_item(TriviaButton(opt, answer, user))

class TriviaButton(Button):
    def __init__(self, label, answer, user):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.answer = answer
        self.user = user

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ Esta trivia no es para ti", ephemeral=True)
            return
            
        correct = self.label == self.answer
        color = discord.Color.green() if correct else discord.Color.red()
        msg = "✅ ¡Correcto!" if correct else f"❌ Incorrecto! La respuesta era: {self.answer}"
        
        embed = discord.Embed(title="🎯 Trivia", description=msg, color=color)
        await interaction.response.edit_message(embed=embed, view=None)

class AnimeTrivia(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def get_trivia_question(self):
        """Obtiene una pregunta de trivia de la API"""
        url = "https://opentdb.com/api.php?amount=1&type=multiple"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data["results"]:
                            q = data["results"][0]
                            question = self.clean_text(q["question"])
                            options = [self.clean_text(opt) for opt in q["incorrect_answers"]]
                            options.append(self.clean_text(q["correct_answer"]))
                            random.shuffle(options)
                            answer = self.clean_text(q["correct_answer"])
                            return question, options, answer
        except Exception as e:
            print(f"Error en trivia: {e}")
            
        return None, [], ""

    def clean_text(self, text: str) -> str:
        """Limpia texto HTML de la trivia"""
        replacements = {
            "&quot;": '"', "&#039;": "'", "&amp;": "&", 
            "&lt;": "<", "&gt;": ">", "&nbsp;": " ",
            "&eacute;": "é", "&ouml;": "ö"
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    @app_commands.command(name="trivia", description="Responde preguntas de trivia")
    async def trivia(self, interaction: discord.Interaction):
        """Comando principal de trivia"""
        await interaction.response.defer()
        
        question, options, answer = await self.get_trivia_question()
        
        if not question:
            await interaction.followup.send("❌ No se pudo obtener una pregunta de trivia. Intenta más tarde.", ephemeral=True)
            return
            
        view = TriviaView(interaction.user, options, answer)
        embed = discord.Embed(
            title="🎯 Trivia",
            description=question,
            color=discord.Color.blue()
        )
        embed.set_footer(text="Tienes 30 segundos para responder")
        
        await interaction.followup.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(AnimeTrivia(bot))
    print("✅ Cog AnimeTrivia cargado")