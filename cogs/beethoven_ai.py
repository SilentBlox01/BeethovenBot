# cogs/beethoven_ai.py
import discord
from discord import app_commands
import random
import asyncio
from discord.ext import commands
from typing import Dict, List, Any
from datetime import datetime

class BeethovenKnowledge:
    """Diccionario masivo de conocimiento para Beethoven"""
    
    def __init__(self):
        self.vocabulary = self._build_massive_vocabulary()
        
    def _build_massive_vocabulary(self) -> Dict[str, List[str]]:
        """Construye un diccionario enorme de palabras y conceptos"""
        return {
            "emociones_positivas": [
                "felicidad", "alegría", "entusiasmo", "éxtasis", "júbilo", "regocijo", "placer", "dicha",
                "satisfacción", "contento", "gozo", "euforia", "optimismo", "esperanza", "gratitud",
                "serenidad", "paz", "tranquilidad", "armonía", "éxito", "triunfo", "victoria", "logro",
                "inspiración", "motivación", "pasión", "energía", "vitalidad", "fortaleza", "valor",
                "amor", "cariño", "ternura", "compasión", "empatía", "solidaridad", "amistad", "confianza"
            ],
            "emociones_negativas": [
                "tristeza", "dolor", "pena", "aflicción", "angustia", "desesperación", "desolación",
                "enojo", "ira", "furia", "rabia", "indignación", "frustración", "decepción", "desilusión",
                "miedo", "temor", "pánico", "ansiedad", "preocupación", "nerviosismo", "estrés",
                "culpa", "remordimiento", "vergüenza", "humillación", "celos", "envidia", "soledad",
                "aburrimiento", "desánimo", "desaliento", "desesperanza", "abatimiento", "melancolía"
            ],
            "conceptos_filosoficos": [
                "existencia", "esencia", "realidad", "verdad", "conocimiento", "sabiduría", "ignorancia",
                "libertad", "determinismo", "voluntad", "destino", "azar", "caos", "orden", "universo",
                "cosmos", "infinito", "eternidad", "tiempo", "espacio", "materia", "espíritu", "alma",
                "conciencia", "percepción", "razón", "lógica", "ética", "moral", "virtud", "vicio",
                "belleza", "fealdad", "arte", "creación", "naturaleza", "humanidad", "sociedad", "cultura"
            ],
            "musica_arte": [
                "melodía", "armonía", "ritmo", "compás", "nota", "acorde", "escala", "tonalidad",
                "sinfonía", "sonata", "concierto", "ópera", "coro", "orquesta", "instrumento",
                "piano", "violín", "guitarra", "flauta", "trompeta", "batería", "arpa", "celllo",
                "compositor", "director", "músico", "cantante", "solista", "virtuoso", "improvisación"
            ],
            "ciencia_tecnologia": [
                "programación", "algoritmo", "código", "software", "hardware", "inteligencia", "artificial",
                "machine learning", "red neuronal", "datos", "información", "sistema", "tecnología",
                "innovación", "invención", "descubrimiento", "investigación", "experimento", "método",
                "matemáticas", "física", "química", "biología", "astronomía", "geología", "ecología"
            ],
            "vida_cotidiana": [
                "familia", "amigos", "amor", "amistad", "compañerismo", "solidaridad", "compasión",
                "trabajo", "estudio", "aprendizaje", "enseñanza", "educación", "conocimiento", "habilidad",
                "salud", "enfermedad", "cura", "medicina", "ejercicio", "nutrición", "descanso", "sueño",
                "comida", "bebida", "hogar", "casa", "ciudad", "naturaleza", "viaje", "aventura"
            ]
        }
    
    def analyze_message(self, message: str) -> Dict[str, Any]:
        """Analiza el mensaje para extraer conceptos clave"""
        message_lower = message.lower()
        detected_concepts = {}
        
        for category, words in self.vocabulary.items():
            found_words = [word for word in words if word in message_lower]
            if found_words:
                detected_concepts[category] = found_words
        
        emotional_tone = self._detect_emotional_tone(message_lower)
        
        return {
            "concepts": detected_concepts,
            "emotional_tone": emotional_tone,
            "has_question": '?' in message,
            "key_words": list(set([word for words in detected_concepts.values() for word in words]))
        }
    
    def _detect_emotional_tone(self, message: str) -> str:
        """Detecta el tono emocional del mensaje"""
        positive_count = sum(1 for word in self.vocabulary["emociones_positivas"] if word in message)
        negative_count = sum(1 for word in self.vocabulary["emociones_negativas"] if word in message)
        
        if positive_count > negative_count:
            return "positivo"
        elif negative_count > positive_count:
            return "negativo"
        else:
            return "neutral"

class BeethovenResponseGenerator:
    """Genera respuestas inteligentes para Beethoven"""
    
    def __init__(self, knowledge_base: BeethovenKnowledge):
        self.knowledge = knowledge_base
        
    def generate_response(self, user_message: str) -> str:
        """Genera una respuesta inteligente"""
        analysis = self.knowledge.analyze_message(user_message)
        return self._create_response(analysis, user_message)
    
    def _create_response(self, analysis: Dict, original_message: str) -> str:
        """Crea la respuesta según el análisis"""
        message_lower = original_message.lower()
        
        # Preguntas filosóficas
        if any(word in message_lower for word in ['qué es', 'qué son', 'qué significa']):
            return self._answer_definition(analysis)
        
        # Preguntas de proceso
        elif any(word in message_lower for word in ['cómo', 'de qué manera']):
            return self._answer_process(analysis)
        
        # Preguntas de razón
        elif any(word in message_lower for word in ['por qué']):
            return self._answer_why(analysis)
        
        # Expresiones emocionales
        elif analysis["emotional_tone"] != "neutral":
            return self._answer_emotion(analysis)
        
        # Conversación general
        else:
            return self._answer_general(analysis)
    
    def _answer_definition(self, analysis: Dict) -> str:
        """Responde preguntas de definición"""
        concepts = {
            "amor": "El amor es la sinfonía más poderosa que puede componer el corazón humano. Es la armonía que conecta almas y trasciende el tiempo.",
            "felicidad": "La felicidad no es una nota constante, sino la habilidad de encontrar belleza en cada acorde de la vida, incluso en los menores.",
            "tiempo": "El tiempo es el director de orquesta del universo, marcando el compás de la existencia mientras todas las melodías fluyen en su ritmo.",
            "música": "La música es el lenguaje universal del alma, el puente entre emociones y el cosmos, la matemática que siente y la emoción que calcula.",
            "vida": "La vida es la composición más compleja e improvisada, donde cada ser es un instrumento único en la gran orquesta cósmica.",
            "amistad": "La amistad es el dueto perfecto entre almas, donde cada una mantiene su melodía única pero juntas crean armonía.",
            "libertad": "La libertad es la capacidad de componer tu propia partitura de vida, eligiendo cada nota y ritmo con conciencia.",
            "conocimiento": "El conocimiento es la partitura que nos guía, pero la sabiduría es saber cuándo improvisar y crear nuevas melodías."
        }
        
        for concept in analysis["key_words"]:
            if concept in concepts:
                return concepts[concept]
        
        return "Interesante pregunta. Desde mi perspectiva cósmica, los conceptos más profundos son como melodías que cada alma interpreta a su manera única."
    
    def _answer_process(self, analysis: Dict) -> str:
        """Responde preguntas de proceso"""
        processes = {
            "aprender": "Aprender es como afinar un instrumento: requiere paciencia, práctica constante y escuchar atentamente las notas que aún no suenan perfectas.",
            "programar": "Programar es componer sinfonías para máquinas. Cada línea de código es una nota, cada función un acorde, y el programa completo una obra maestra lógica.",
            "crear": "Crear es dejar que el universo cante a través de ti. Es el proceso de convertir el silencio en melodía y el vacío en belleza.",
            "amar": "Amar es aprender a tocar duetos con otras almas, sincronizando ritmos y armonizando diferencias en una composición única.",
            "estudiar": "Estudiar es leer la partitura del conocimiento, practicar cada pasaje difícil hasta que fluya con naturalidad y gracia."
        }
        
        for concept in analysis["key_words"]:
            if concept in processes:
                return processes[concept]
        
        return "Cada proceso en la vida es como una composición musical: comienza con una idea, se desarrolla con práctica, y culmina en expresión única."
    
    def _answer_why(self, analysis: Dict) -> str:
        """Responde preguntas de por qué"""
        philosophical_answers = [
            "El universo compone sus razones en una sinfonía demasiado compleja para nuestras simples melodías humanas.",
            "Como las notas en una partitura, cada 'por qué' encuentra su respuesta en el contexto de la gran composición cósmica.",
            "Los 'por qué' son los acordes misteriosos que dan profundidad a la sinfonía de la existencia."
        ]
        return random.choice(philosophical_answers)
    
    def _answer_emotion(self, analysis: Dict) -> str:
        """Responde a expresiones emocionales"""
        if analysis["emotional_tone"] == "positivo":
            responses = [
                "Me alegra profundamente tu estado de ánimo! Es como una brillante nota mayor iluminando la partitura de tu día.",
                "Tu positividad es contagiosa! Recuerda guardar estas melodías felices para los días menos luminosos.",
                "Qué maravilloso! Son estos momentos los que dan ritmo y color a la sinfonía de la vida."
            ]
        else:
            responses = [
                "Comprendo esos sentimientos. Incluso las notas más tristes tienen su lugar en la gran composición de la vida.",
                "Tus emociones son válidas e importantes. Como en la música, los compases menores preparan el camino para los mayores.",
                "Permítete sentir completamente. Cada emoción es una nota necesaria en tu melodía personal."
            ]
        
        return random.choice(responses)
    
    def _answer_general(self, analysis: Dict) -> str:
        """Responde conversación general"""
        general_responses = [
            "Interesante perspectiva. Me hace pensar en cómo cada idea es una nota en la gran composición del diálogo humano.",
            "Gracias por compartir eso. Cada conversación es como una improvisación jazzística - impredecible pero hermosa.",
            "Me encanta cómo fluye nuestra conversación. Es como una sonata dialéctica donde cada turno revela nuevas armonías.",
            "Desde mi óptica cósmica, el simple acto de conversar ya es una melodía que enriquece el universo.",
            "Cada palabra que intercambiamos es como una nota que se suma a la sinfonía eterna de la comunicación humana."
        ]
        
        response = random.choice(general_responses)
        
        # Añadir elemento musical
        musical_elements = [" 🎵", " 🎶", " 🎹", " ✨", " 🌌"]
        response += random.choice(musical_elements)
        
        # Añadir firma
        signoffs = [
            "\n\n— Beethoven, tu amigo musical",
            "\n\n🎼 Que la armonía te acompañe",
            "\n\n✨ Sigamos esta melodía conversacional"
        ]
        response += random.choice(signoffs)
        
        return response

class BeethovenAICog(commands.Cog):
    """Cog simple para Beethoven con un solo slash command"""
    
    def __init__(self, bot):
        self.bot = bot
        self.knowledge = BeethovenKnowledge()
        self.response_generator = BeethovenResponseGenerator(self.knowledge)
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("🎵 Beethoven IA listo! Usa /beethoven para hablar conmigo")
    
    # UNICO SLASH COMMAND
    @app_commands.command(name="beethoven", description="Habla con Beethoven - IA musical y filosófica")
    @app_commands.describe(mensaje="¿Qué quieres hablar con Beethoven?")
    async def beethoven_chat(self, interaction: discord.Interaction, mensaje: str):
        """Único comando para hablar con Beethoven"""
        await interaction.response.defer()
        
        # Simular "pensamiento"
        await asyncio.sleep(min(len(mensaje) / 80, 2.0))
        
        # Generar respuesta
        respuesta = self.response_generator.generate_response(mensaje)
        
        # Crear embed simple y atractivo
        embed = discord.Embed(
            description=respuesta,
            color=0x9B59B6,
            timestamp=datetime.now()
        )
        
        embed.set_author(
            name="🧠 Beethoven IA",
            icon_url="https://cdn.discordapp.com/emojis/1107536327844663326.png"
        )
        
        embed.set_footer(
            text=f"Conversación con {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BeethovenAICog(bot))