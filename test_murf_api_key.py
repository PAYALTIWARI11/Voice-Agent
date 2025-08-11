import requests
import json

# --- Test Script Configuration ---
# Replace this with your actual Murf.ai API key.
# This key is the source of the persistent error, so please be sure it's correct.
MURF_API_KEY = "ap2_9a9ae282-4002-4556-be2d-6c7b6b0fc95d" 

# Murf.ai API details for a simple test
MURF_API_URL = "https://api.murf.ai/v1/speech/stream"
VOICE_ID = "en-US-natalie" 
TEST_TEXT = "Hello, this is a test of the Murf API key."

# --- API Call ---
headers = {
    "Content-Type": "application/json",
    "x-api-key": MURF_API_KEY
}

payload = {
    "voiceId": VOICE_ID,
    "text": TEST_TEXT
}

def test_murf_api_key():
    """
    Tests the Murf API key by making a simple TTS request.
    """
    if MURF_API_KEY == "YOUR_MURF_API_KEY" or not MURF_API_KEY:
        print("ERROR: Please replace 'YOUR_MURF_API_KEY' with your actual key before running.")
        return

    print("Attempting to connect to Murf.ai API...")
    try:
        response = requests.post(MURF_API_URL, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("\nSUCCESS! Your API key is working. Status code: 200 OK.")
            print("The Murf API is accepting your key. The issue may be with the `app.py` environment.")
            print("Response size:", len(response.content), "bytes.")
        else:
            print(f"\nFAILURE. The Murf API returned an error: {response.status_code} {response.reason}")
            print(f"Details: {response.text}")
            print("\nThis confirms that the API key is either invalid, expired, or has a different format.")
            print("Please double-check your key in the Murf.ai dashboard and try again.")

    except requests.exceptions.RequestException as e:
        print(f"\nNETWORK ERROR. Could not connect to Murf.ai API: {e}")
        print("This may be a temporary network issue or a DNS problem.")

if __name__ == "__main__":
    test_murf_api_key()
