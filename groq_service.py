import os
import json
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY no encontrada en el archivo .env")

print(f"Gemini API Key loaded: {GEMINI_API_KEY[:10]}...")

# Intentar importar y configurar Gemini
try:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)

    try:
        # Usar un modelo conocido que funciona
        model = genai.GenerativeModel('gemini-2.0-flash')
        GEMINI_AVAILABLE = True
        print("Gemini AI configurado correctamente con gemini-2.0-flash")

    except Exception as e:
        print(f"Error al configurar Gemini: {e}")
        try:
            # Intentar con otro modelo
            model = genai.GenerativeModel('gemini-pro')
            GEMINI_AVAILABLE = True
            print("Gemini AI configurado correctamente con gemini-pro")
        except Exception as e2:
            print(f"Tampoco funciona gemini-pro: {e2}")
            GEMINI_AVAILABLE = False
            model = None
except ImportError as e:
    print(f"ADVERTENCIA: Google Generative AI no esta instalado: {e}")
    print("Instala con: pip install google-generativeai")
    GEMINI_AVAILABLE = False
    model = None
    genai = None
except Exception as e:
    print(f"Error al configurar Gemini: {e}")
    GEMINI_AVAILABLE = False
    model = None
    genai = None

def transcribe_audio(audio_path):
    """Transcribe audio usando Gemini AI"""
    if not GEMINI_AVAILABLE:
        return "ADVERTENCIA: Google Generative AI no esta instalado. Instala con: pip install google-generativeai"

    try:
        # Subir el archivo de audio a Gemini
        audio_file = genai.upload_file(audio_path)

        # Transcribir usando Gemini con el archivo subido
        response = model.generate_content([
            "Transcribe este audio al español. Proporciona únicamente la transcripción del habla, sin comentarios adicionales ni formato especial.",
            audio_file
        ])

        transcription = response.text.strip()
        return transcription if transcription else "No se pudo transcribir el audio."

    except Exception as e:
        return f"Error al transcribir con Gemini: {str(e)}. El archivo de audio puede ser demasiado largo o tener un formato incompatible."

def extract_profile(text):
    """Extrae información del perfil usando Gemini AI"""
    import json

    if not GEMINI_AVAILABLE:
        return json.dumps({
            "error": "ADVERTENCIA: Google Generative AI no esta instalado. Instala con: pip install google-generativeai",
            "nombre": "No disponible",
            "profesion": "No disponible",
            "experiencia": "No disponible",
            "educacion": "No disponible",
            "tecnologias": "No disponible",
            "idiomas": "No disponible",
            "logros": "No disponible",
            "habilidades_blandas": "No disponible"
        }, ensure_ascii=False)

    prompt = (
        "Analiza el siguiente texto transcrito de un video de presentación personal y extrae la información del perfil.\n\n"
        "Devuelve ÚNICAMENTE un objeto JSON válido con los siguientes campos:\n"
        "- nombre: El nombre de la persona\n"
        "- profesion: La ocupación actual, cargo o especialidad mencionada\n"
        "- experiencia: Áreas o temas en los que tiene práctica laboral o conocimiento aplicado\n"
        "- educacion: Títulos, grados, estudios o formación académica. Si no se menciona explícitamente, infiérelo lógicamente de la profesión (ej. si es 'Contador Público', educación podría ser 'Contaduría Pública'; si es 'Ingeniero de Software', 'Ingeniería de Software')\n"
        "- tecnologias: Herramientas, softwares, lenguajes o técnicas específicas mencionadas\n"
        "- idiomas: Lista de idiomas hablados o entendidos\n"
        "- logros: Reconocimientos, hitos o aportes relevantes\n"
        "- habilidades_blandas: Habilidades sociales o personales\n\n"
        "Si algún campo no está presente en el texto y no puede inferirse, usa 'No especificado'.\n\n"
        f"Texto a analizar:\n{text}\n\n"
        "Responde SOLO con el JSON, sin texto adicional."
    )

    try:
        response = model.generate_content(prompt)
        # Intentar parsear el JSON de la respuesta
        import re

        # Extraer JSON de la respuesta
        response_text = response.text.strip()

        # Buscar JSON en la respuesta (puede tener texto adicional)
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            # Validar que sea JSON válido
            parsed = json.loads(json_str)
            return json.dumps(parsed, ensure_ascii=False)
        else:
            # Si no encuentra JSON, devolver un JSON básico
            return json.dumps({
                "nombre": "No especificado",
                "profesion": "No especificado",
                "experiencia": "No especificado",
                "educacion": "No especificado",
                "tecnologias": "No especificado",
                "idiomas": "No especificado",
                "logros": "No especificado",
                "habilidades_blandas": "No especificado"
            }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "error": f"Error al procesar con Gemini: {str(e)}",
            "nombre": "No especificado",
            "profesion": "No especificado",
            "experiencia": "No especificado",
            "educacion": "No especificado",
            "tecnologias": "No especificado",
            "idiomas": "No especificado",
            "logros": "No especificado",
            "habilidades_blandas": "No especificado"
        }, ensure_ascii=False)

def generate_cv_profile(transcription, profile_dict):
    """Genera un perfil profesional para hoja de vida usando Gemini AI"""
    if not GEMINI_AVAILABLE:
        return "ADVERTENCIA: Google Generative AI no esta instalado. Instala con: pip install google-generativeai"

    prompt = (
        "Con base en la siguiente transcripción de un video de presentación personal y la información extraída del perfil, "
        "redacta un perfil profesional completo y atractivo para una hoja de vida. El perfil debe ser en español, "
        "profesional, persuasivo y formal, escrito en tercera persona, conciso pero informativo, como un resumen ejecutivo impactante para un currículum vitae. "
        "Estructúralo en uno o dos párrafos conectados, integrando toda la información relevante de manera natural, fluida y coherente, "
        "usando conectores lógicos y transiciones suaves. Comienza con el nombre, profesión y experiencia clave, luego educación, tecnologías, idiomas, logros y habilidades blandas si están disponibles. "
        "Hazlo sonar motivador y profesional, destacando fortalezas y potencial.\n\n"
        f"Transcripción: {transcription}\n\n"
        f"Información extraída: {json.dumps(profile_dict, ensure_ascii=False)}\n\n"
        "Ejemplo mejorado: 'Elier Fernando Rosero Bravo es un Contador Público altamente experimentado con más de 5 años de trayectoria en el sector contable y docente. Posee una Maestría en Gerencia y Auditoría Tributaria, y actualmente se especializa en Ingeniería de Software. Domina tecnologías como Python, Laravel y Spring Boot, además de hablar español nativo e inglés básico. Se destaca por su capacidad para el trabajo en equipo y su compromiso con la excelencia profesional.'\n\n"
        "Si algún dato no está disponible o es 'No especificado', intégralo de manera que suene natural o omítelo si no es esencial. "
        "No uses formato Markdown, placeholders como '(Por favor, añadir...)' ni texto adicional fuera del perfil. "
        "El perfil debe ser objetivo, profesional y atractivo para reclutadores."
    )

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error al generar perfil profesional: {str(e)}"
