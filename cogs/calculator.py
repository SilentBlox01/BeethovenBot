# cogs/calculator.py
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
from utils.rate_limiter import safe_interaction_response
import sympy
from sympy import sin, cos, tan, log, ln, sqrt, pi, E, Pow
from utils.database import db
import logging

logger = logging.getLogger(__name__)

class Calculator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    class AdvancedCalcView(View):
        def __init__(self):
            super().__init__(timeout=300)
            self.expression = ""

            buttons = [
                ["7","8","9","/","sin"],
                ["4","5","6","*","cos"],
                ["1","2","3","-","tan"],
                ["0",".","(","+",")"],
                ["C","^","√","ln","="]
            ]

            total = 0
            for row_idx, row in enumerate(buttons):
                for btn in row:
                    if total < 25:
                        self.add_item(Calculator.AdvancedCalcButton(btn, self, row=row_idx))
                        total += 1

    class AdvancedCalcButton(Button):
        def __init__(self, label, view: 'Calculator.AdvancedCalcView', row: int = 0):
            super().__init__(label=label, style=discord.ButtonStyle.secondary, row=row)
            self.view_ref = view

        async def callback(self, interaction: discord.Interaction):
            expr = self.view_ref.expression

            if self.label == "C":
                self.view_ref.expression = ""
            elif self.label == "DEL":
                self.view_ref.expression = expr[:-1]
            elif self.label == "=":
                try:
                    allowed_symbols = {
                        "sin": sin, "cos": cos, "tan": tan,
                        "log": log, "ln": ln, "√": sqrt,
                        "pi": pi, "e": E, "^": Pow
                    }
                    safe_expr = expr.replace("√", "sqrt")
                    safe_expr = safe_expr.replace("^", "**")
                    result = sympy.sympify(safe_expr, locals=allowed_symbols).evalf()
                    self.view_ref.expression = str(result)
                except Exception as e:
                    logger.error(f"Error calculating expression '{expr}': {e}")
                    self.view_ref.expression = "Error"
            else:
                self.view_ref.expression += self.label

            embed = discord.Embed(
                title="🧮 Calculadora Científica",
                description=f"```{self.view_ref.expression or '0'}```",
                color=discord.Color.blurple()
            )
            
            # Verificar si la interacción necesita edit o response
            try:
                if interaction.response.is_done():
                    await interaction.edit_original_response(embed=embed, view=self.view_ref)
                else:
                    await interaction.response.send_message(embed=embed, view=self.view_ref, ephemeral=False)
            except Exception as e:
                logger.error(f"Error updating calculator display: {e}")
                # Fallback
                try:
                    await interaction.followup.send(embed=embed, view=self.view_ref, ephemeral=True)
                except:
                    pass

    @app_commands.command(name="calc", description="Calculadora científica")
    async def calc(self, interaction: discord.Interaction):
        try:
            if await self.bot.emergency_check():
                await safe_interaction_response(
                    interaction, 
                    content="🔴 Bot en modo de recuperación. Intenta más tarde.", 
                    ephemeral=True
                )
                return
            
            view = self.AdvancedCalcView()
            embed = discord.Embed(
                title="🧮 Calculadora Científica",
                description="```0```",
                color=discord.Color.blurple()
            )
            embed.set_footer(text="Usa los botones para realizar cálculos matemáticos")
            
            await safe_interaction_response(
                interaction, 
                embed=embed, 
                view=view, 
                ephemeral=False
            )
            
        except Exception as e:
            logger.error(f"Error in calc command: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ Ocurrió un error al iniciar la calculadora.", 
                        ephemeral=True
                    )
            except:
                pass

    class TutorialView(View):
        def __init__(self):
            super().__init__(timeout=180)
            self.page = 0

            self.pages = [
                discord.Embed(
                    title="📘 Tutorial de /calc",
                    description=(
                        "Bienvenido al **tutorial del comando `/calc`**.\n\n"
                        "Este comando te permite realizar **operaciones matemáticas** directamente desde Discord.\n"
                        "Usa expresiones simples o funciones avanzadas como si estuvieras en una calculadora científica 🧮."
                    ),
                    color=discord.Color.blurple()
                ),
                discord.Embed(
                    title="➕ Operaciones básicas",
                    description=(
                        "**Suma (+)** → `2 + 3` = **5**\n"
                        "**Resta (-)** → `8 - 4` = **4**\n"
                        "**Multiplicación (*)** → `6 * 7` = **42**\n"
                        "**División (/)** → `9 / 3` = **3.0**\n"
                        "**Potencia (^)** → `2 ** 3` = **8**\n\n"
                        "💡 Consejo: Usa paréntesis para agrupar operaciones, ejemplo:\n"
                        "`(3 + 2) * 5` = **25**"
                    ),
                    color=discord.Color.green()
                ),
                discord.Embed(
                    title="🔢 Funciones avanzadas",
                    description=(
                        "Puedes usar **funciones matemáticas** del módulo `math`:\n\n"
                        "📏 `sqrt(x)` → Raíz cuadrada\n"
                        "🌀 `sin(x)`, `cos(x)`, `tan(x)` → Trigonometría (en radianes)\n"
                        "📈 `ln(x)` → Logaritmo natural (base *e*)\n"
                        "🎯 `^(x, y)` → Potencia de `x` elevado a `y`\n"
                        "Ejemplo: `sin(3.1416/2)` = **1.0**"
                    ),
                    color=discord.Color.orange()
                ).set_footer(
                    text="Nota: Siempre usa los parentesis '()' al usar funciones como sin o cos para obtener un resultado y evitar errores."
                ),
                discord.Embed(
                    title="💡 Ejemplos prácticos",
                    description=(
                        "Aquí tienes algunos ejemplos listos para usar:\n\n"
                        "🔹 `/calculate expression: 2+2`\n"
                        "→ **Resultado:** 4\n\n"
                        "🔹 `/calculate expression: sqrt(16)`\n"
                        "→ **Resultado:** 4\n\n"
                        "🔹 `/calculate expression: sin(3.1416/2)`\n"
                        "→ **Resultado:** 1.0\n\n"
                        "🚀 ¡Y listo! Ahora puedes usar `/calculate` para resolver cualquier expresión matemática."
                    ),
                    color=discord.Color.purple()
                )
            ]

            self.add_item(Calculator.PrevButton(self))
            self.add_item(Calculator.NextButton(self))

    class PrevButton(Button):
        def __init__(self, tutorial_view):
            super().__init__(label="⏪ Anterior", style=discord.ButtonStyle.secondary)
            self.view_ref = tutorial_view

        async def callback(self, interaction: discord.Interaction):
            self.view_ref.page = (self.view_ref.page - 1) % len(self.view_ref.pages)
            embed = self.view_ref.pages[self.view_ref.page]
            
            try:
                if interaction.response.is_done():
                    await interaction.edit_original_response(embed=embed, view=self.view_ref)
                else:
                    await interaction.response.send_message(embed=embed, view=self.view_ref, ephemeral=False)
            except Exception as e:
                logger.error(f"Error in PrevButton callback: {e}")
                try:
                    await interaction.followup.send(embed=embed, view=self.view_ref, ephemeral=True)
                except:
                    pass

    class NextButton(Button):
        def __init__(self, tutorial_view):
            super().__init__(label="Siguiente ⏩", style=discord.ButtonStyle.secondary)
            self.view_ref = tutorial_view

        async def callback(self, interaction: discord.Interaction):
            self.view_ref.page = (self.view_ref.page + 1) % len(self.view_ref.pages)
            embed = self.view_ref.pages[self.view_ref.page]
            
            try:
                if interaction.response.is_done():
                    await interaction.edit_original_response(embed=embed, view=self.view_ref)
                else:
                    await interaction.response.send_message(embed=embed, view=self.view_ref, ephemeral=False)
            except Exception as e:
                logger.error(f"Error in NextButton callback: {e}")
                try:
                    await interaction.followup.send(embed=embed, view=self.view_ref, ephemeral=True)
                except:
                    pass

    @app_commands.command(name="calculate_tutorial", description="Muestra un tutorial sobre cómo usar el comando /calc.")
    async def calculate_tutorial(self, interaction: discord.Interaction):
        try:
            if await self.bot.emergency_check():
                await safe_interaction_response(
                    interaction, 
                    content="🔴 Bot en modo de recuperación. Intenta más tarde.", 
                    ephemeral=True
                )
                return
            
            view = self.TutorialView()
            
            # Verificar que las páginas existen
            if not view.pages or not view.pages[0]:
                logger.error("Tutorial pages are empty or None")
                await safe_interaction_response(
                    interaction, 
                    content="❌ Error: No se pudieron cargar las páginas del tutorial.", 
                    ephemeral=True
                )
                return
            
            await safe_interaction_response(
                interaction, 
                embed=view.pages[0], 
                view=view, 
                ephemeral=False
            )
            
        except Exception as e:
            logger.error(f"Error in calculate_tutorial command: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ Ocurrió un error al cargar el tutorial.", 
                        ephemeral=True
                    )
            except:
                pass

async def setup(bot):
    await bot.add_cog(Calculator(bot))