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
import aiofiles # Import aiofiles for asynchronous file operations

# --- API Keys ---
# IMPORTANT: Replace these with your actual API keys.
# You can get a Gemini API key from Google AI Studio.
# You can get a Murf.ai API key from your Murf.ai dashboard.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDbfrWHOC0aNXbG3fAwU_kPYxDW67LxLEw")
MURF_API_KEY = os.environ.get("MURF_API_KEY", "ap2_9a9ae282-4002-4556-be2d-6c7b6b0fc95d")

# --- Configuration ---
# Configure the Gemini API client
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Murf.ai API details
MURF_API_URL = "https://api.murf.ai/v1/speech/stream"
VOICE_ID = "en-US-natalie" 
VOICE = "Natalie"

app = FastAPI()

# --- FIX START ---
# Get the absolute path to the directory where app.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# CORRECTED: Now explicitly points to the 'templates' subdirectory
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads") # Ensure uploads directory is also relative to app.py

# Ensure the 'templates' directory actually exists
if not os.path.isdir(TEMPLATES_DIR):
    print(f"Warning: 'templates' directory not found at {TEMPLATES_DIR}. Please create it and place index.html inside.")

# Mount a directory for static files (our HTML, JS, CSS)
# This serves files from the BASE_DIR, so if you were to access /static/templates/index.html it would work
# But we are serving index.html via Jinja2Templates for the root path.
app.mount("/static", StaticFiles(directory=BASE_DIR), name="static")

# Jinja2 for template rendering (used to serve index.html for the root path)
# Now explicitly tells Jinja2 to look in the 'templates' directory
templates = Jinja2Templates(directory=TEMPLATES_DIR)
# --- FIX END ---

# Pydantic model for our API request body (for chat endpoint)
class ChatRequest(BaseModel):
    message: str

# --- API Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def serve_app(request: Request):
    """
    Serves the main HTML page for the conversational agent.
    """
    print(f"Attempting to serve index.html from template directory: {TEMPLATES_DIR}") # Debug log
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        # Catch Jinja2 TemplateNotFound specifically, or any other rendering error
        print(f"Error rendering index.html: {e}")
        # Provide a more informative error message to the user
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

@app.post("/upload-audio/")
async def upload_audio(audio_file: UploadFile = File(...)):
    """
    Receives an audio file from the frontend, saves it temporarily,
    and returns its metadata.
    """
    os.makedirs(UPLOADS_DIR, exist_ok=True) # Create uploads directory if it doesn't exist

    file_location = os.path.join(UPLOADS_DIR, audio_file.filename)
    
    try:
        async with aiofiles.open(file_location, "wb") as f:
            while contents := await audio_file.read(1024): # Read in chunks
                await f.write(contents)
        
        file_size = os.path.getsize(file_location)

        print(f"Received file: {audio_file.filename}, Type: {audio_file.content_type}, Size: {file_size} bytes")

        return {
            "filename": audio_file.filename,
            "content_type": audio_file.content_type,
            "file_size": file_size,
            "message": "File uploaded successfully!"
        }
    except Exception as e:
        print(f"Error saving file: {e}")
        raise HTTPException(status_code=500, detail=f"Could not upload file: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
