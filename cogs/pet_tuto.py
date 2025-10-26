import discord
from discord.ext import commands
from discord import app_commands, ButtonStyle
from discord.ui import Button, View
import logging
from utils.rate_limiter import safe_interaction_response
from utils.database import db

logger = logging.getLogger("BeethovenBot")

class PetTutorialCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("PetTutorialCog inicializado")

    class PetTutorialView(View):
        def __init__(self):
            super().__init__(timeout=300)
            self.page = 0

            self.pages = [
                # Página 0 - Introducción
                discord.Embed(
                    title="🐾 **Sistema de Mascotas - Tutorial Completo**",
                    description=(
                        "¡Bienvenido al **sistema de mascotas coleccionables**! 🎮\n\n"
                        "🌟 **Características principales:**\n"
                        "• **35+ mascotas** con diferentes rarezas\n"
                        "• **Sistema elemental** con ventajas estratégicas\n"
                        "• **35+ logros** para desbloquear\n"
                        "• **Batallas PvP** contra otros jugadores\n"
                        "• **Misiones diarias** y recompensas\n"
                        "• **Evolución** y habilidades especiales\n\n"
                        "¡Conviértete en el mejor entrenador! 🏆"
                    ),
                    color=0x00FF00
                ).set_thumbnail(url="https://cdn.discordapp.com/emojis/1107536327844663326.png"),

                # Página 1 - Comandos Básicos
                discord.Embed(
                    title="🛠️ **Comandos Básicos**",
                    description=(
                        "**Comando principal:** `/pet [subcomando]`\n\n"
                        "🔹 **`/pet adoptar`** - Adopta una mascota aleatoria\n"
                        "🔹 **`/pet info`** - Ve tu colección completa\n"
                        "🔹 **`/pet feed`** - Alimenta a tu mascota activa\n"
                        "🔹 **`/pet play`** - Juega para aumentar felicidad\n"
                        "🔹 **`/pet train`** - Entrena para ganar XP\n"
                        "🔹 **`/pet sleep`** - Descansa para recuperar energía\n\n"
                        "💡 **Consejo:** Usa estos comandos regularmente para mantener a tus mascotas felices y saludables."
                    ),
                    color=0x3498db
                ),

                # Página 2 - Sistema de Rarezas
                discord.Embed(
                    title="🌈 **Sistema de Rarezas**",
                    description=(
                        "Las mascotas vienen en **7 niveles de rareza**:\n\n"
                        "🔵 **Común** (40%) - Stats básicos\n"
                        "🟢 **Poco Común** (25%) - +10% stats\n"
                        "🔵 **Raro** (15%) - +20% stats\n"
                        "🟣 **Épico** (10%) - +30% stats\n"
                        "🟠 **Legendario** (5%) - +50% stats\n"
                        "🔴 **Mítico** (4%) - +80% stats\n"
                        "⚫ **Universal** (1%) - +100% stats\n\n"
                        "🎵 **Beethoven** - ¡La mascota más rara (0.1%)!"
                    ),
                    color=0x9b59b6
                ).add_field(
                    name="🎯 Probabilidades",
                    value="Las probabilidades se acumulan, ¡sigue intentando!",
                    inline=False
                ),

                # Página 3 - Sistema Elemental
                discord.Embed(
                    title="⚡ **Sistema Elemental**",
                    description=(
                        "Cada mascota tiene un **elemento** que afecta las batallas:\n\n"
                        "🔥 **Fuego** → 💧 Agua → 🌿 Planta → 🔥\n"
                        "⚡ **Eléctrico** → 🌍 Tierra → 💧 Agua\n"
                        "❄️ **Hielo** → 🔥 Fuego → 🌿 Planta\n"
                        "🔮 **Psíquico** → 🌑 Oscuridad → ✨ Luz\n"
                        "🐲 **Dragón** - Elemento especial\n\n"
                        "💥 **Ventaja elemental:** 1.5x daño\n"
                        "🛡️ **Desventaja elemental:** 0.5x daño"
                    ),
                    color=0xe74c3c
                ),

                # Página 4 - Batallas PvP
                discord.Embed(
                    title="⚔️ **Sistema de Batallas**",
                    description=(
                        "**Comando:** `/pet battle @usuario`\n\n"
                        "🎯 **Mecánicas de batalla:**\n"
                        "• Turnos alternados entre mascotas\n"
                        "• Daño basado en nivel y felicidad\n"
                        "• Habilidades especiales por clase\n"
                        "• Ventajas elementales estratégicas\n"
                        "• Combos de habilidades\n\n"
                        "🏆 **Recompensas por ganar:**\n"
                        "• +50 XP para la mascota ganadora\n"
                        "• Posibilidad de items raros\n"
                        "• Progreso en logros de batallas"
                    ),
                    color=0xe67e22
                ),

                # Página 5 - Habilidades y Niveles
                discord.Embed(
                    title="✨ **Habilidades y Evolución**",
                    description=(
                        "**Sistema de niveles:**\n"
                        "• Gana XP alimentando, jugando y entrenando\n"
                        "• Cada nivel aumenta stats máximos\n"
                        "• Desbloquea habilidades especiales\n\n"
                        "🎯 **Habilidades por nivel:**\n"
                        "• **Nivel 2-5:** Habilidades básicas\n"
                        "• **Nivel 10:** Habilidad elemental básica\n"
                        "• **Nivel 20:** Habilidad elemental avanzada\n"
                        "• **Nivel 25+:** Habilidades únicas\n\n"
                        "💫 **Ejemplo de habilidades:**\n"
                        "`Llamarada Infernal`, `Tsunami Devastador`"
                    ),
                    color=0xf1c40f
                ),

                # Página 6 - Misiones y Logros
                discord.Embed(
                    title="🎯 **Misiones y Logros**",
                    description=(
                        "**Misiones Diarias:**\n"
                        "• Alimentar mascotas\n"
                        "• Jugar con mascotas\n"
                        "• Ganar batallas\n"
                        "• Entrenar mascotas\n\n"
                        "**Misiones Semanales:**\n"
                        "• Completar misiones diarias\n"
                        "• Mantener felicidad alta\n"
                        "• Adoptar mascotas raras\n\n"
                        "🏆 **Sistema de Logros (35+):**\n"
                        "• Colección (obtener mascotas)\n"
                        "• Niveles (subir de nivel)\n"
                        "• Batallas (ganar combates)\n"
                        "• Elementos (dominar elementos)\n"
                        "• Especiales (logros únicos)"
                    ),
                    color=0x2ecc71
                ),

                # Página 7 - Tienda y Economía
                discord.Embed(
                    title="🏪 **Tienda y Economía**",
                    description=(
                        "**Comando:** `/pet shop [acción]`\n\n"
                        "🛍️ **Items disponibles:**\n"
                        "• **Poción de Energía** (50 monedas) - +50 energía\n"
                        "• **Juguete Mágico** (30 monedas) - +20 felicidad\n"
                        "• **Medicina Especial** (40 monedas) - +50 salud\n"
                        "• **Impulso de XP** (100 monedas) - +100 XP\n"
                        "• **Caja Misteriosa** (200 monedas) - Mascota rara\n"
                        "• **Piedra Elemental** (300 monedas) - Cambia elemento\n\n"
                        "💰 **Gana monedas:**\n"
                        "• Completando misiones\n"
                        "• Ganando batallas\n"
                        "• Desbloqueando logros"
                    ),
                    color=0x95a5a6
                ),

                # Página 8 - Estrategias Avanzadas
                discord.Embed(
                    title="🎮 **Estrategias Avanzadas**",
                    description=(
                        "🔥 **Consejos para expertos:**\n\n"
                        "1. **Equilibra tu equipo** - Ten mascotas de diferentes elementos\n"
                        "2. **Aprovecha ventajas** - Usa elementos contra oponentes débiles\n"
                        "3. **Maneja la energía** - No dejes que tus mascotas se agoten\n"
                        "4. **Combina habilidades** - Algunas habilidades funcionan mejor juntas\n"
                        "5. **Farmea items** - Usa la tienda estratégicamente\n\n"
                        "🏅 **Meta del juego:**\n"
                        "• Obtener todas las mascotas\n"
                        "• Desbloquear todos los logros\n"
                        "• Tener un equipo nivel máximo\n"
                        "• Dominar todos los elementos\n"
                        "• ¡Conseguir a Beethoven!"
                    ),
                    color=0xe91e63
                ),

                # Página 9 - Comandos Avanzados
                discord.Embed(
                    title="🔧 **Comandos Avanzados**",
                    description=(
                        "**Comandos adicionales para gestión:**\n\n"
                        "📊 **`/pet logros`** - Ve tu progreso y estadísticas\n"
                        "🎁 **`/pet shop view`** - Explora la tienda\n"
                        "🛒 **`/pet shop buy [item] [mascota]`** - Compra items\n"
                        "⚗️ **`/pet shop use [item] [mascota]`** - Usa items\n"
                        "📋 **`/pet missions`** - Revisa tus misiones\n\n"
                        "🔄 **Comandos de interacción:**\n"
                        "• **feed** - Cada 3 minutos\n"
                        "• **play** - Cada 4 minutos\n"
                        "• **train** - Cada 10 minutos\n"
                        "• **battle** - Cada 15 minutos\n\n"
                        "¡Planifica tu estrategia!"
                    ),
                    color=0x607d8b
                ),

                # Página 10 - Ejemplos Prácticos
                discord.Embed(
                    title="🚀 **Ejemplos Prácticos**",
                    description=(
                        "**Flujo de juego típico:**\n\n"
                        "1. **`/pet adoptar`** - Consigue tu primera mascota\n"
                        "2. **`/pet feed`** - Mantenla alimentada\n"
                        "3. **`/pet play`** - Aumenta su felicidad\n"
                        "4. **`/pet train`** - Sube de nivel\n"
                        "5. **`/pet battle @amigo`** - Practica combates\n"
                        "6. **`/pet missions`** - Completa misiones\n"
                        "7. **`/pet shop buy`** - Mejora con items\n\n"
                        "🎯 **Meta diaria recomendada:**\n"
                        "• Alimentar 2-3 veces\n"
                        "• Jugar 2-3 veces\n"
                        "• Entrenar 1-2 veces\n"
                        "• 1-2 batallas\n"
                        "• Revisar misiones\n\n"
                        "¡Diviértete construyendo tu equipo perfecto! 🎉"
                    ),
                    color=0x00bcd4
                )
            ]

            # Agregar botones de navegación
            self.add_item(PetTutorialCog.PrevButton(self))
            self.add_item(PetTutorialCog.NextButton(self))
            self.add_item(PetTutorialCog.QuickNavButton("🏠 Inicio", 0, ButtonStyle.primary))
            self.add_item(PetTutorialCog.QuickNavButton("⚔️ Batallas", 4, ButtonStyle.danger))
            self.add_item(PetTutorialCog.QuickNavButton("🏆 Logros", 6, ButtonStyle.success))

    class PrevButton(Button):
        def __init__(self, tutorial_view):
            super().__init__(label="⏪ Anterior", style=ButtonStyle.secondary, row=1)
            self.view_ref = tutorial_view

        async def callback(self, interaction: discord.Interaction):
            self.view_ref.page = max(0, self.view_ref.page - 1)
            embed = self.view_ref.pages[self.view_ref.page]
            embed.set_footer(text=f"Página {self.view_ref.page + 1}/{len(self.view_ref.pages)} • Usa los botones para navegar • Timeout: 5 minutos")
            await interaction.response.edit_message(embed=embed, view=self.view_ref)

    class NextButton(Button):
        def __init__(self, tutorial_view):
            super().__init__(label="Siguiente ⏩", style=ButtonStyle.secondary, row=1)
            self.view_ref = tutorial_view

        async def callback(self, interaction: discord.Interaction):
            self.view_ref.page = min(len(self.view_ref.pages) - 1, self.view_ref.page + 1)
            embed = self.view_ref.pages[self.view_ref.page]
            embed.set_footer(text=f"Página {self.view_ref.page + 1}/{len(self.view_ref.pages)} • Usa los botones para navegar • Timeout: 5 minutos")
            await interaction.response.edit_message(embed=embed, view=self.view_ref)

    class QuickNavButton(Button):
        def __init__(self, label, page, style):
            super().__init__(label=label, style=style, row=1)
            self.target_page = page

        async def callback(self, interaction: discord.Interaction):
            view = self.view
            view.page = self.target_page
            embed = view.pages[view.page]
            embed.set_footer(text=f"Página {view.page + 1}/{len(view.pages)} • Usa los botones para navegar • Timeout: 5 minutos")
            await interaction.response.edit_message(embed=embed, view=view)

    @app_commands.command(name="pet_tutorial", description="Tutorial completo del sistema de mascotas")
    async def pet_tutorial(self, interaction: discord.Interaction):
        """Muestra un tutorial interactivo del sistema de mascotas"""
        logger.debug(f"Usuario {interaction.user.id} ejecutó /pet_tutorial")
        if await self.bot.emergency_check():
            await safe_interaction_response(interaction, "🔴 Bot en modo de recuperación. Intenta más tarde.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=False)
        view = self.PetTutorialView()
        embed = view.pages[0]
        embed.set_footer(text=f"Página 1/{len(view.pages)} • Usa los botones para navegar • Timeout: 5 minutos")
        await safe_interaction_response(interaction, embed=embed, view=view, ephemeral=False)

    @app_commands.command(name="pet_help", description="Guía rápida de comandos de mascotas")
    async def pet_help(self, interaction: discord.Interaction):
        """Muestra una guía rápida de comandos"""
        logger.debug(f"Usuario {interaction.user.id} ejecutó /pet_help")
        embed = discord.Embed(
            title="🐾 **Guía Rápida - Comandos de Mascotas**",
            description="Resumen de todos los comandos disponibles:\n",
            color=0x5865F2
        )
        embed.add_field(
            name="🛠️ **Comandos Básicos**",
            value=(
                "`/pet adoptar` - Adoptar mascota\n"
                "`/pet info` - Ver colección\n"
                "`/pet feed` - Alimentar\n"
                "`/pet play` - Jugar\n"
                "`/pet train` - Entrenar\n"
                "`/pet sleep` - Dormir"
            ),
            inline=True
        )
        embed.add_field(
            name="⚔️ **Comandos de Batalla**",
            value=(
                "`/pet battle @usuario` - Batalla PvP\n"
                "`/pet missions` - Ver misiones\n"
                "`/pet logros` - Progreso"
            ),
            inline=True
        )
        embed.add_field(
            name="🏪 **Comandos de Tienda**",
            value=(
                "`/pet shop view` - Ver tienda\n"
                "`/pet shop buy` - Comprar items\n"
                "`/pet shop use` - Usar items"
            ),
            inline=True
        )
        embed.add_field(
            name="📚 **Tutoriales**",
            value=(
                "`/pet_tutorial` - Tutorial completo\n"
                "`/pet_help` - Esta guía rápida"
            ),
            inline=False
        )
        embed.set_footer(text="Usa /pet_tutorial para el tutorial completo con imágenes y ejemplos")
        await safe_interaction_response(interaction, embed=embed, ephemeral=False)

async def setup(bot):
    await bot.add_cog(PetTutorialCog(bot))