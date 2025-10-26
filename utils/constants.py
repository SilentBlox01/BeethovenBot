# utils/constants.py
DAILY_RESET_HOUR = 0  # Medianoche UTC
PET_NAMES_BY_RARITY = {
    "Común": ["Bolita", "Chispa", "Pelusín", "Nubi", "Tico", "Moti", "Lilo", "Coco", "Pufi", "Rulo"],
    "Poco Común": ["Zippy", "Bruma", "Tinta", "Glim", "Nekozo", "Floppi", "Quibi", "Sombrax", "Lixie", "Vento"],
    "Raro": ["Drakko", "Lumora", "Hexin", "Zoriel", "Pyxie", "Orbix", "Vayla", "Kuroko", "Nimbra", "Tundrix"],
    "Épico": ["Ignarok", "Sylphora", "Thundrax", "Cryonix", "Velkyr", "Arkanis", "Zephira", "Umbros", "Solvane", "Glacior"],
    "Legendario": ["Fenrion", "Aetherion", "Drakzeth", "Lunaris", "Obscurion", "Valtor", "Nyxara", "Chronox", "Seraphyx", "Eldrath"],
    "Mítico": ["Xelvyr", "Omnira", "Kaelith", "Zenthros", "Myrrhax", "Ecliptor", "Veylun", "Thalmyra", "Orakion", "Quorvex"],
    "Universal": ["Infinyx", "Cosmiral", "Nexora", "Eternyx", "Solithar", "Beethoven"]
}

PET_CLASSES = {
    "Común": {"probability": 0.40, "stat_multiplier": 1.0, "xp_needed": 100, "color": 0x808080, "emoji": "🔵"},
    "Poco Común": {"probability": 0.25, "stat_multiplier": 1.1, "xp_needed": 110, "color": 0x00FF00, "emoji": "🟢"},
    "Raro": {"probability": 0.15, "stat_multiplier": 1.2, "xp_needed": 120, "color": 0x0000FF, "emoji": "🔵"},
    "Épico": {"probability": 0.10, "stat_multiplier": 1.3, "xp_needed": 130, "color": 0x800080, "emoji": "🟣"},
    "Legendario": {"probability": 0.05, "stat_multiplier": 1.5, "xp_needed": 140, "color": 0xFFD700, "emoji": "🟠"},
    "Mítico": {"probability": 0.04, "stat_multiplier": 1.8, "xp_needed": 150, "color": 0x00FFFF, "emoji": "🔴"},
    "Universal": {"probability": 0.01, "stat_multiplier": 2.0, "xp_needed": 200, "color": 0xFF00FF, "emoji": "⚫"}
}

PET_TYPES = {
    "canino": {"emoji": "🐶", "base_stats": {"hambre": 50, "energía": 80, "felicidad": 70, "salud": 100}, "element": "tierra"},
    "felino": {"emoji": "🐱", "base_stats": {"hambre": 60, "energía": 70, "felicidad": 80, "salud": 90}, "element": "psíquico"},
    "dragón": {"emoji": "🐲", "base_stats": {"hambre": 40, "energía": 90, "felicidad": 60, "salud": 120}, "element": "dragón"},
    "ave": {"emoji": "🦜", "base_stats": {"hambre": 70, "energía": 60, "felicidad": 90, "salud": 80}, "element": "planta"},
    "conejo": {"emoji": "🐰", "base_stats": {"hambre": 55, "energía": 85, "felicidad": 85, "salud": 95}, "element": "eléctrico"},
    "universal": {"emoji": "🌈", "base_stats": {"hambre": 30, "energía": 100, "felicidad": 100, "salud": 150}, "element": "universal"}
}

PET_ELEMENTS = {
    "fuego": {"emoji": "🔥", "color": 0xFF4500, "weakness": "agua", "strength": "planta"},
    "agua": {"emoji": "💧", "color": 0x1E90FF, "weakness": "planta", "strength": "fuego"},
    "planta": {"emoji": "🌿", "color": 0x32CD32, "weakness": "fuego", "strength": "agua"},
    "eléctrico": {"emoji": "⚡", "color": 0xFFD700, "weakness": "tierra", "strength": "agua"},
    "hielo": {"emoji": "❄️", "color": 0x87CEEB, "weakness": "fuego", "strength": "planta"},
    "tierra": {"emoji": "🌍", "color": 0x8B4513, "weakness": "agua", "strength": "eléctrico"},
    "psíquico": {"emoji": "🔮", "color": 0x9370DB, "weakness": "oscuridad", "strength": "lucha"},
    "oscuridad": {"emoji": "🌑", "color": 0x2F4F4F, "weakness": "luz", "strength": "psíquico"},
    "luz": {"emoji": "✨", "color": 0xFFEC8B, "weakness": "oscuridad", "strength": "psíquico"},
    "dragón": {"emoji": "🐲", "color": 0x4169E1, "weakness": "hielo", "strength": "dragón"},
    "universal": {"emoji": "🌈", "color": 0xFF00FF, "weakness": None, "strength": None}
}

PET_SHOP_ITEMS = {
    "Poción de Energía": {"cost": 50, "emoji": "⚗️", "effect": "Restaura 50 de energía", "type": "consumable"},
    "Juguete Mágico": {"cost": 30, "emoji": "🧸", "effect": "Aumenta felicidad en 20", "type": "consumable"},
    "Medicina Especial": {"cost": 60, "emoji": "💊", "effect": "Restaura 50 de salud", "type": "consumable"},
    "Impulso de XP": {"cost": 80, "emoji": "📈", "effect": "Aumenta experiencia en 100", "type": "consumable"},
    "Moneda Dorada": {"cost": 100, "emoji": "💰", "effect": "Otorga 50 monedas", "type": "consumable"}
}

RARE_ITEMS = {
    "Caja Misteriosa": {"cost": 200, "emoji": "🎁", "effect": "Otorga una mascota rara aleatoria", "type": "special"},
    "Piedra Elemental": {"cost": 150, "emoji": "💎", "effect": "Cambia el elemento de la mascota", "type": "special"},
    "Ticket Raro": {"cost": 120, "emoji": "🎟️", "effect": "Aumenta la probabilidad de obtener una mascota rara", "type": "special"}
}