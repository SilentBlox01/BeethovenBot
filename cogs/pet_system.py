import discord
from discord import app_commands
from discord.ext import commands
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from utils.database import get_user_pets, save_user_pets, update_user_coins, update_user_achievements, use_item, update_mission_progress
from utils.constants import PET_NAMES_BY_RARITY, PET_CLASSES, PET_TYPES, PET_ELEMENTS, PET_SHOP_ITEMS, RARE_ITEMS

# Configuración de logging
logger = logging.getLogger(__name__)

class PetSystem(commands.Cog):
    """Sistema de mascotas para Beethoven Bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.rare_pet_tickets = {}  # Cache para tickets raros (user_id: expiration_time)

    # ===== COMANDOS DE MASCOTAS =====
    
    @app_commands.command(name="pet", description="Gestiona tus mascotas")
    @app_commands.describe(action="Acción a realizar", pet_name="Nombre de la mascota")
    async def pet(self, interaction: discord.Interaction, action: str = "view", pet_name: str = None):
        """Comando principal para gestionar mascotas"""
        await interaction.response.defer()
        user_id = str(interaction.user.id)
        user_data = get_user_pets(user_id)
        
        try:
            if action == "view":
                await self.handle_view(interaction, user_id, user_data, pet_name)
            elif action == "adopt":
                await self.handle_adopt(interaction, user_id, user_data, pet_name)
            elif action == "interact":
                await self.handle_interact(interaction, user_id, user_data, pet_name)
            elif action == "rename":
                await self.handle_rename(interaction, user_id, user_data, pet_name)
            elif action == "release":
                await self.handle_release(interaction, user_id, user_data, pet_name)
            else:
                await interaction.followup.send("❌ Acción no válida. Usa: view, adopt, interact, rename, release")
                
        except Exception as e:
            logger.error(f"Error en comando /pet: {e}")
            await interaction.followup.send("❌ Error al procesar el comando. Intenta de nuevo.")

    async def handle_view(self, interaction: discord.Interaction, user_id: str, user_data: dict, pet_name: str = None):
        """Maneja la acción de ver mascotas"""
        if not user_data["mascotas"]:
            embed = discord.Embed(
                title="Sin Mascotas",
                description="¡No tienes mascotas! Usa `/pet adopt` para adoptar una.",
                color=0xFF6B6B
            )
            await interaction.followup.send(embed=embed)
            return

        if pet_name and pet_name in user_data["mascotas"]:
            pet = user_data["mascotas"][pet_name]
            embed = discord.Embed(
                title=f"🐾 {pet_name} - {pet['tipo'].capitalize()} ({pet['clase']})",
                color=PET_CLASSES[pet["clase"]]["color"]
            )
            embed.add_field(name="Elemento", value=f"{PET_ELEMENTS[pet['elemento']]['emoji']} {pet['elemento'].capitalize()}", inline=True)
            embed.add_field(name="Nivel", value=pet["nivel"], inline=True)
            embed.add_field(name="Experiencia", value=f"{pet['experiencia']}/{PET_CLASSES[pet['clase']]['xp_needed'] * pet['nivel']}", inline=True)
            embed.add_field(name="Hambre", value=pet["hambre"], inline=True)
            embed.add_field(name="Energía", value=f"{pet['energía']}/{pet['max_energía']}", inline=True)
            embed.add_field(name="Felicidad", value=pet["felicidad"], inline=True)
            embed.add_field(name="Salud", value=f"{pet['salud']}/{pet['max_salud']}", inline=True)
            embed.add_field(name="Estado", value=pet["estado"].capitalize(), inline=True)
            embed.add_field(name="Inventario", value=", ".join([f"{item['emoji']} {item['name']}" for item in pet.get("inventario", [])]) or "Vacío", inline=False)
            await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(title="Tus Mascotas", color=0x9B59B6)
            for name, pet in user_data["mascotas"].items():
                embed.add_field(
                    name=name,
                    value=f"{pet['emoji']} {pet['tipo'].capitalize()} ({pet['clase']}) - Nivel {pet['nivel']}",
                    inline=False
                )
            embed.set_footer(text=f"Monedas: {user_data.get('coins', 0)} 💰")
            await interaction.followup.send(embed=embed)

    async def handle_adopt(self, interaction: discord.Interaction, user_id: str, user_data: dict, pet_name: str = None):
        """Maneja la adopción de una nueva mascota"""
        if len(user_data["mascotas"]) >= 10:
            await interaction.followup.send("❌ No puedes tener más de 10 mascotas.")
            return

        # Verificar si el usuario tiene un ticket raro activo
        ticket_active = self.rare_pet_tickets.get(user_id, datetime.min) > datetime.now()
        probabilities = {
            cls: data["probability"] * (2.0 if ticket_active and cls in ["Raro", "Épico", "Legendario", "Mítico", "Universal"] else 1.0)
            for cls, data in PET_CLASSES.items()
        }
        total = sum(probabilities.values())
        probabilities = {cls: prob / total for cls, prob in probabilities.items()}
        selected_class = random.choices(list(probabilities.keys()), weights=list(probabilities.values()), k=1)[0]
        
        available_names = PET_NAMES_BY_RARITY[selected_class]
        if pet_name and pet_name in available_names and pet_name not in user_data["mascotas"]:
            selected_name = pet_name
        else:
            selected_name = random.choice([name for name in available_names if name not in user_data["mascotas"]])
        
        pet_type = "universal" if selected_class == "Universal" else random.choice(list(PET_TYPES.keys()))
        pet_type_data = PET_TYPES[pet_type]
        element = pet_type_data["element"]
        stat_multiplier = PET_CLASSES[selected_class]["stat_multiplier"]

        new_pet = {
            "tipo": pet_type,
            "clase": selected_class,
            "elemento": element,
            "emoji": pet_type_data["emoji"],
            "nivel": 1,
            "experiencia": 0,
            "hambre": int(pet_type_data["base_stats"]["hambre"] * stat_multiplier),
            "energía": int(pet_type_data["base_stats"]["energía"] * stat_multiplier),
            "felicidad": int(pet_type_data["base_stats"]["felicidad"] * stat_multiplier),
            "salud": int(pet_type_data["base_stats"]["salud"] * stat_multiplier),
            "estado": "activo",
            "última_interacción": str(datetime.now()),
            "max_energía": int(pet_type_data["base_stats"]["energía"] * stat_multiplier),
            "max_salud": int(pet_type_data["base_stats"]["salud"] * stat_multiplier),
            "habilidades": [],
            "inventario": []
        }

        user_data["mascotas"][selected_name] = new_pet
        save_user_pets(user_id, user_data)
        
        # Verificar logros
        await self.check_achievements(interaction, user_id, user_data)
        
        # Actualizar misión de adopción
        await update_mission_progress(user_id, "diarias.adopt_pet", 1)
        
        embed = discord.Embed(
            title="🎉 ¡Mascota Adoptada!",
            description=f"Has adoptado a **{selected_name}**, un {pet_type} ({selected_class}) {pet_type_data['emoji']}",
            color=PET_CLASSES[selected_class]["color"]
        )
        await interaction.followup.send(embed=embed)

    async def handle_interact(self, interaction: discord.Interaction, user_id: str, user_data: dict, pet_name: str):
        """Maneja la interacción con una mascota"""
        if not pet_name or pet_name not in user_data["mascotas"]:
            await interaction.followup.send("❌ Mascota no encontrada. Usa `/pet view` para ver tus mascotas.")
            return

        pet = user_data["mascotas"][pet_name]
        if pet["estado"] == "durmiendo":
            await interaction.followup.send(f"😴 {pet_name} está durmiendo. Espera a que despierte.")
            return

        now = datetime.now()
        last_interaction = datetime.fromisoformat(pet["última_interacción"]) if pet.get("última_interacción") else now - timedelta(hours=1)
        if (now - last_interaction).total_seconds() < 300:
            await interaction.followup.send(f"⏳ {pet_name} necesita descansar. Intenta de nuevo más tarde.")
            return

        interaction_types = ["jugar", "alimentar", "acariciar"]
        interaction_type = random.choice(interaction_types)
        updates = {}
        
        if interaction_type == "jugar":
            updates["felicidad"] = 10
            updates["energía"] = -10
            updates["experiencia"] = 20
            message = f"🎾 ¡Has jugado con {pet_name}! Felicidad +10, Energía -10, XP +20"
            await update_mission_progress(user_id, "diarias.play_pet", 1)
        elif interaction_type == "alimentar":
            updates["hambre"] = -15
            updates["felicidad"] = 5
            message = f"🍽️ ¡Has alimentado a {pet_name}! Hambre -15, Felicidad +5"
            await update_mission_progress(user_id, "diarias.feed_pet", 1)
        elif interaction_type == "acariciar":
            updates["felicidad"] = 15
            updates["experiencia"] = 10
            message = f"🤗 ¡Has acariciado a {pet_name}! Felicidad +15, XP +10"
            await update_mission_progress(user_id, "diarias.pet_pet", 1)

        updates["última_interacción"] = str(now)
        from utils.database import update_pet_stats
        update_pet_stats(user_id, pet_name, updates)
        
        # Verificar si la mascota debe dormir
        if pet["energía"] + updates.get("energía", 0) <= 20:
            pet["estado"] = "durmiendo"
            pet["última_interacción"] = str(now)
            save_user_pets(user_id, user_data)
            message += f"\n😴 {pet_name} está cansado y se fue a dormir."

        await self.check_achievements(interaction, user_id, user_data)
        
        embed = discord.Embed(title="Interacción con Mascota", description=message, color=0x9B59B6)
        await interaction.followup.send(embed=embed)

    async def handle_rename(self, interaction: discord.Interaction, user_id: str, user_data: dict, pet_name: str):
        """Maneja el cambio de nombre de una mascota"""
        await interaction.followup.send("🔄 Funcionalidad de cambio de nombre en desarrollo...")
        # Implementar si es necesario

    async def handle_release(self, interaction: discord.Interaction, user_id: str, user_data: dict, pet_name: str):
        """Maneja la liberación de una mascota"""
        if not pet_name or pet_name not in user_data["mascotas"]:
            await interaction.followup.send("❌ Mascota no encontrada. Usa `/pet view` para ver tus mascotas.")
            return

        del user_data["mascotas"][pet_name]
        save_user_pets(user_id, user_data)
        embed = discord.Embed(
            title="🕊️ Mascota Liberada",
            description=f"Has liberado a **{pet_name}**. ¡Adiós, pequeño amigo!",
            color=0x9B59B6
        )
        await interaction.followup.send(embed=embed)

    # ===== TIENDA DE MASCOTAS =====
    
    @app_commands.command(name="pet_shop", description="Accede a la tienda de mascotas")
    @app_commands.describe(action="Acción: view, buy, use", item="Nombre del item", quantity="Cantidad a comprar", pet_name="Nombre de la mascota (para usar)")
    async def pet_shop(self, interaction: discord.Interaction, action: str = "view", item: str = None, quantity: int = 1, pet_name: str = None):
        """Comando para la tienda de mascotas"""
        await interaction.response.defer()
        user_id = str(interaction.user.id)
        user_data = get_user_pets(user_id)
        
        try:
            await self.handle_shop(interaction, user_id, user_data, action, item, quantity, pet_name)
        except Exception as e:
            logger.error(f"Error en comando /pet_shop: {e}")
            await interaction.followup.send("❌ Error al procesar el comando de la tienda. Intenta de nuevo.")

    async def handle_shop(self, interaction: discord.Interaction, user_id: str, user_data: dict, action: str, item: str, quantity: int, pet_name: str):
        """Maneja el comando /pet shop"""
        try:
            if action == "view":
                embed = discord.Embed(
                    title="🛍️ Tienda de Mascotas",
                    description="Compra items para tus mascotas",
                    color=0x9B59B6
                )
                
                for item_name, item_data in PET_SHOP_ITEMS.items():
                    embed.add_field(
                        name=f"{item_data['emoji']} {item_name} - 💰 {item_data['cost']}",
                        value=item_data['effect'],
                        inline=False
                    )
                for item_name, item_data in RARE_ITEMS.items():
                    embed.add_field(
                        name=f"{item_data['emoji']} {item_name} - 💰 {item_data['cost']} (Raro)",
                        value=item_data['effect'],
                        inline=False
                    )
                
                embed.set_footer(text=f"Monedas: {user_data.get('coins', 0)} 💰 | Usa /pet shop buy [item] [cantidad] o /pet shop use [item] [pet_name]")
                await interaction.followup.send(embed=embed)
            
            elif action == "buy" and item:
                if item not in PET_SHOP_ITEMS and item not in RARE_ITEMS:
                    await interaction.followup.send(f"❌ El item **{item}** no está disponible en la tienda.")
                    return
                
                item_data = PET_SHOP_ITEMS.get(item, RARE_ITEMS.get(item))
                total_cost = item_data["cost"] * quantity
                
                if quantity < 1:
                    await interaction.followup.send("❌ La cantidad debe ser mayor que 0.")
                    return
                
                if user_data.get("coins", 0) < total_cost:
                    await interaction.followup.send(f"❌ No tienes suficientes monedas. Necesitas {total_cost} 💰.")
                    return
                
                # Actualizar monedas
                user_data["coins"] = user_data.get("coins", 0) - total_cost
                update_user_coins(user_id, user_data["coins"])
                
                # Agregar items al inventario de la mascota (o al usuario si no se especifica mascota)
                target_inventory = user_data.setdefault("inventario_global", [])
                for _ in range(quantity):
                    target_inventory.append({
                        "name": item,
                        "emoji": item_data["emoji"],
                        "effect": item_data["effect"],
                        "type": item_data["type"]
                    })
                
                save_user_pets(user_id, user_data)
                await update_mission_progress(user_id, "diarias.buy_item", quantity)
                await self.check_achievements(interaction, user_id, user_data)
                
                embed = discord.Embed(
                    title="🛒 Compra Exitosa",
                    description=f"Has comprado {quantity} x **{item}** {item_data['emoji']} por {total_cost} 💰.",
                    color=0x9B59B6
                )
                embed.set_footer(text=f"Monedas restantes: {user_data['coins']} 💰")
                await interaction.followup.send(embed=embed)
            
            elif action == "use" and item and pet_name:
                if pet_name not in user_data["mascotas"]:
                    await interaction.followup.send(f"❌ No tienes una mascota llamada **{pet_name}**.")
                    return
                
                result = use_item(user_id, pet_name, item)
                if result["success"]:
                    embed = discord.Embed(
                        title="🎁 Item Usado",
                        description=f"¡Has usado **{item}** en **{pet_name}** con éxito!\n{result['message']}",
                        color=0x9B59B6
                    )
                    await update_mission_progress(user_id, "diarias.use_item", 1)
                    await self.check_achievements(interaction, user_id, user_data)
                else:
                    embed = discord.Embed(
                        title="❌ Error",
                        description=result["message"],
                        color=0xFF6B6B
                    )
                await interaction.followup.send(embed=embed)
            
            else:
                await interaction.followup.send("❌ Parámetros incorrectos. Usa: `/pet shop view`, `/pet shop buy [item] [cantidad]`, o `/pet shop use [item] [pet_name]`")
                
        except Exception as e:
            logger.error(f"❌ Error en tienda de mascotas: {e}")
            await interaction.followup.send("❌ Error en la tienda de mascotas.")

    # ===== SISTEMA DE LOGROS =====
    
    async def check_achievements(self, interaction: discord.Interaction, user_id: str, user_data: dict):
        """Verifica y actualiza los logros del usuario"""
        achievements = get_user_achievements(user_id)
        
        # Primer mascota
        if not achievements.get("primer_mascota") and user_data["mascotas"]:
            await update_user_achievements(user_id, "primer_mascota")
            user_data["coins"] = user_data.get("coins", 0) + 50
            save_user_pets(user_id, user_data)
            await interaction.followup.send("🏆 **Logro Desbloqueado: Primer Mascota** - ¡+50 monedas!")
        
        # Coleccionista novato (3 o más mascotas)
        if not achievements.get("coleccionista_novato") and len(user_data["mascotas"]) >= 3:
            await update_user_achievements(user_id, "coleccionista_novato")
            user_data["coins"] = user_data.get("coins", 0) + 100
            save_user_pets(user_id, user_data)
            await interaction.followup.send("🏆 **Logro Desbloqueado: Coleccionista Novato** - ¡+100 monedas!")
        
        # Primer raro (mascota rara o superior)
        if not achievements.get("primer_raro"):
            for pet in user_data["mascotas"].values():
                if pet["clase"] in ["Raro", "Épico", "Legendario", "Mítico", "Universal"]:
                    await update_user_achievements(user_id, "primer_raro")
                    user_data["coins"] = user_data.get("coins", 0) + 80
                    save_user_pets(user_id, user_data)
                    await interaction.followup.send("🏆 **Logro Desbloqueado: Primer Raro** - ¡+80 monedas!")
                    break
        
        # Explorador de items (comprar o usar 5 items)
        total_items = sum(len(pet.get("inventario", [])) for pet in user_data["mascotas"].values()) + len(user_data.get("inventario_global", []))
        if not achievements.get("explorador_items") and total_items >= 5:
            await update_user_achievements(user_id, "explorador_items")
            user_data["coins"] = user_data.get("coins", 0) + 60
            save_user_pets(user_id, user_data)
            await interaction.followup.send("🏆 **Logro Desbloqueado: Explorador de Items** - ¡+60 monedas!")

    # ===== SISTEMA DE MISIONES =====
    
    MISSIONS = {
        "diarias": {
            "adopt_pet": {"description": "Adopta una mascota", "goal": 1, "reward": {"coins": 30, "xp": 50}},
            "play_pet": {"description": "Juega con una mascota", "goal": 2, "reward": {"coins": 20, "xp": 30}},
            "feed_pet": {"description": "Alimenta a una mascota", "goal": 2, "reward": {"coins": 20, "xp": 30}},
            "pet_pet": {"description": "Acaricia a una mascota", "goal": 3, "reward": {"coins": 15, "xp": 20}},
            "buy_item": {"description": "Compra un item en la tienda", "goal": 1, "reward": {"coins": 10, "xp": 20}},
            "use_item": {"description": "Usa un item en una mascota", "goal": 1, "reward": {"coins": 15, "xp": 25}}
        },
        "semanales": {
            "master_collector": {"description": "Adopta 3 mascotas", "goal": 3, "reward": {"coins": 100, "xp": 150}},
            "pet_master": {"description": "Interactúa con mascotas 10 veces", "goal": 10, "reward": {"coins": 80, "xp": 120}},
            "shopper": {"description": "Compra 5 items", "goal": 5, "reward": {"coins": 50, "xp": 100}}
        }
    }

    @app_commands.command(name="pet_missions", description="Verifica tus misiones diarias y semanales")
    async def pet_missions(self, interaction: discord.Interaction):
        """Muestra las misiones del usuario y su progreso"""
        await interaction.response.defer()
        user_id = str(interaction.user.id)
        user_data = get_user_pets(user_id)
        
        try:
            embed = discord.Embed(title="📋 Tus Misiones", color=0x9B59B6)
            
            # Misiones diarias
            embed.add_field(name="Misiones Diarias", value="Resetean cada 24 horas", inline=False)
            for mission_key, mission_data in self.MISSIONS["diarias"].items():
                progress = user_data.get("misiones", {}).get("diarias", {}).get(mission_key, {}).get("progreso", 0)
                completed = progress >= mission_data["goal"]
                status = "✅ Completada" if completed else f"{progress}/{mission_data['goal']}"
                embed.add_field(
                    name=mission_data["description"],
                    value=f"Progreso: {status}\nRecompensa: {mission_data['reward']['coins']} 💰, {mission_data['reward']['xp']} XP",
                    inline=False
                )
                if completed and not user_data["misiones"]["diarias"].get(mission_key, {}).get("claimed", False):
                    await self.claim_mission_reward(user_id, user_data, "diarias", mission_key, mission_data["reward"])
                    await interaction.followup.send(f"🎉 ¡Has completado la misión diaria '{mission_data['description']}'! Recompensa: {mission_data['reward']['coins']} 💰, {mission_data['reward']['xp']} XP")
            
            # Misiones semanales
            embed.add_field(name="Misiones Semanales", value="Resetean cada 7 días", inline=False)
            for mission_key, mission_data in self.MISSIONS["semanales"].items():
                progress = user_data.get("misiones", {}).get("semanales", {}).get(mission_key, {}).get("progreso", 0)
                completed = progress >= mission_data["goal"]
                status = "✅ Completada" if completed else f"{progress}/{mission_data['goal']}"
                embed.add_field(
                    name=mission_data["description"],
                    value=f"Progreso: {status}\nRecompensa: {mission_data['reward']['coins']} 💰, {mission_data['reward']['xp']} XP",
                    inline=False
                )
                if completed and not user_data["misiones"]["semanales"].get(mission_key, {}).get("claimed", False):
                    await self.claim_mission_reward(user_id, user_data, "semanales", mission_key, mission_data["reward"])
                    await interaction.followup.send(f"🎉 ¡Has completado la misión semanal '{mission_data['description']}'! Recompensa: {mission_data['reward']['coins']} 💰, {mission_data['reward']['xp']} XP")
            
            embed.set_footer(text="Las recompensas se reclaman automáticamente al completar las misiones.")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error en comando /pet_missions: {e}")
            await interaction.followup.send("❌ Error al mostrar las misiones.")

    async def claim_mission_reward(self, user_id: str, user_data: dict, mission_type: str, mission_key: str, reward: dict):
        """Reclama la recompensa de una misión completada"""
        user_data["coins"] = user_data.get("coins", 0) + reward["coins"]
        for pet_name in user_data["mascotas"]:
            from utils.database import update_pet_stats
            update_pet_stats(user_id, pet_name, {"experiencia": reward["xp"]})
        user_data.setdefault("misiones", {}).setdefault(mission_type, {})[mission_key] = {
            "progreso": user_data["misiones"].get(mission_type, {}).get(mission_key, {}).get("progreso", 0),
            "claimed": True
        }
        save_user_pets(user_id, user_data)

async def setup(bot):
    await bot.add_cog(PetSystem(bot))