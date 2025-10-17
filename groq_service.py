import os
import json
from dotenv import load_dotenv

load_dotenv()

# Configurar Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY no encontrada en el archivo .env")

print(f"Groq API Key loaded: {GROQ_API_KEY[:10]}...")

# Intentar importar y configurar Groq
try:
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    GROQ_AVAILABLE = True
    print("Groq AI configurado correctamente")
except ImportError as e:
    print(f"ADVERTENCIA: Groq no esta instalado: {e}")
    print("Instala con: pip install groq")
    GROQ_AVAILABLE = False
    client = None
except Exception as e:
    print(f"Error al configurar Groq: {e}")
    GROQ_AVAILABLE = False
    client = None

# Configurar Gemini como respaldo
if not GEMINI_API_KEY:
    print("GEMINI_API_KEY no encontrada, usando solo Groq")
    GEMINI_AVAILABLE = False
    model = None
else:
    print(f"Gemini API Key loaded: {GEMINI_API_KEY[:10]}...")
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)

        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            GEMINI_AVAILABLE = True
            print("Gemini AI configurado correctamente con gemini-2.0-flash")
        except Exception as e:
            print(f"Error al configurar Gemini: {e}")
            try:
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
    """Transcribe audio usando Groq AI (Whisper)"""
    if not GROQ_AVAILABLE:
        if GEMINI_AVAILABLE:
            print("Groq no disponible, usando Gemini como respaldo")
            return transcribe_audio_gemini(audio_path)
        return "ADVERTENCIA: Ni Groq ni Gemini están disponibles para transcripción."

    try:
        print(f"Transcribiendo audio con Groq: {audio_path}")
        with open(audio_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(audio_path, file.read()),
                model="whisper-large-v3",
                prompt="Transcribe este audio al español. Es una presentación personal o profesional.",
                response_format="text",
                language="es"
            )
        print(f"Transcripción obtenida con Groq: {transcription[:200]}...")
        return transcription.strip() if transcription else "No se pudo transcribir el audio."

    except Exception as e:
        print(f"Error en transcribe_audio con Groq: {str(e)}")
        if GEMINI_AVAILABLE:
            print("Intentando con Gemini como respaldo...")
            return transcribe_audio_gemini(audio_path)
        return f"Error al transcribir: {str(e)}"

def transcribe_audio_gemini(audio_path):
    """Transcribe audio usando Gemini AI como respaldo"""
    if not GEMINI_AVAILABLE:
        return "ADVERTENCIA: Google Generative AI no esta instalado."

    try:
        # Subir el archivo de audio a Gemini
        audio_file = genai.upload_file(audio_path)
        print(f"Archivo de audio subido a Gemini: {audio_file.name}")

        # Transcribir usando Gemini con el archivo subido
        response = model.generate_content([
            "Transcribe este audio al español. Proporciona únicamente la transcripción del habla, sin comentarios adicionales ni formato especial.",
            audio_file
        ])

        transcription = response.text.strip()
        print(f"Transcripción obtenida con Gemini: {transcription[:200]}...")
        return transcription if transcription else "No se pudo transcribir el audio."

    except Exception as e:
        print(f"Error en transcribe_audio_gemini: {str(e)}")
        return f"Error al transcribir con Gemini: {str(e)}"

def extract_profile(text):
    """Extrae información del perfil usando Groq AI"""
    import json

    print(f"Texto recibido para extracción de perfil: {text[:500]}...")

    if not GROQ_AVAILABLE:
        if GEMINI_AVAILABLE:
            print("Groq no disponible, usando Gemini como respaldo")
            return extract_profile_gemini(text)
        return json.dumps({
            "error": "ADVERTENCIA: Ni Groq ni Gemini están disponibles.",
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
        print("Enviando prompt a Groq para extracción de perfil...")
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Eres un asistente que extrae información de perfiles profesionales de textos transcritos. Siempre respondes solo con JSON válido."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1000
        )
        response_text = response.choices[0].message.content.strip()
        print(f"Respuesta de Groq para perfil: {response_text[:500]}...")

        # Intentar parsear el JSON de la respuesta
        import re

        # Extraer JSON de la respuesta
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            # Validar que sea JSON válido
            parsed = json.loads(json_str)
            print(f"Perfil extraído exitosamente: {json.dumps(parsed, ensure_ascii=False)}")
            return json.dumps(parsed, ensure_ascii=False)
        else:
            print("No se encontró JSON en la respuesta de Groq")
            if GEMINI_AVAILABLE:
                print("Intentando con Gemini como respaldo...")
                return extract_profile_gemini(text)
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
        print(f"Error en extract_profile con Groq: {str(e)}")
        if GEMINI_AVAILABLE:
            print("Intentando con Gemini como respaldo...")
            return extract_profile_gemini(text)
        return json.dumps({
            "error": f"Error al procesar: {str(e)}",
            "nombre": "No especificado",
            "profesion": "No especificado",
            "experiencia": "No especificado",
            "educacion": "No especificado",
            "tecnologias": "No especificado",
            "idiomas": "No especificado",
            "logros": "No especificado",
            "habilidades_blandas": "No especificado"
        }, ensure_ascii=False)

def extract_profile_gemini(text):
    """Extrae información del perfil usando Gemini AI como respaldo"""
    import json

    if not GEMINI_AVAILABLE:
        return json.dumps({
            "error": "ADVERTENCIA: Google Generative AI no esta instalado.",
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
        print("Enviando prompt a Gemini para extracción de perfil...")
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        print(f"Respuesta de Gemini para perfil: {response_text[:500]}...")

        # Intentar parsear el JSON de la respuesta
        import re

        # Extraer JSON de la respuesta
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            # Validar que sea JSON válido
            parsed = json.loads(json_str)
            print(f"Perfil extraído exitosamente con Gemini: {json.dumps(parsed, ensure_ascii=False)}")
            return json.dumps(parsed, ensure_ascii=False)
        else:
            print("No se encontró JSON en la respuesta de Gemini")
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
        print(f"Error en extract_profile_gemini: {str(e)}")
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
    """Genera un perfil profesional para hoja de vida usando Groq AI"""
    print(f"Generando perfil CV con transcripción: {transcription[:300]}...")
    print(f"Perfil dict: {json.dumps(profile_dict, ensure_ascii=False)}")

    if not GROQ_AVAILABLE:
        if GEMINI_AVAILABLE:
            print("Groq no disponible, usando Gemini como respaldo")
            return generate_cv_profile_gemini(transcription, profile_dict)
        return "ADVERTENCIA: Ni Groq ni Gemini están disponibles para generar perfil."

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
        print("Enviando prompt a Groq para generar perfil CV...")
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Eres un asistente especializado en crear perfiles profesionales para hojas de vida. Genera textos persuasivos y profesionales en español."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        cv_profile = response.choices[0].message.content.strip()
        print(f"Perfil CV generado con Groq: {cv_profile[:300]}...")
        return cv_profile
    except Exception as e:
        print(f"Error en generate_cv_profile con Groq: {str(e)}")
        if GEMINI_AVAILABLE:
            print("Intentando con Gemini como respaldo...")
            return generate_cv_profile_gemini(transcription, profile_dict)
        return f"Error al generar perfil profesional: {str(e)}"

def generate_cv_profile_gemini(transcription, profile_dict):
    """Genera un perfil profesional para hoja de vida usando Gemini AI como respaldo"""
    if not GEMINI_AVAILABLE:
        return "ADVERTENCIA: Google Generative AI no esta instalado."

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
        print("Enviando prompt a Gemini para generar perfil CV...")
        response = model.generate_content(prompt)
        cv_profile = response.text.strip()
        print(f"Perfil CV generado con Gemini: {cv_profile[:300]}...")
        return cv_profile
    except Exception as e:
        print(f"Error en generate_cv_profile_gemini: {str(e)}")
        return f"Error al generar perfil profesional: {str(e)}"
