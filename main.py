from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from gtts import gTTS
import uuid
import os

app = FastAPI()

# CORS for local frontend testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static HTML
app.mount("/", StaticFiles(directory="static", html=True), name="static")
app.mount("/audios", StaticFiles(directory="audios"), name="audios")

@app.post("/generate-voice")
async def generate_voice(request: Request):
    body = await request.json()
    text = body.get("text", "Hello from gTTS!")

    os.makedirs("audios", exist_ok=True)
    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join("audios", filename)

    tts = gTTS(text)
    tts.save(filepath)

    return {
        "audio_url": f"http://localhost:8000/audios/{filename}"
    }
