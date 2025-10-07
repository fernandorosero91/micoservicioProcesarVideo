from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
import shutil
import subprocess
import tempfile
import os
import json
from groq_service import transcribe_audio, extract_profile, generate_cv_profile

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def get_upload_form():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Subir Video - API JSON</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .info { background: #e8f4fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
            pre { background: #f5f5f5; padding: 10px; border-radius: 3px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <h1>🎥 Extracción de Perfil desde Videos</h1>

        <div class="info">
            <h3>📋 Esta API devuelve respuestas en formato JSON</h3>
            <p>La aplicación procesa videos y devuelve:</p>
            <pre>{
  "transcripcion": "Perfil profesional redactado para hoja de vida",
  "perfil": {
    "nombre": "Nombre extraído",
    "profesion": "Profesión/ocupación",
    "experiencia": "Años y áreas de experiencia",
    "educacion": "Formación académica",
    "tecnologias": "Herramientas y tecnologías",
    "idiomas": "Idiomas hablados",
    "logros": "Reconocimientos y logros",
    "habilidades_blandas": "Habilidades personales"
  }
}</pre>
        </div>

        <form action="/upload-video" method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept="video/*" required>
            <button type="submit">📤 Subir y Procesar Video</button>
        </form>

        <p><em>Nota: Usa herramientas como Postman, curl o el inspector del navegador para ver la respuesta JSON completa.</em></p>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):
    try:
        # 1. Guardar video temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video_file:
            temp_video = temp_video_file.name
            shutil.copyfileobj(file.file, temp_video_file)

        # 2. Extraer audio con FFmpeg
        audio_file = temp_video.replace('.mp4', '.wav')

        subprocess.run([
            "ffmpeg", "-i", temp_video, "-vn", "-acodec", "pcm_s16le",
            "-ar", "16000", "-ac", "1", audio_file
        ], check=True)

        # 3. Transcribir audio
        transcription = transcribe_audio(audio_file)

        # 4. Extraer perfil
        profile_json = extract_profile(transcription)
        try:
            profile = json.loads(profile_json)
        except json.JSONDecodeError:
            profile = {"error": "No se pudo parsear el perfil JSON", "raw": profile_json}

        # 5. Generar perfil profesional para hoja de vida
        cv_profile = generate_cv_profile(transcription, profile)

        # Limpiar archivos temporales
        os.unlink(temp_video)
        os.unlink(audio_file)

        # Crear respuesta JSON
        response_data = {
            "transcripcion": cv_profile,
            "perfil": profile
        }

        return response_data

    except Exception as e:
        import traceback
        return HTMLResponse(content=f"<h1>Error</h1><pre>{traceback.format_exc()}</pre><a href='/'>Volver</a>", status_code=500)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 9000))
    uvicorn.run(app, host="0.0.0.0", port=port)
