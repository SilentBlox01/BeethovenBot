# Beethoven
Un bot creado en discod.py de codigo abierto.

# Beethoven Bot 🎵🐾

![Beethoven Logo](https://cdn.discordapp.com/banners/872866276232540190/14da5680b5231ad6eb1d7f5b40cf3889.png?size=1024)  

Beethoven Bot es un bot multifuncional para Discord que combina entretenimiento, sistemas de economía, mascotas virtuales (pets), niveles de usuario, logros, música, y un panel web completo para la gestión de la cuenta y estadísticas.

---

## 🌟 Características principales

### 1. Sistema de **Pets**
- Pets clasificados por rareza:
  - Comunes
  - Poco comunes
  - Raras
  - Épicas
  - Legendarias
  - Míticas
  - Universales
- Los usuarios pueden **adoptar, evolucionar y mejorar** sus pets.
- Cada pet tiene **estadísticas y habilidades especiales**.
- Sistema de **niveles de pets** usando XP ganado al interactuar con el bot.
- Tienda para comprar items y mejorar los pets.


### 2. Sistema de **Niveles y XP**
- Los usuarios ganan XP **hablando en el servidor**.
- Niveles desbloquean recompensas exclusivas y logros.
- Sistema de **logros** progresivos con dificultad creciente (al menos 50 logros planeados).

### 3. Sistema de **Logros**
- Logros temáticos y progresivos para los pets:
  - Desde actividades básicas hasta retos complejos.
  - Desbloquean recompensas como monedas, items y pets especiales.

### 4. Panel web interactivo (en desarrollo)
- URL: `bot.beethoven.gg`  
- Permite gestionar tu cuenta y ver estadísticas.
- Integración con el bot para **consultar pets, XP, logros y economía**.
- Diseño moderno y profesional con soporte de login seguro.

### 5. Funcionalidades adicionales
- Comandos de música (en desarrollo) (play, pause, skip, queue)
- Sistema de reportes de bugs directamente en un canal del servidor de desarrollo
- Integración con APIs de anime (Jikan)
- Generación de códigos QR y utilidades adicionales

---

## ⚙️ Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/SilentBlox01/beethoven.git
cd beethoven
Crear un entorno virtual (recomendado):

python -m venv venv
source venv/bin/activate  # Linux / macOS
venv\Scripts\activate     # Windows
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Crear un archivo .env con las variables necesarias:

```
DISCORD_TOKEN=Tu_Token_Aquí
PREFIX=!
DATABASE_URL=sqlite:///data.db
WEB_PORT=8000
```

🚀 Uso

Ejecutar el bot:

```
python bot.py
```

Comandos principales en Discord:

```
!adoptar [pet]       -> Adoptar un pet
!mispets             -> Ver tus pets
!perfil              -> Ver tu perfil de usuario
!logros              -> Lista tus logros
!monedas             -> Ver tu saldo
!play [url/canción]  -> Reproducir música
```

Acceder al panel web:

```
http://localhost:8000
```

📁 Estructura de archivos
```
/beethoven
├─ bot.py                 # Script principal del bot
├─ requirements.txt       # Dependencias
├─ keepalive.py           # Script de Keep Alive para web server
├─ utils/                 # Funciones y helpers del bot
├─ cogs/                  # Todos los comandos y sistemas del bot
│  ├─ pets.py
│  ├─ economia.py
│  ├─ niveles.py
│  └─ logros.py
├─ web/                   # Archivos del panel web
│  ├─ templates/
│  │  ├─ index.html
│  │  ├─ perfil.html
│  │  └─ pets.html
│  └─ static/
│     ├─ css/
│     └─ js/
└─ data/                  # Base de datos SQLite
```

🛠️ Dependencias principales
```
discord.py
 ≥ 2.2.2

Flask

aiosqlite

requests

qrcode

JikanPy
```

💡 Contribuciones

Si quieres contribuir:

Haz un fork del repositorio

Crea una rama para tu feature (git checkout -b feature/nueva-funcion)

Haz commit de tus cambios (git commit -m "Agrega nueva función")

Haz push a la rama (git push origin feature/nueva-funcion)

Abre un Pull Request

⚖️ Licencia
```
Este proyecto está bajo la licencia MIT.
Consulta el archivo LICENSE
 para más detalles.
```

🎯 Próximos pasos planeados

Completar 50 logros progresivos

Mejorar el diseño del panel web

Añadir pets universales y habilidades especiales

Crear eventos automáticos y minijuegos

Web de manejo del bot

Integracion con sistema de musica


# **Nota**
# Este bot requiere muchisimas dependencias y el codigo es grande, por lo que tarda un poco en arrancar. Estay trabajando duro para optimizarlo lo mejor posible. Gracias por considerar este proyecto! ^^