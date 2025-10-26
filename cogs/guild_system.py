import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Dict, Any
from utils.database import get_user_pets, save_user_pets, create_guild, get_guild, update_guild
from utils.constants import PET_CLASSES  # Importar si es necesario para integración

logger = logging.getLogger(__name__)

class GuildSystem(commands.Cog):
    """Sistema de gremios para BeethovenBot"""
    
    def __init__(self, bot):
        self.bot = bot

    async def create_guild(self, user_id: str, guild_name: str, discord_guild_id: str = None) -> Dict[str, Any]:
        """Crea un nuevo gremio"""
        try:
            user_data = get_user_pets(user_id)
            if user_data.get("guild_id"):
                return {"success": False, "message": "Ya perteneces a un gremio. Debes salir primero."}
            
            guild_id = str(random.randint(100000, 999999))  # ID simple, considera usar UUID
            guild_data = {
                "guild_id": guild_id,
                "name": guild_name,
                "owner_id": user_id,
                "members": [user_id],
                "created_at": str(datetime.now()),
                "last_update": str(datetime.now()),
                "level": 1,
                "xp": 0,
                "bank": 0
            }
            if discord_guild_id:
                guild_data["discord_guild_id"] = discord_guild_id
            
            if await create_guild(guild_data):
                user_data["guild_id"] = guild_id
                user_data["guild_role"] = "owner"
                save_user_pets(user_id, user_data)
                return {"success": True, "message": f"Gremio **{guild_name}** creado con éxito! ID: {guild_id}"}
            else:
                return {"success": False, "message": "Error al crear el gremio en la base de datos."}
        except Exception as e:
            logger.error(f"Error creando gremio: {e}")
            return {"success": False, "message": "Error al crear el gremio."}

    async def join_guild(self, user_id: str, guild_id: str) -> Dict[str, Any]:
        """Une a un usuario a un gremio"""
        try:
            user_data = get_user_pets(user_id)
            if user_data.get("guild_id"):
                return {"success": False, "message": "Ya perteneces a un gremio. Debes salir primero."}
            
            guild_data = await get_guild(guild_id)
            if not guild_data:
                return {"success": False, "message": "Gremio no encontrado."}
            
            if user_id in guild_data["members"]:
                return {"success": False, "message": "Ya eres miembro de este gremio."}
            
            guild_data["members"].append(user_id)
            guild_data["last_update"] = str(datetime.now())
            await update_guild(guild_id, guild_data)
            
            user_data["guild_id"] = guild_id
            user_data["guild_role"] = "member"
            save_user_pets(user_id, user_data)
            
            return {"success": True, "message": f"Te has unido al gremio **{guild_data['name']}**!"}
        except Exception as e:
            logger.error(f"Error uniéndose a gremio: {e}")
            return {"success": False, "message": "Error al unirse al gremio."}

    async def leave_guild(self, user_id: str) -> Dict[str, Any]:
        """Sale de un gremio"""
        try:
            user_data = get_user_pets(user_id)
            guild_id = user_data.get("guild_id")
            if not guild_id:
                return {"success": False, "message": "No perteneces a ningún gremio."}
            
            guild_data = await get_guild(guild_id)
            if not guild_data:
                return {"success": False, "message": "Gremio no encontrado."}
            
            if user_id == guild_data["owner_id"]:
                return {"success": False, "message": "El dueño no puede salir del gremio. Transfiere la propiedad primero."}
            
            guild_data["members"].remove(user_id)
            guild_data["last_update"] = str(datetime.now())
            await update_guild(guild_id, guild_data)
            
            del user_data["guild_id"]
            del user_data["guild_role"]
            save_user_pets(user_id, user_data)
            
            return {"success": True, "message": f"Has salido del gremio **{guild_data['name']}**."}
        except Exception as e:
            logger.error(f"Error saliendo de gremio: {e}")
            return {"success": False, "message": "Error al salir del gremio."}

    async def get_guild_info(self, guild_id: str) -> Dict[str, Any]:
        """Obtiene información de un gremio"""
        try:
            guild_data = await get_guild(guild_id)
            if not guild_data:
                return {"success": False, "message": "Gremio no encontrado."}
            
            return {"success": True, "data": guild_data}
        except Exception as e:
            logger.error(f"Error obteniendo info de gremio: {e}")
            return {"success": False, "message": "Error al obtener info del gremio."}

    @app_commands.command(name="guild", description="Gestiona tu gremio")
    @app_commands.describe(action="Acción a realizar", guild_name="Nombre del gremio (para crear)", guild_id="ID del gremio (para unirte o info)")
    async def guild(self, interaction: discord.Interaction, action: str, guild_name: str = None, guild_id: str = None):
        """Comando principal para gremios"""
        await interaction.response.defer()
        user_id = str(interaction.user.id)
        
        try:
            if action == "create" and guild_name:
                result = await self.create_guild(user_id, guild_name, str(interaction.guild_id))
            elif action == "join" and guild_id:
                result = await self.join_guild(user_id, guild_id)
            elif action == "leave":
                result = await self.leave_guild(user_id)
            elif action == "info" and guild_id:
                result = await self.get_guild_info(guild_id)
                if result["success"]:
                    data = result["data"]
                    embed = discord.Embed(title=f"Gremio: {data['name']}", color=0x3498db)
                    embed.add_field(name="ID", value=data['guild_id'], inline=True)
                    embed.add_field(name="Dueño", value=f"<@{data['owner_id']}>", inline=True)
                    embed.add_field(name="Miembros", value=len(data['members']), inline=True)
                    embed.add_field(name="Nivel", value=data['level'], inline=True)
                    embed.add_field(name="Banco", value=f"{data['bank']} 💰", inline=True)
                    embed.add_field(name="Creado", value=data['created_at'], inline=False)
                    embed.add_field(name="Miembros", value="\n".join([f"<@{member}>" for member in data['members']]), inline=False)
                    await interaction.followup.send(embed=embed)
                    return
            else:
                await interaction.followup.send("❌ Acción no válida o parámetros faltantes. Usa: create [nombre], join [id], leave, info [id]")
                return
            
            if result["success"]:
                await interaction.followup.send(result["message"])
            else:
                await interaction.followup.send(f"❌ {result['message']}")
        except Exception as e:
            logger.error(f"Error en comando /guild: {e}")
            await interaction.followup.send("❌ Error al procesar el comando de gremio.")

async def setup(bot):
    await bot.add_cog(GuildSystem(bot))