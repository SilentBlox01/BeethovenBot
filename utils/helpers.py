# helpers.py
import discord
import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Any
import math
import logging

# Configuración de logging
logger = logging.getLogger(__name__)

# Si necesitas importar constantes específicas
try:
    from utils.database import logger as db_logger
except ImportError:
    db_logger = logger

try:
    from utils.constants import PET_CLASSES, PET_ELEMENTS
except ImportError:
    # Definiciones básicas como fallback
    PET_CLASSES = {}
    PET_ELEMENTS = {}

class PetHelpers:
    """Helpers para el sistema de mascotas"""
    
    @staticmethod
    def calculate_level_stats(pet_data: Dict) -> Dict:
        """Calcula las estadísticas basadas en el nivel de la mascota"""
        nivel = pet_data.get("nivel", 1)
        clase = pet_data.get("clase", "Común")
        stat_multiplier = PET_CLASSES.get(clase, {}).get("stat_multiplier", 1.0)
        
        # Estadísticas base por nivel
        base_stats = {
            "max_salud": 100 + (nivel * 10),
            "max_energía": 80 + (nivel * 8),
            "ataque": 10 + (nivel * 2),
            "defensa": 5 + (nivel * 1.5)
        }
        
        # Aplicar multiplicador de clase
        for stat in base_stats:
            base_stats[stat] = int(base_stats[stat] * stat_multiplier)
            
        return base_stats
    
    @staticmethod
    def format_time(seconds: int) -> str:
        """Formatea segundos a un string legible"""
        if seconds < 60:
            return f"{seconds} segundos"
        elif seconds < 3600:
            return f"{seconds // 60} minutos"
        else:
            return f"{seconds // 3600} horas"
    
    @staticmethod
    def create_progress_bar(current: int, maximum: int, length: int = 10) -> str:
        """Crea una barra de progreso visual"""
        if maximum == 0:
            return "█" * length
            
        progress = min(current / maximum, 1.0)
        filled = int(progress * length)
        bar = "█" * filled + "░" * (length - filled)
        return f"{bar} {current}/{maximum}"
    
    @staticmethod
    def calculate_xp_for_next_level(current_level: int, pet_class: str) -> int:
        """Calcula el XP necesario para el siguiente nivel"""
        base_xp = PET_CLASSES.get(pet_class, {}).get("xp_needed", 100)
        return base_xp * current_level
    
    @staticmethod
    def get_rarity_color(rarity: str) -> int:
        """Obtiene el color correspondiente a la rareza"""
        colors = {
            "Común": 0x808080,
            "Poco Común": 0x00FF00, 
            "Raro": 0x0000FF,
            "Épico": 0x800080,
            "Legendario": 0xFFD700,
            "Mítico": 0x00FFFF,
            "Universal": 0xFF00FF
        }
        return colors.get(rarity, 0x000000)
    
    @staticmethod
    def calculate_battle_damage(attacker: Dict, defender: Dict, skill: Optional[Dict] = None) -> Tuple[int, str]:
        """Calcula el daño en batalla considerando elementos y habilidades"""
        # Daño base basado en nivel y clase
        base_damage = attacker.get("nivel", 1) * 5
        
        # Multiplicador por clase
        class_multiplier = PET_CLASSES.get(attacker.get("clase", "Común"), {}).get("stat_multiplier", 1.0)
        base_damage *= class_multiplier
        
        # Ventaja elemental
        element_advantage = 1.0
        attacker_element = attacker.get("elemento")
        defender_element = defender.get("elemento")
        
        if attacker_element and defender_element:
            attacker_data = PET_ELEMENTS.get(attacker_element, {})
            if attacker_data.get("strength") == defender_element:
                element_advantage = 1.5
            elif attacker_data.get("weakness") == defender_element:
                element_advantage = 0.5
        
        # Bonus de habilidad
        skill_multiplier = 1.0
        if skill and skill.get("battle_effect"):
            effect = skill["battle_effect"]
            if effect["type"] == "damage_boost":
                skill_multiplier = effect["value"]
        
        # Cálculo final
        total_damage = int(base_damage * element_advantage * skill_multiplier)
        
        # Mensaje de ventaja
        advantage_msg = ""
        if element_advantage > 1.0:
            advantage_msg = " ¡Ventaja elemental! 🔥"
        elif element_advantage < 1.0:
            advantage_msg = " ¡Desventaja elemental! 💧"
            
        return total_damage, advantage_msg

class EventHelpers:
    """Helpers específicos para events.py"""
    
    @staticmethod
    async def handle_guild_xp(guild_data: Dict, xp_gained: int, channel: discord.TextChannel) -> Dict:
        """Maneja la ganancia de XP del gremio y subida de nivel"""
        guild_data["xp"] = guild_data.get("xp", 0) + xp_gained
        level_up = False
        
        # Verificar si sube de nivel
        xp_required = guild_data.get("level", 1) * 1000
        if guild_data["xp"] >= xp_required:
            guild_data["level"] += 1
            guild_data["xp"] = 0
            level_up = True
            
            # Enviar mensaje de nivel up
            if channel:
                try:
                    await channel.send(
                        f"🎉 ¡El gremio **{guild_data['name']}** ha subido al nivel {guild_data['level']}!"
                    )
                except Exception as e:
                    logger.error(f"Error enviando mensaje de nivel up: {e}")
        
        return guild_data, level_up
    
    @staticmethod
    async def handle_user_activity(user_id: str, activity_type: str, user_data: Dict) -> Dict:
        """Maneja la actividad del usuario y actualiza misiones"""
        # Aquí puedes añadir lógica para tracking de actividad
        # Por ejemplo, contar mensajes, comandos usados, etc.
        
        if activity_type == "message":
            user_data["message_count"] = user_data.get("message_count", 0) + 1
        elif activity_type == "command":
            user_data["command_count"] = user_data.get("command_count", 0) + 1
        
        return user_data
    
    @staticmethod
    def generate_welcome_message(member: discord.Member) -> discord.Embed:
        """Genera un mensaje de bienvenida personalizado"""
        embed = discord.Embed(
            title=f"👋 ¡Bienvenido {member.display_name}!",
            description="Gracias por unirte a nuestro servidor.",
            color=0x00FF00,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🎮 Comandos útiles",
            value="• `/pet` - Sistema de mascotas\n• `/help` - Ayuda del bot",
            inline=False
        )
        
        embed.add_field(
            name="📝 Información",
            value=f"• Eres el miembro #{member.guild.member_count}\n• Cuenta creada: {member.created_at.strftime('%d/%m/%Y')}",
            inline=False
        )
        
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text="¡Diviértete en el servidor!")
        
        return embed
    
    @staticmethod
    async def check_afk_status(user_id: int, bot) -> Optional[str]:
        """Verifica si un usuario está AFK"""
        try:
            from utils.database import get_afk_user
            return await get_afk_user(user_id)
        except ImportError:
            return None

class ModerationHelpers:
    """Helpers específicos para moderation.py"""
    
    @staticmethod
    def create_moderation_embed(action: str, member: discord.Member, reason: str, moderator: discord.Member) -> discord.Embed:
        """Crea un embed consistente para acciones de moderación"""
        action_config = {
            "ban": {"title": "🔨 Usuario Baneado", "color": 0xe74c3c},
            "kick": {"title": "👢 Usuario Expulsado", "color": 0xf39c12},
            "mute": {"title": "🔇 Usuario Silenciado", "color": 0x95a5a6},
            "warn": {"title": "⚠️ Usuario Advertido", "color": 0xf1c40f},
            "purge": {"title": "🧹 Mensajes Eliminados", "color": 0x2ecc71}
        }
        
        config = action_config.get(action, {"title": f"🛡️ Acción de Moderación", "color": 0x3498db})
        
        embed = discord.Embed(
            title=config["title"],
            color=config["color"],
            timestamp=datetime.now()
        )
        
        embed.add_field(name="👤 Usuario", value=f"{member.mention} ({member.id})", inline=True)
        embed.add_field(name="🛡️ Moderador", value=moderator.mention, inline=True)
        embed.add_field(name="📝 Razón", value=reason, inline=False)
        
        if action == "purge":
            embed.description = f"Se eliminaron **{reason}** mensajes del canal"
            embed.remove_field(2)  # Remove reason field for purge
        
        embed.set_footer(text="Sistema de moderación")
        
        return embed
    
    @staticmethod
    def create_blacklist_embed(action: str, user_id: str, username: str, success: bool) -> discord.Embed:
        """Crea embeds para acciones de lista negra"""
        if action == "add":
            if success:
                embed = discord.Embed(
                    title="🚫 Usuario Añadido a Lista Negra",
                    description="El usuario ha sido añadido a la lista negra global",
                    color=0xe74c3c
                )
            else:
                embed = discord.Embed(
                    title="⚠️ Usuario Ya en Lista Negra",
                    description="El usuario ya se encontraba en la lista negra",
                    color=0xf39c12
                )
        elif action == "remove":
            if success:
                embed = discord.Embed(
                    title="✅ Usuario Removido de Lista Negra",
                    description="El usuario ha sido removido de la lista negra global",
                    color=0x2ecc71
                )
            else:
                embed = discord.Embed(
                    title="⚠️ Usuario No Encontrado",
                    description="El usuario no se encontró en la lista negra",
                    color=0x95a5a6
                )
        
        embed.add_field(name="🆔 ID de Usuario", value=f"`{user_id}`", inline=True)
        embed.add_field(name="👤 Nombre", value=username, inline=True)
        
        return embed
    
    @staticmethod
    def validate_user_id(user_id: str, interaction: discord.Interaction, bot) -> Tuple[bool, Optional[int], str]:
        """Valida un ID de usuario para acciones de moderación"""
        try:
            user_id_int = int(user_id)
            
            # Validaciones de seguridad
            if user_id_int == bot.user.id:
                return False, None, "No puedes realizar esta acción sobre el bot."
                
            if user_id_int == interaction.user.id:
                return False, None, "No puedes realizar esta acción sobre ti mismo."
            
            return True, user_id_int, "Válido"
            
        except ValueError:
            return False, None, "Por favor, introduce un ID de usuario válido (solo números)."
    
    @staticmethod
    async def get_user_info(member: discord.Member, bot) -> discord.Embed:
        """Obtiene información detallada de un usuario"""
        try:
            from utils.database import is_blacklisted
            
            is_blacklisted_user = await is_blacklisted(member.id)
            
            embed = discord.Embed(
                title=f"👤 Información de {member.display_name}",
                color=0x00f549,
                timestamp=datetime.now()
            )
            
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            
            # Información básica
            embed.add_field(name="🆔 ID", value=f"`{member.id}`", inline=True)
            embed.add_field(name="📅 Cuenta creada", value=member.created_at.strftime("%d/%m/%Y"), inline=True)
            embed.add_field(name="🔰 Estado", value="🚫 Lista Negra" if is_blacklisted_user else "✅ Normal", inline=True)
            
            # Información del servidor
            if member.joined_at:
                embed.add_field(name="📥 Se unió", value=member.joined_at.strftime("%d/%m/%Y"), inline=True)
            
            embed.add_field(name="🎭 Roles", value=len(member.roles) - 1, inline=True)  # -1 para @everyone
            embed.add_field(name="🚦 Estado", value=str(member.status).title(), inline=True)
            
            # Permisos importantes
            permissions = []
            if member.guild_permissions.administrator:
                permissions.append("Administrador")
            if member.guild_permissions.manage_messages:
                permissions.append("Gestionar Mensajes")
            if member.guild_permissions.ban_members:
                permissions.append("Banear Miembros")
                
            if permissions:
                embed.add_field(name="🔐 Permisos", value=", ".join(permissions[:3]), inline=False)
            
            embed.set_footer(text=f"Solicitado por {interaction.user.display_name}")
            
            return embed
            
        except Exception as e:
            logger.error(f"Error obteniendo información de usuario: {e}")
            raise

class PermissionHelpers:
    """Helpers para manejo de permisos"""
    
    @staticmethod
    def check_hierarchy(interaction: discord.Interaction, target: discord.Member) -> Tuple[bool, str]:
        """Verifica la jerarquía de permisos"""
        if target == interaction.guild.owner:
            return False, "No puedes realizar esta acción sobre el dueño del servidor."
        
        if target.top_role >= interaction.user.top_role:
            return False, "No puedes realizar esta acción sobre un usuario con un rol igual o superior al tuyo."
        
        if target.top_role >= interaction.guild.me.top_role:
            return False, "No puedo realizar esta acción sobre un usuario con un rol igual o superior al mío."
        
        return True, "Jerarquía válida"
    
    @staticmethod
    def get_missing_permissions(member: discord.Member, required_permissions: List[str]) -> List[str]:
        """Obtiene los permisos faltantes de un miembro"""
        missing = []
        for perm in required_permissions:
            if not getattr(member.guild_permissions, perm, False):
                missing.append(perm)
        return missing

class LoggingHelpers:
    """Helpers para logging y auditoría"""
    
    @staticmethod
    async def log_moderation_action(
        action: str, 
        moderator: discord.Member, 
        target: Union[discord.Member, str], 
        reason: str,
        guild: discord.Guild,
        additional_info: Dict = None
    ):
        """Log de acciones de moderación"""
        log_message = (
            f"🛡️ **Acción de Moderación**\n"
            f"• **Acción:** {action}\n"
            f"• **Moderador:** {moderator} ({moderator.id})\n"
            f"• **Objetivo:** {target}\n"
            f"• **Razón:** {reason}\n"
            f"• **Servidor:** {guild.name} ({guild.id})\n"
            f"• **Hora:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        if additional_info:
            for key, value in additional_info.items():
                log_message += f"\n• **{key}:** {value}"
        
        logger.info(log_message)
    
    @staticmethod
    def format_blacklist_view(blacklisted_users: set) -> List[discord.Embed]:
        """Formatea la vista de lista negra en múltiples embeds si es necesario"""
        if not blacklisted_users:
            embed = discord.Embed(
                title="📝 Lista Negra Global",
                description="La lista negra está actualmente vacía",
                color=0x95a5a6
            )
            return [embed]
        
        embeds = []
        user_list = list(blacklisted_users)
        chunks = [user_list[i:i + 10] for i in range(0, len(user_list), 10)]
        
        for i, chunk in enumerate(chunks):
            embed = discord.Embed(
                title=f"📋 Lista Negra Global" if i == 0 else f"📋 Lista Negra (Cont.)",
                description=f"Total de usuarios: **{len(blacklisted_users)}**",
                color=0xff6b6b
            )
            
            embed.add_field(
                name=f"Usuarios {i*10 + 1}-{i*10 + len(chunk)}",
                value="\n".join([f"`{user_id}`" for user_id in chunk]),
                inline=False
            )
            
            if i == 0:
                embed.add_field(
                    name="💾 Sistema",
                    value="Base de datos en tiempo real",
                    inline=True
                )
            
            embeds.append(embed)
        
        return embeds

class ErrorHandlingHelpers:
    """Helpers para manejo de errores"""
    
    @staticmethod
    async def handle_interaction_error(interaction: discord.Interaction, error: Exception, command_name: str):
        """Maneja errores de interacción de manera consistente"""
        error_mapping = {
            app_commands.MissingPermissions: "🚫 No tienes los permisos necesarios para usar este comando.",
            app_commands.BotMissingPermissions: "🤖 No tengo los permisos necesarios para ejecutar este comando.",
            app_commands.CommandOnCooldown: "⏰ Este comando está en enfriamiento. Intenta de nuevo más tarde.",
            discord.NotFound: "❌ El recurso solicitado no fue encontrado.",
            discord.Forbidden: "🔒 No tengo permisos para realizar esta acción.",
            discord.HTTPException: "🌐 Error de conexión. Intenta de nuevo más tarde."
        }
        
        for error_type, message in error_mapping.items():
            if isinstance(error, error_type):
                embed = discord.Embed(
                    title="Error",
                    description=message,
                    color=0xe74c3c
                )
                try:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                except:
                    await interaction.followup.send(embed=embed, ephemeral=True)
                return
        
        # Error no manejado específicamente
        logger.error(f"Error no manejado en {command_name}: {error}")
        embed = discord.Embed(
            title="❌ Error del Sistema",
            description="Ocurrió un error inesperado. Los desarrolladores han sido notificados.",
            color=0xe74c3c
        )
        try:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            await interaction.followup.send(embed=embed, ephemeral=True)

# Instancias globales para fácil acceso
pet_helpers = PetHelpers()
embed_helpers = EventHelpers()  # Reutilizando para embeds generales
event_helpers = EventHelpers()
moderation_helpers = ModerationHelpers()
permission_helpers = PermissionHelpers()
logging_helpers = LoggingHelpers()
error_helpers = ErrorHandlingHelpers()

# Helper de embeds generales (para backward compatibility)
class EmbedHelpers:
    @staticmethod
    def create_success_embed(title: str, description: str) -> discord.Embed:
        return discord.Embed(title=f"✅ {title}", description=description, color=0x00FF00)
    
    @staticmethod
    def create_error_embed(title: str, description: str) -> discord.Embed:
        return discord.Embed(title=f"❌ {title}", description=description, color=0xFF0000)
    
    @staticmethod
    def create_warning_embed(title: str, description: str) -> discord.Embed:
        return discord.Embed(title=f"⚠️ {title}", description=description, color=0xFFA500)
    
    @staticmethod
    def create_info_embed(title: str, description: str) -> discord.Embed:
        return discord.Embed(title=f"ℹ️ {title}", description=description, color=0x3498DB)

embed_helpers_general = EmbedHelpers()