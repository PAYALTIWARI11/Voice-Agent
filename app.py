import os
import requests
import json
import asyncio
import httpx
from fastapi import FastAPI, HTTPException, Request, Response, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import aiofiles
import assemblyai as aai
import base64
import struct

# --- API Keys ---
# Using AssemblyAI for transcription, and Gemini for text generation and TTS.
GEMINI_API_KEY = "AIzaSyDbfrWHOC0aNXbG3fAwU_kPYxDW67LxLEw"
ASSEMBLYAI_API_KEY = "661f2c6b775c428e8f9647c97314d502"

# --- Configuration ---
if not GEMINI_API_KEY or GEMINI_API_KEY == "INSERT_YOUR_GEMINI_API_KEY_HERE":
    print("FATAL ERROR: Gemini API Key is missing. Please replace the placeholder.")
if not ASSEMBLYAI_API_KEY or ASSEMBLYAI_API_KEY == "INSERT_YOUR_ASSEMBLYAI_API_KEY_HERE":
    print("FATAL ERROR: AssemblyAI API Key is missing. Please replace the placeholder.")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

aai.settings.api_key = ASSEMBLYAI_API_KEY

app = FastAPI()

# --- CORS Middleware Configuration ---
origins = ["*"] 
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

if not os.path.isdir(TEMPLATES_DIR):
    print(f"Warning: 'templates' directory not found at {TEMPLATES_DIR}. Please create it and place index.html inside.")

app.mount("/static", StaticFiles(directory=BASE_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

class ChatRequest(BaseModel):
    message: str

# Helper function to convert PCM data to WAV format
def pcm_to_wav(pcm_data, sample_rate=16000):
    """Converts PCM audio data to a WAV file byte stream."""
    header = b'RIFF'
    header += struct.pack('<I', 36 + len(pcm_data))
    header += b'WAVE'
    header += b'fmt '
    header += struct.pack('<I', 16)
    header += struct.pack('<H', 1) # PCM format
    header += struct.pack('<H', 1) # Mono channel
    header += struct.pack('<I', sample_rate)
    header += struct.pack('<I', sample_rate * 2) # byte rate
    header += struct.pack('<H', 2) # block align
    header += struct.pack('<H', 16) # bits per sample
    header += b'data'
    header += struct.pack('<I', len(pcm_data))
    return header + pcm_data

# Gemini TTS function
async def generate_gemini_audio(text: str) -> bytes:
    """
    Generates audio from text using the Gemini Text-to-Speech API.
    The API returns raw PCM data, which needs to be converted to WAV format.
    """
    if not text:
        raise ValueError("Text for TTS cannot be empty.")
    
    # Corrected payload structure: The 'responseModality' key is removed,
    # as the model's name implies the audio output.
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": text}
                ]
            }
        ],
        "generationConfig": {
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": "Kore"
                    }
                }
            }
        }
    }
    
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={GEMINI_API_KEY}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(api_url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            part = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0]
            audio_data = part.get('inlineData', {}).get('data')
            
            if not audio_data:
                raise HTTPException(status_code=500, detail="Gemini TTS did not return audio data.")
            
            pcm_data = base64.b64decode(audio_data)
            
            return pcm_to_wav(pcm_data, sample_rate=16000)

        except httpx.HTTPStatusError as e:
            print(f"Gemini TTS API error: {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail=f"Gemini TTS API Error: {e.response.text}")
        except Exception as e:
            print(f"An unexpected error occurred during Gemini TTS: {e}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.get("/", response_class=HTMLResponse)
async def serve_app(request: Request):
    """
    Serves the main HTML page.
    """
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        print(f"Error rendering index.html: {e}")
        return HTMLResponse(content=f"Error loading page: {e}", status_code=500)

@app.post("/llm/query")
async def llm_query(audio_file: UploadFile = File(...)):
    """
    (Day 9: Full Non-Streaming Pipeline with Gemini TTS)
    1. Accepts audio input from the user.
    2. Transcribes the audio using AssemblyAI.
    3. Sends the transcription to the Gemini LLM to generate a response.
    4. Sends the LLM's text response to Gemini TTS to generate audio.
    5. Returns the final Gemini-generated audio file.
    """
    print("Received audio file for full non-streaming pipeline.")
    try:
        # Step 1: Transcribe the incoming audio using AssemblyAI
        audio_data = await audio_file.read()
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_data)

        if transcript.status == aai.TranscriptStatus.error:
            raise HTTPException(status_code=500, detail=f"Transcription failed: {transcript.error}")
        
        transcribed_text = transcript.text.strip() if transcript and transcript.text else ""
        print(f"Transcription successful: '{transcribed_text}'")

        if not transcribed_text:
            raise HTTPException(status_code=400, detail="Transcription was empty. Please speak clearly before stopping the recording.")
        
        # Step 2: Send the transcription to the Gemini LLM
        print(f"Sending to Gemini LLM: '{transcribed_text}'")
        response_stream = model.generate_content(transcribed_text, stream=True)
        llm_response_text = ""
        for chunk in response_stream:
            llm_response_text += chunk.text
        
        cleaned_llm_response = llm_response_text.strip()
        print(f"Received LLM response: '{cleaned_llm_response}'")

        # Step 3: Send the LLM's response to Gemini TTS to generate audio
        print(f"Sending LLM response to Gemini for TTS...")
        tts_audio_data = await generate_gemini_audio(cleaned_llm_response)
        print("Gemini audio generation successful.")

        # Step 4: Return the audio file to the client
        return StreamingResponse(
            content=iter([tts_audio_data]),
            media_type="audio/wav"
        )

    except HTTPException as e:
        print(f"Error in /llm/query pipeline: {e.detail}")
        raise e
    except Exception as e:
        print(f"An unexpected error occurred in /llm/query: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    import uvicorn
    if "INSERT_YOUR_ASSEMBLYAI_API_KEY_HERE" in ASSEMBLYAI_API_KEY or "INSERT_YOUR_GEMINI_API_KEY_HERE" in GEMINI_API_KEY:
        print("Please set your AssemblyAI and Gemini API keys before running the application.")
    else:
        uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
