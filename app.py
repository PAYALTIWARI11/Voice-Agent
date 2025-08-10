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

GEMINI_API_KEY = "AIzaSyDbfrWHOC0aNXbG3fAwU_kPYxDW67LxLEw"
ASSEMBLYAI_API_KEY = "661f2c6b775c428e8f9647c97314d502"

# --- Configuration ---
if not GEMINI_API_KEY or GEMINI_API_KEY == "INSERT_YOUR_GEMINI_API_KEY_HERE":
    print("FATAL ERROR: Gemini API Key is missing. Please replace the placeholder.")
if not ASSEMBLYAI_API_KEY or ASSEMBLYAI_API_KEY == "INSERT_YOUR_ASSEMBLYAI_API_KEY_HERE":
    print("FATAL ERROR: AssemblyAI API Key is missing. Please replace the placeholder.")

genai.configure(api_key=GEMINI_API_KEY)
# We will use gemini-1.5-flash for the chat model
model = genai.GenerativeModel('gemini-1.5-flash')
# And gemini-2.5-flash-preview-tts for the TTS model

# AssemblyAI API details
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


async def generate_gemini_audio(text: str) -> bytes:
    """
    Generates audio from text using the Gemini TTS API.
    Returns the audio data as a bytes object in WAV format.
    """
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {"voiceName": "Kore"}
                }
            }
        },
        "model": "gemini-2.5-flash-preview-tts"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(api_url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            audio_data_b64 = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('inlineData', {}).get('data')
            
            if audio_data_b64:
                pcm_data = base64.b64decode(audio_data_b64)
                wav_data = pcm_to_wav(pcm_data, sample_rate=16000)
                return wav_data
            else:
                raise HTTPException(status_code=500, detail="Gemini TTS API returned no audio data.")

        except httpx.HTTPStatusError as e:
            print(f"Gemini TTS API returned an error: {e}")
            raise HTTPException(status_code=e.response.status_code, detail=f"Gemini API Error: {e.response.text}")
        except Exception as e:
            print(f"An unexpected error occurred in Gemini TTS call: {e}")
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

# --- API Endpoints ---

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

@app.post("/chat")
async def chat_with_agent(chat_request: ChatRequest):
    """
    (Day 4 functionality) Handles a text message, gets a Gemini response,
    and streams back Gemini-generated audio.
    """
    try:
        gemini_response_text = ""
        response_stream = model.generate_content(chat_request.message, stream=True)
        for chunk in response_stream:
            gemini_response_text += chunk.text

        audio_data = await generate_gemini_audio(gemini_response_text)
        
        return StreamingResponse(
            content=iter([audio_data]),
            media_type="audio/wav"
        )

    except Exception as e:
        print(f"An error occurred in /chat: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.post("/transcribe/file")
async def transcribe_file(audio_file: UploadFile = File(...)):
    """
    (Day 6 functionality) Receives an audio file, transcribes it, and returns the transcription.
    """
    try:
        audio_data = await audio_file.read()
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_data)

        if transcript.status == aai.TranscriptStatus.error:
            raise HTTPException(status_code=500, detail=f"Transcription failed: {transcript.error}")

        return {"transcription": transcript.text}

    except Exception as e:
        print(f"An error occurred during transcription: {e}")
        raise HTTPException(status_code=500, detail=f"Could not transcribe file: {e}")

@app.post("/tts/echo")
async def tts_echo(audio_file: UploadFile = File(...)):
    """
    (Day 7 functionality) Echo Bot v2, now with Gemini TTS.
    1. Transcribes incoming audio using AssemblyAI.
    2. Sends the transcription to Gemini TTS to get new audio.
    3. Returns the new Gemini audio and transcription as a JSON object.
    """
    print("Received audio file for Echo Bot v2 processing.")
    try:
        # This will be printed to the console when a file is received
        print("File uploaded successfully.")

        # Step 1: Transcribe the incoming audio
        audio_data = await audio_file.read()
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_data)

        if transcript.status == aai.TranscriptStatus.error:
            raise HTTPException(status_code=500, detail=f"Transcription failed: {transcript.error}")
        
        # Robust check for empty or whitespace-only transcription
        transcribed_text = transcript.text.strip() if transcript and transcript.text else ""
        print(f"Transcription successful: '{transcribed_text}'")

        if not transcribed_text:
            raise HTTPException(status_code=400, detail="Transcription was empty. Please speak clearly before stopping the recording.")
        
        # Log the text being sent to the TTS API for debugging
        print(f"Sending to Gemini TTS: '{transcribed_text}'")

        # Step 2: Generate TTS audio using Gemini
        generated_audio_data = await generate_gemini_audio(transcribed_text)
        
        # Step 3: Prepare the response with transcription and audio
        # Encode the audio data to base64 to include it in the JSON response
        audio_b64 = base64.b64encode(generated_audio_data).decode('utf-8')

        response_content = json.dumps({
            "transcription": transcribed_text,
            "audio": audio_b64
        })

        return Response(content=response_content, media_type="application/json")

    except HTTPException as e:
        # Catch the specific error from the generate_gemini_audio function and re-raise it
        print(f"Error from Gemini TTS: {e.detail}")
        raise e
    except Exception as e:
        print(f"An unexpected error occurred in /tts/echo: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@app.post("/llm/query")
async def llm_query(chat_request: ChatRequest):
    """
    (Day 8 functionality) Accepts text input, queries the Gemini LLM, and returns the response.
    """
    print(f"Received query for LLM: {chat_request.message}")
    try:
        # Generate content from the Gemini LLM
        response_stream = model.generate_content(chat_request.message, stream=True)
        full_response_text = ""
        for chunk in response_stream:
            full_response_text += chunk.text
        
        return {"response": full_response_text}

    except Exception as e:
        print(f"An error occurred in /llm/query: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    import uvicorn
    if "INSERT_YOUR_ASSEMBLYAI_API_KEY_HERE" in ASSEMBLYAI_API_KEY:
        print("Please set your AssemblyAI API key before running the application.")
    else:
        uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
