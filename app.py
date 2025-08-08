import os
import requests
import json
import asyncio
import httpx
from fastapi import FastAPI, HTTPException, Request, Response, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from google.generativeai.types import GenerateContentResponse
import google.generativeai as genai
import aiofiles
import assemblyai as aai # Import AssemblyAI SDK

# --- API Keys ---
# IMPORTANT: Replace these with your actual API keys.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "ap2_9a9ae282-4002-4556-be2d-6c7b6b0fc95d")
MURF_API_KEY = os.environ.get("MURF_API_KEY", "AIzaSyDbfrWHOC0aNXbG3fAwU_kPYxDW67LxLEw")
# Day 6: AssemblyAI API Key
ASSEMBLYAI_API_KEY = os.environ.get("ASSEMBLYAI_API_KEY", "661f2c6b775c428e8f9647c97314d502")

# --- Configuration ---
# Configure the Gemini API client
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Murf.ai API details
MURF_API_URL = "https://api.murf.ai/v1/speech/stream"
VOICE_ID = "en-US-natalie" 
VOICE = "Natalie"

# AssemblyAI API details
aai.settings.api_key = ASSEMBLYAI_API_KEY

app = FastAPI()

# Get the absolute path to the directory where app.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

if not os.path.isdir(TEMPLATES_DIR):
    print(f"Warning: 'templates' directory not found at {TEMPLATES_DIR}. Please create it and place index.html inside.")

app.mount("/static", StaticFiles(directory=BASE_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Pydantic model for our API request body (for chat endpoint)
class ChatRequest(BaseModel):
    message: str

# --- API Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def serve_app(request: Request):
    """
    Serves the main HTML page for the conversational agent.
    """
    print(f"Attempting to serve index.html from template directory: {TEMPLATES_DIR}")
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        print(f"Error rendering index.html: {e}")
        return HTMLResponse(content=f"""
            <html>
                <head>
                    <title>Error Loading Page</title>
                </head>
                <body>
                    <h1>Internal Server Error</h1>
                    <p>There was a problem loading the page. The server could not find 'index.html'.</p>
                    <p>Please ensure 'index.html' is in the <b>'{os.path.basename(TEMPLATES_DIR)}'</b> directory, which should be inside the same folder as 'app.py'.</p>
                    <p>Server tried to find template in: <code>{TEMPLATES_DIR}</code></p>
                    <p>Details: {e}</p>
                </body>
            </html>
        """, status_code=500)

@app.post("/chat")
async def chat_with_agent(chat_request: ChatRequest):
    """
    Handles the conversational logic (from Day 4).
    1. Sends the user's message to the Gemini API.
    2. Takes Gemini's response and sends it to the Murf.ai API.
    3. Streams the audio back to the client.
    """
    try:
        # Step 1: Send the user's message to the Gemini API
        print(f"User message: {chat_request.message}")
        
        gemini_response_text = ""
        response_stream = model.generate_content(chat_request.message, stream=True)
        for chunk in response_stream:
            gemini_response_text += chunk.text

        print(f"Gemini response: {gemini_response_text}")

        # Step 2: Use the Gemini response text to call the Murf.ai TTS API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {MURF_API_KEY}"
        }
        
        murf_payload = {
            "voiceId": VOICE_ID,
            "text": gemini_response_text
        }

        async with httpx.AsyncClient() as client:
            murf_response = await client.post(
                MURF_API_URL, 
                headers=headers, 
                json=murf_payload, 
                timeout=60.0
            )

        murf_response.raise_for_status()

        async def audio_streamer():
            async for chunk in murf_response.aiter_bytes():
                yield chunk

        return StreamingResponse(audio_streamer(), media_type="audio/mpeg")

    except genai.APIError as e:
        print(f"Gemini API error: {e}")
        raise HTTPException(status_code=500, detail=f"Gemini API error: {e}")
    except httpx.HTTPStatusError as e:
        print(f"Murf.ai API error: {e.response.text}")
        raise HTTPException(status_code=500, detail=f"Murf.ai API error: {e.response.text}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.post("/transcribe/file")
async def transcribe_file(audio_file: UploadFile = File(...)):
    """
    Day 6 Task: Receives an audio file, transcribes it using AssemblyAI,
    and returns the transcription.
    """
    print(f"Received file for transcription: {audio_file.filename}")

    # Read the audio file data directly into memory
    audio_data = await audio_file.read()
    
    try:
        # Pass the binary audio data to the AssemblyAI transcriber
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_data)

        if transcript.status == aai.TranscriptStatus.error:
            raise HTTPException(status_code=500, detail=f"Transcription failed: {transcript.error}")

        print(f"Transcription successful: {transcript.text}")
        return {"transcription": transcript.text}

    except Exception as e:
        print(f"An error occurred during transcription: {e}")
        raise HTTPException(status_code=500, detail=f"Could not transcribe file: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
