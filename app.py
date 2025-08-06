from fastapi import FastAPI
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

# ... other imports and your app = FastAPI() line

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ... the rest of your code

MURF_API_KEY = os.getenv("MURF_API_KEY")  # ✅ Make sure this exists in .env

class TextRequest(BaseModel):
    text: str

@app.post("/generate-voice")
def generate_voice(request: TextRequest):
    url = "https://api.murf.ai/v1/speech/generate"

    payload = {
        "text": request.text,
        "voice_id": "en-IN-priya"  # ✅ Valid voice ID
    }

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "api-key": MURF_API_KEY
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        if "audioFile" in data:
            return {"audio_url": data["audioFile"]}
        else:
            return {"error": "audioFile not found in response.", "response": data}

    except requests.exceptions.RequestException as err:
        return {"error": str(err), "details": response.text if response else "No response received"}
