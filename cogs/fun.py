# cogs/fun.py
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import random
import asyncio
from utils.rate_limiter import safe_interaction_response, safe_followup_send
from utils.database import db

class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ------------------ Comandos existentes ------------------
    @app_commands.command(name="hello", description="El bot te saluda.")
    async def hello(self, interaction: discord.Interaction):
        await safe_interaction_response(interaction, f"Hola {interaction.user.mention}! ¿Qué tal?")

    @app_commands.command(name="bola8", description="Pregúntale algo a la bola 8.")
    @app_commands.describe(question="Tu pregunta")
    async def bola8(self, interaction: discord.Interaction, question: str):
        responses = [
            "Sí", "No", "Quizás", "Probablemente", "No lo sé", 
            "Absolutamente", "Nunca", "Tal vez", "Definitivamente sí",
            "Definitivamente no", "Pregunta más tarde", "Mejor no te digo"
        ]
        await safe_interaction_response(
            interaction, 
            f"🎱 **Pregunta:** {question}\n🎱 **Respuesta:** {random.choice(responses)}"
        )

    @app_commands.command(name="dado", description="Tira un dado.")
    async def dice(self, interaction: discord.Interaction):
        result = random.randint(1, 6)
        await safe_interaction_response(interaction, f"🎲 {interaction.user.mention} tiró un dado y obtuvo: **{result}**")

    @app_commands.command(name="moneda", description="Lanza una moneda.")
    async def coin(self, interaction: discord.Interaction):
        result = random.choice(["Cara", "Cruz"])
        await safe_interaction_response(interaction, f"🪙 {interaction.user.mention} lanzó una moneda: **{result}**")

    # ------------------ Comandos de amor/diversión ------------------
    @app_commands.command(name="lovecalc", description="Calcula el amor entre dos personas")
    @app_commands.describe(user1="Usuario 1", user2="Usuario 2")
    async def lovecalc(self, interaction: discord.Interaction, user1: discord.Member, user2: discord.Member):
        percent = random.randint(0, 100)
        await safe_interaction_response(interaction, f"💖 {user1.mention} y {user2.mention} tienen un **{percent}% de compatibilidad**.")

    @app_commands.command(name="ship", description="Combina dos usuarios y genera un ship name")
    @app_commands.describe(user1="Usuario 1", user2="Usuario 2")
    async def ship(self, interaction: discord.Interaction, user1: discord.Member, user2: discord.Member):
        name1 = user1.display_name[:len(user1.display_name)//2]
        name2 = user2.display_name[len(user2.display_name)//2:]
        ship_name = name1 + name2
        await safe_interaction_response(interaction, f"💞 El ship entre {user1.mention} y {user2.mention} es **{ship_name}**")

    @app_commands.command(name="compliment", description="Envía un cumplido a alguien")
    @app_commands.describe(user="Usuario a quien hacer el cumplido")
    async def compliment(self, interaction: discord.Interaction, user: discord.Member):
        compliments = ["¡Eres increíble!", "¡Qué talento tienes!", "¡Me inspiras!"]
        await safe_interaction_response(interaction, f"💖 {user.mention}, {random.choice(compliments)}")

    @app_commands.command(name="insult", description="Insulta de manera divertida a alguien")
    @app_commands.describe(user="Usuario a quien insultar")
    async def insult(self, interaction: discord.Interaction, user: discord.Member):
        insults = ["¡Eres un desastre!", "¡Qué desastre de persona!", "¡Me haces reír a carcajadas!"]
        await safe_interaction_response(interaction, f"😈 {user.mention}, {random.choice(insults)}")

    # ------------------ Comandos de azar ------------------
    @app_commands.command(name="fortune", description="Recibe una fortuna aleatoria.")
    async def fortune(self, interaction: discord.Interaction):
        fortunes = [
            "Hoy tendrás un día lleno de sorpresas.",
            "Un amigo te traerá buenas noticias.",
            "Prepárate para un cambio inesperado.",
            "El éxito está cerca, no te rindas.",
            "Alguien apreciará un detalle tuyo hoy.",
            "Tu creatividad te abrirá nuevas puertas.",
            "Evita discusiones innecesarias, hoy es día de paz.",
            "Un pequeño riesgo traerá grandes recompensas.",
            "La paciencia será tu mejor aliada.",
            "Un viaje inesperado podría ocurrir pronto."
            "Una sonrisa que des hoy volverá a ti multiplicada.",
            "Tu intuición te guiará hacia algo especial.",
            "Una puerta que creías cerrada se abrirá pronto.",
            "Hoy alguien te recordará con cariño.",
            "Tu esfuerzo silencioso será reconocido.",
            "Una coincidencia te hará pensar dos veces.",
            "El universo está conspirando a tu favor.",
            "Una idea que parecía pequeña se volverá gigante.",
            "Hoy será un buen día para empezar algo nuevo.",
            "Tu energía atraerá personas valiosas.",
            "Un recuerdo feliz te visitará cuando menos lo esperes.",
            "Tu voz será escuchada en el momento justo.",
            "Una conversación casual te dará una gran pista.",
            "Hoy es un buen día para confiar en ti.",
            "Un gesto amable cambiará el rumbo de tu día.",
            "Tu talento brillará sin que lo busques.",
            "Una sorpresa te hará sonreír antes de dormir.",
            "Hoy alguien pensará en ti con gratitud.",
            "Tu paciencia será recompensada de forma inesperada.",
            "Un mensaje que esperabas llegará pronto.",
            "Tu luz interior será más visible que nunca.",
            "Una nueva oportunidad está tocando tu puerta.",
            "Hoy es el día perfecto para soltar lo que pesa.",
            "Tu creatividad será la llave de algo nuevo.",
            "Una canción te recordará quién eres.",
            "Tu presencia será más importante de lo que imaginas.",
            "Un pequeño cambio traerá una gran mejora.",
            "Hoy es buen momento para decir lo que sientes.",
            "Tu calma será contagiosa para quienes te rodean.",
            "Una decisión valiente traerá paz a tu corazón.",
            "Tu curiosidad te llevará a un descubrimiento feliz.",
            "Un reencuentro te llenará de alegría.",
            "Hoy alguien te verá como su inspiración.",
            "Tu silencio tendrá más fuerza que mil palabras.",
            "Una señal te mostrará que vas por buen camino.",
            "Hoy es el día ideal para agradecer sin razón.",
            "Tu ternura será el regalo que alguien necesita.",
            "Una nueva amistad está por comenzar.",
            "Tu historia está a punto de dar un giro hermoso.",
            "Hoy el universo te susurra: confía.",
            "Tu risa será medicina para alguien cercano.",
            "Una puerta que no esperabas se abrirá con facilidad.",
            "Tu valor será admirado en silencio.",
            "Hoy es el día para dejar que la magia ocurra.",
            "Tu mirada traerá consuelo a quien lo necesita.",
            "Una idea olvidada volverá con fuerza renovada.",
            "Tu presencia será justo lo que alguien necesita.",
            "Hoy es buen momento para sembrar algo nuevo.",
            "Tu bondad será recordada más de lo que imaginas.",
            "Una estrella fugaz te concederá un deseo secreto.",
            "Tu camino se aclarará con una simple señal."
        ]
        await safe_interaction_response(interaction, f"🔮 **Fortuna:** {random.choice(fortunes)}")

    @app_commands.command(name="curse", description="Lanza una maldicion totalmente estupida e inecesaria.")
    async def curse(self, interaction: discord.Interaction):
        curses = [
            "Que cada vez que te pongas a escribir, el bolígrafo se quede sin tinta.",
            "Que tu silla siempre tenga una pata coja cuando más la necesites.",
            "Que cada vez que te pongas los zapatos, uno esté más apretado que el otro.",
            "Que tu ventilador solo funcione cuando no estás en la habitación.",
            "Que cada vez que digas 'esto es fácil', se complique por arte de magia.",
            "Que tu mochila siempre pese más de lo que debería.",
            "Que cada vez que te pongas a estudiar, el vecino decida hacer karaoke.",
            "Que tu comida se enfríe justo cuando encuentres el tenedor.",
            "Que cada vez que digas 'no puede ser', efectivamente pueda ser.",
            "Que tu gato te mire con juicio cada vez que bailes solo.",
            "Que cada vez que te pongas a limpiar, aparezca una nueva telaraña.",
            "Que tu paraguas se rompa justo cuando empieza la tormenta.",
            "Que cada vez que digas 'ya casi termino', te falte la mitad.",
            "Que tu cargador solo funcione si lo colocas en una posición imposible.",
            "Que cada vez que te pongas a cocinar, el gas se acabe.",
            "Que tu serie favorita se pause justo en el cliffhanger.",
            "Que cada vez que te pongas los lentes, estén sucios por dentro.",
            "Que tu café se enfríe mientras decides qué taza usar.",
            "Que cada vez que digas 'esto nunca falla', falle discretamente.",
            "Que tu impresora imprima una hoja en blanco por cada hoja útil.",
            "Que cada vez que te pongas a meditar, alguien toque el timbre.",
            "Que tu sandwich se desarme al primer mordisco.",
            "Que cada vez que te pongas a grabar, pase una moto ruidosa.",
            "Que tu taza favorita tenga una grieta invisible que gotea solo cuando la usas.",
            "Que cada vez que digas 'ya está listo', descubras que falta un paso.",
            "Que tu mouse se congele justo cuando estás por hacer clic.",
            "Que cada vez que digas 'ahora sí', se te olvide lo que ibas a hacer.",
            "Que tu ropa recién lavada huela a humedad sin explicación.",
            "Que cada vez que digas 'solo un minuto', te tarden diez.",
            "Que tu app favorita se actualice justo cuando la necesitas.",
            "Que cada vez que te pongas a cocinar, falte un ingrediente esencial.",
            "Que tu silla gire lentamente sin que lo notes, hasta que estés mirando a la pared.",
            "Que cada vez que digas 'no me voy a olvidar', lo olvides en menos de una hora.",
            "Que tu sandwich se caiga siempre con el lado untado hacia abajo.",
            "Que cada vez que te pongas a leer, alguien te hable de algo urgente.",
            "Que tu lápiz se quede sin punta justo cuando estás inspirado.",
            "Que cada vez que digas 'esto nunca falla', falle discretamente.",
            "Que tu ventilador haga un sonido que solo tú escuchas.",
            "Que cada vez que te pongas a grabar, pase una moto ruidosa.",
            "Que tu espejo te muestre despeinado justo cuando creías estar perfecto.",
            "Que cada vez que te acomodes en la cama, recuerdes algo pendiente.",
            "Que tu teclado escriba una letra de más cuando estés apurado.",
            "Que tu sandwich se desarme al primer mordisco.",
            "Que cada vez que te pongas a limpiar, aparezca una nueva mancha.",
            "Que tu alarma suene cinco minutos antes de que realmente debas levantarte.",
            "Que cada vez que digas 'no pasa nada', pase algo pequeño pero molesto.",
            "Que tu sombrilla se voltee con el primer viento tímido.",
            "Que cada vez que te pongas a leer, alguien te hable de algo urgente.",
            "Que tu mouse se congele justo cuando estás por hacer clic.",
            "Que cada vez que digas 'ahora sí', se te olvide lo que ibas a hacer.",
            "Que tu comida se enfríe mientras decides qué serie ver.",
            "Que cada vez que te pongas a escribir, el cursor desaparezca por arte de magia.",
            "Que tu ropa recién lavada huela a humedad sin explicación.",
            "Que cada vez que digas 'solo un minuto', te tarden diez.",
            "Que tu app favorita se actualice justo cuando la necesitas.",
            "Que cada vez que te pongas a cocinar, falte un ingrediente esencial.",
            "Que tu silla gire lentamente sin que lo notes, hasta que estés mirando a la pared.",
            "Que cada vez que digas 'no me voy a olvidar', lo olvides en menos de una hora.",
            "Que tu sandwich se caiga siempre con el lado untado hacia abajo.",
            "Que cada vez que te pongas a meditar, alguien toque el timbre.",
            "Que tu lápiz se quede sin punta justo cuando estás inspirado.",
            "Que cada vez que digas 'esto nunca falla', falle discretamente.",
            "Que tu ventilador haga un sonido que solo tú escuchas.",
            "Que cada vez que te pongas a grabar, pase una moto ruidosa.",
            "Que tu taza favorita tenga una grieta invisible que gotea solo cuando la usas.",
            "Que cada vez que digas 'ya está listo', descubras que falta un paso."
        ]
        await safe_interaction_response(interaction, f"🪄 Maldición: {random.choice(curses)}")

    # ------------------ Piedra, papel o tijera ------------------
    @app_commands.command(name="rps", description="Juega piedra, papel o tijera con el bot.")
    async def rps(self, interaction: discord.Interaction):
        class RPSView(View):
            def __init__(self, original_interaction: discord.Interaction):
                super().__init__(timeout=30.0)
                self.original_interaction = original_interaction
                self.user_choice = None
                self.bot_choice = None

            @discord.ui.button(label="🪨 Piedra", style=discord.ButtonStyle.primary)
            async def rock(self, interaction: discord.Interaction, button: Button):
                await self.handle_choice(interaction, "🪨")

            @discord.ui.button(label="📜 Papel", style=discord.ButtonStyle.primary)
            async def paper(self, interaction: discord.Interaction, button: Button):
                await self.handle_choice(interaction, "📜")

            @discord.ui.button(label="✂️ Tijera", style=discord.ButtonStyle.primary)
            async def scissors(self, interaction: discord.Interaction, button: Button):
                await self.handle_choice(interaction, "✂️")

            async def handle_choice(self, interaction: discord.Interaction, choice: str):
                self.user_choice = choice
                self.bot_choice = random.choice(["🪨", "📜", "✂️"])
                if self.user_choice == self.bot_choice:
                    result = "Empate!"
                elif (self.user_choice == "🪨" and self.bot_choice == "✂️") or \
                     (self.user_choice == "📜" and self.bot_choice == "🪨") or \
                     (self.user_choice == "✂️" and self.bot_choice == "📜"):
                    result = "¡Ganaste! 🎉"
                else:
                    result = "¡Perdiste! 💀"

                embed = discord.Embed(title="Piedra, Papel o Tijera - Resultado", color=discord.Color.green())
                embed.add_field(name="Tu elección", value=self.user_choice, inline=True)
                embed.add_field(name="Elección del bot", value=self.bot_choice, inline=True)
                embed.add_field(name="Resultado", value=result, inline=True)
                await interaction.response.edit_message(embed=embed, view=None)
                self.stop()

            async def on_timeout(self):
                try:
                    await self.original_interaction.edit_original_response(
                        content="⏰ Tiempo agotado. El juego ha terminado.",
                        view=None
                    )
                except:
                    pass

        embed = discord.Embed(
            title="Piedra, Papel o Tijera",
            description="Elige una opción:",
            color=discord.Color.blue()
        )
        await safe_interaction_response(interaction, embed=embed, view=RPSView(interaction))


async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))
