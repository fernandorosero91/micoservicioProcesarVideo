from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
import shutil
import subprocess
import tempfile
import os
import json
from groq_service import transcribe_audio, extract_profile

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
  "transcripcion": "Texto transcrito del video",
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

        # Limpiar archivos temporales
        os.unlink(temp_video)
        os.unlink(audio_file)

        # Crear respuesta JSON
        response_data = {
            "transcripcion": transcription,
            "perfil": profile
        }

        # Formatear respuesta JSON para mostrar en HTML
        import json as json_module
        formatted_json = json_module.dumps(response_data, ensure_ascii=False, indent=2)

        # Crear HTML para mostrar el JSON formateado
        html_response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Resultado - JSON API</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background: #f8f9fa;
                }}
                .container {{
                    background: white;
                    border-radius: 10px;
                    padding: 30px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #2c3e50;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .section {{
                    margin-bottom: 30px;
                    border-left: 4px solid #3498db;
                    padding-left: 20px;
                }}
                .section h2 {{
                    color: #34495e;
                    margin-top: 0;
                    font-size: 1.4em;
                }}
                .json-container {{
                    background: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 5px;
                    padding: 20px;
                    font-family: 'Courier New', monospace;
                    font-size: 14px;
                    line-height: 1.4;
                    overflow-x: auto;
                    white-space: pre-wrap;
                }}
                .transcription {{
                    background: #e8f8f5;
                    border-left-color: #27ae60;
                }}
                .profile {{
                    background: #fef5e7;
                    border-left-color: #f39c12;
                }}
                .back-link {{
                    display: inline-block;
                    margin-top: 20px;
                    padding: 10px 20px;
                    background: #3498db;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    transition: background 0.3s;
                }}
                .back-link:hover {{
                    background: #2980b9;
                }}
                .status {{
                    padding: 10px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                    font-weight: bold;
                }}
                .status.success {{
                    background: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎯 Resultado de Extracción - API JSON</h1>

                <div class="status success">
                    ✅ Video procesado exitosamente - Respuesta JSON generada
                </div>

                <div class="section transcription">
                    <h2>📝 Transcripción del Audio</h2>
                    <div class="json-container">
{json_module.dumps({"transcripcion": transcription}, ensure_ascii=False, indent=2)}
                    </div>
                </div>

                <div class="section profile">
                    <h2>👤 Perfil Extraído</h2>
                    <div class="json-container">
{json_module.dumps({"perfil": profile}, ensure_ascii=False, indent=2)}
                    </div>
                </div>

                <div class="section">
                    <h2>🔧 Respuesta JSON Completa</h2>
                    <div class="json-container">
{formatted_json}
                    </div>
                </div>

                <a href="/" class="back-link">⬅️ Subir otro video</a>
            </div>
        </body>
        </html>
        """

        return HTMLResponse(content=html_response)

    except Exception as e:
        import traceback
        return HTMLResponse(content=f"<h1>Error</h1><pre>{traceback.format_exc()}</pre><a href='/'>Volver</a>", status_code=500)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 9000))
    uvicorn.run(app, host="0.0.0.0", port=port)
