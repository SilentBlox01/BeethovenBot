import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Select
from utils.rate_limiter import safe_interaction_response
import logging

logger = logging.getLogger("BeethovenBot")

# ---------------- Config ----------------
MAIN_CATEGORIES = {
    "🛡️ Moderación": ["ban", "kick", "unban", "purge", "blacklistadd", "blacklistremove", "say"],
    "🔧 Utilidad": ["userinfo", "serverinfo", "avatar", "morse", "qr", "afk", "unafk", "calculate_tutorial",
                    "sobremi", "invite", "soporte", "dev", "calc", "reportbug"],
    "🎮 Diversión": ["hello", "bola8", "rps", "guess", "dado", "moneda", "curse", "fortune"],
    "🎌 Anime": ["aniinfo", "aniquote", "anicharacter", "anisearch", "mangainfo", "mangasearch",
                 "manhwa", "manhwasearch", "mangaquote"],
    "🐾 Mascotas": ["pet", "adoptar", "info", "feed", "play", "sleep", "train", "battle", "missions",
                    "shop", "logros", "view", "buy", "use", "pet_tutorial"],
}

INTERACTION_CMDS = [
    "interact"  # El comando único que junta todas las interacciones
]

# ---------------- Cog ----------------
class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("HelpCog inicializado")

    @app_commands.command(name="help", description="Muestra todos los comandos del bot categorizados.")
    async def help_command(self, interaction: discord.Interaction):
        """Muestra la lista de comandos organizados por categorías dinámicamente"""
        if await self.bot.emergency_check():
            await safe_interaction_response(interaction, content="🔴 Bot en modo de recuperación. Intenta más tarde.", ephemeral=True)
            return

        commands_list = [c for c in self.bot.tree.get_commands() if hasattr(c, 'description')]

        if not commands_list:
            await safe_interaction_response(interaction, content="❌ No se encontraron comandos.", ephemeral=True)
            return

        categories = self.generate_categories(commands_list)

        embed = discord.Embed(
            title="📚 Menú de ayuda - Beethoven Bot",
            description="Selecciona una categoría para explorar los comandos disponibles.",
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Usa los botones para navegar • ¡Hola! 👋")

        view = HelpMainView(commands_list, self.bot, categories)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)
        logger.info(f"Comando /help ejecutado por {interaction.user}")

    def generate_categories(self, commands_list):
        categories = {}
        # Categorías principales
        for cat_name, cmd_names in MAIN_CATEGORIES.items():
            categories[cat_name] = [cmd.name for cmd in commands_list if cmd.name in cmd_names]

        # Interacción
        categories["💝 Interacción"] = [cmd.name for cmd in commands_list if cmd.name in INTERACTION_CMDS]

        # NSFW
        categories["🔞 NSFW"] = [cmd.name for cmd in commands_list if cmd.name.startswith("nsfw_")]

        # Otros
        categorized = sum(categories.values(), [])
        categories["Otros"] = [cmd.name for cmd in commands_list if cmd.name not in categorized]

        return categories

# ---------------- Views ----------------
class HelpMainView(View):
    def __init__(self, commands_list, bot, categories):
        super().__init__(timeout=120)
        self.commands_list = commands_list
        self.bot = bot
        self.categories = categories

        for cat_name, cmds in self.categories.items():
            if cmds:  # Solo agregamos botones de categorías con comandos
                self.add_item(CategoryButton(cat_name, self.commands_list, self.bot, self.categories))

class CategoryButton(Button):
    def __init__(self, category_name, commands_list, bot, categories):
        super().__init__(label=category_name, style=discord.ButtonStyle.primary)
        self.category_name = category_name
        self.commands_list = commands_list
        self.bot = bot
        self.categories = categories

    async def callback(self, interaction: discord.Interaction):
        category_commands = [cmd for cmd in self.commands_list if cmd.name in self.categories[self.category_name]]
        category_commands = [c for c in category_commands if hasattr(c, 'description')]

        if not category_commands:
            await safe_interaction_response(interaction, content=f"❌ No hay comandos en la categoría {self.category_name}", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"{self.category_name} - Comandos",
            description="Selecciona un comando para ver más detalles.",
            color=discord.Color.blue()
        )

        if len(category_commands) <= 10:
            view = CategoryView(category_commands, self.category_name, self.bot)
        else:
            view = PaginatedCategoryView(category_commands, self.category_name, self.bot)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

class CategoryView(View):
    def __init__(self, commands, category_name, bot):
        super().__init__(timeout=120)
        self.commands = commands
        self.category_name = category_name
        self.bot = bot
        self.add_item(CommandSelect(commands, category_name, bot))
        self.add_item(BackToMainButton(bot))

class PaginatedCategoryView(View):
    def __init__(self, commands, category_name, bot):
        super().__init__(timeout=120)
        self.commands = commands
        self.category_name = category_name
        self.bot = bot
        self.page = 0
        self.commands_per_page = 10
        self.update_view()

    def update_view(self):
        self.clear_items()
        start_idx = self.page * self.commands_per_page
        end_idx = start_idx + self.commands_per_page
        page_commands = self.commands[start_idx:end_idx]

        if page_commands:
            self.add_item(CommandSelect(page_commands, self.category_name, self.bot))

        total_pages = (len(self.commands) - 1) // self.commands_per_page + 1
        if self.page > 0:
            self.add_item(PrevPageButton())
        if self.page < total_pages - 1:
            self.add_item(NextPageButton())

        self.add_item(BackToMainButton(self.bot))

    async def update_interaction(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"{self.category_name} - Comandos (Página {self.page + 1})",
            description="Selecciona un comando para ver más detalles.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=self, ephemeral=False)

class CommandSelect(Select):
    def __init__(self, commands, category_name, bot):
        self.commands = [c for c in commands if hasattr(c, 'description')]
        self.category_name = category_name
        self.bot = bot

        options = [
            discord.SelectOption(
                label=f"/{cmd.name}",
                description=(cmd.description[:95] + "..." if cmd.description and len(cmd.description) > 95 else (cmd.description or "Sin descripción")),
                value=cmd.name
            )
            for cmd in sorted(self.commands, key=lambda c: c.name)
        ]

        super().__init__(
            placeholder=f"Selecciona un comando de {category_name}",
            options=options,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        cmd_name = self.values[0]
        cmd = next((c for c in self.commands if c.name == cmd_name), None)

        if not cmd:
            await safe_interaction_response(interaction, content="❌ Comando no encontrado", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"🛠️ /{cmd.name}",
            description=cmd.description or "Sin descripción disponible.",
            color=discord.Color.gold()
        )

        if hasattr(cmd, '_params'):
            params_text = ""
            for param_name, param in cmd._params.items():
                param_desc = getattr(param, 'description', 'Sin descripción')
                required = "✅" if param.required else "❌"
                params_text += f"`{param_name}`: {param_desc} ({required})\n"
            if params_text:
                embed.add_field(name="📋 Parámetros", value=params_text, inline=False)

        view = BackToCategoryView(self.commands, self.category_name, self.bot)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

# ---------------- Bot Buttons ----------------
class BackToMainButton(Button):
    def __init__(self, bot):
        super().__init__(label="↩️ Volver al menú principal", style=discord.ButtonStyle.secondary)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        commands_list = [c for c in self.bot.tree.get_commands() if hasattr(c, 'description')]
        categories = HelpCog(self.bot).generate_categories(commands_list)

        embed = discord.Embed(
            title="📚 Menú de ayuda - Beethoven Bot",
            description="Selecciona una categoría para explorar los comandos disponibles.",
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Usa los botones para navegar • ¡Hola! 👋")

        view = HelpMainView(commands_list, self.bot, categories)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

class BackToCategoryView(View):
    def __init__(self, commands, category_name, bot):
        super().__init__(timeout=120)
        self.commands = commands
        self.category_name = category_name
        self.bot = bot
        self.add_item(BackToCategoryButton(commands, category_name, bot))

class BackToCategoryButton(Button):
    def __init__(self, commands, category_name, bot):
        super().__init__(label="↩️ Volver a la categoría", style=discord.ButtonStyle.secondary)
        self.commands = commands
        self.category_name = category_name
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        if len(self.commands) <= 10:
            view = CategoryView(self.commands, self.category_name, self.bot)
        else:
            view = PaginatedCategoryView(self.commands, self.category_name, self.bot)

        embed = discord.Embed(
            title=f"{self.category_name} - Comandos",
            description="Selecciona un comando para ver más detalles.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

class PrevPageButton(Button):
    def __init__(self):
        super().__init__(label="⏪ Anterior", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        view.page -= 1
        view.update_view()
        await view.update_interaction(interaction)

class NextPageButton(Button):
    def __init__(self):
        super().__init__(label="Siguiente ⏩", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        view.page += 1
        view.update_view()
        await view.update_interaction(interaction)

# ---------------- Setup ----------------
async def setup(bot):
    try:
        await bot.add_cog(HelpCog(bot))
        logger.info("HelpCog registrado")
    except Exception as e:
        logger.error(f"Error cargando HelpCog: {str(e)}")
        raise e
