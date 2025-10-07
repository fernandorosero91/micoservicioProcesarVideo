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
        "redacta un perfil profesional optimizado para una hoja de vida en el estilo de resúmenes ejecutivos concisos y impactantes. El perfil debe ser en español, "
        "profesional y formal, escrito en tercera persona impersonal (sin mencionar el nombre al inicio), estructurado en párrafos cortos y enfocados. "
        "Sigue esta estructura aproximada: "
        "- Primer párrafo: Profesión y experiencia clave, destacando especialidades y áreas de dominio. "
        "- Segundo párrafo: Formación académica y conocimientos técnicos/tecnologías. "
        "- Tercer párrafo: Capacidades, idiomas y habilidades blandas. "
        "- Cuarto párrafo: Reconocimientos, logros y compromiso profesional. "
        "Usa frases impactantes, lenguaje persuasivo y evita redundancias. Integra toda la información relevante de manera coherente.\n\n"
        f"Transcripción: {transcription}\n\n"
        f"Información extraída: {json.dumps(profile_dict, ensure_ascii=False)}\n\n"
        "Ejemplo de estilo: 'Físico Nuclear con sólida experiencia en fisión nuclear, seguridad de plantas y análisis de riesgos operativos. Formación en Ingeniería Nuclear, con dominio de procesos de energía nuclear, control radiológico y sistemas de protección. Capacidad comprobada para trabajar en entornos multidisciplinarios y colaborar en proyectos internacionales gracias a la fluidez en francés y ruso. Reconocido por su escucha activa, comunicación efectiva y disposición al aprendizaje continuo. Comprometido con la excelencia técnica, la innovación científica y la seguridad operacional, orientado a contribuir al desarrollo y mejora de proyectos en el sector energético y nuclear.'\n\n"
        "Si algún dato no está disponible o es 'No especificado', intégralo sutilmente o omítelo si no aporta valor. "
        "No uses formato Markdown, placeholders ni texto adicional fuera del perfil. "
        "El perfil debe ser conciso, persuasivo y adecuado para un CV profesional."
    )

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error al generar perfil profesional: {str(e)}"
