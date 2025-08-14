🎯 30 Days of AI Voice Agents

Welcome to Day 12 of the 30 Days of AI Voice Agents Challenge!
This project is part of a daily build series aimed at creating a functional, user-friendly, and robust voice-controlled AI assistant.

The agent combines Speech-to-Text (STT) and a Large Language Model (LLM) to engage in natural, conversational interactions with the user.

✨ Features

🎙️ Conversational Interface – Listens to user input, processes it, and responds naturally.

🗣️ Real-time Text-to-Speech – Uses the browser's native TTS for quick audio responses.

💬 Chat History – Maintains a full session history for context-aware conversations.

✅ Robust Error Handling – try...catch blocks ensure graceful handling of API failures with friendly fallback messages.

🎨 Revamped UI – Clean, modern, responsive interface with a single smart record button.

🛠️ Technologies Used
Frontend

HTML, CSS, JavaScript – Core structure and logic.

Tailwind CSS – For responsive and modern styling.

APIs

AssemblyAI – High-quality Speech-to-Text (STT) transcription.

Google Gemini API – The LLM providing conversational intelligence.

Web Speech API – Native browser Text-to-Speech (TTS).

🧠 Architecture

Flow Overview:

User Input – The microphone captures audio when the record button is tapped.

Transcription – Audio is sent to AssemblyAI for transcription into text.

LLM Processing – Transcribed text + chat history sent to Gemini API.

Response Generation – Gemini API returns a natural language response.

Audio Output – Web Speech API converts the response to speech and plays it back.

💡 Error Handling:
All API calls are wrapped in try...catch blocks. If any service fails, the app returns a friendly fallback message instead of breaking.

🚀 Setup & Running the Application
Prerequisites

Modern web browser (Chrome, Firefox, Edge, Safari) with microphone access.

API keys for AssemblyAI and Google Gemini.

Configuration

Open index.html in your code editor.

Locate the // API Configuration section in the <script> tag.

Replace placeholder values with your API keys:

const GEMINI_API_KEY = "YOUR_GEMINI_API_KEY";
const ASSEMBLYAI_API_KEY = "YOUR_ASSEMBLYAI_API_KEY";

Running the Code

Open index.html in your preferred browser.

Grant microphone access when prompted.

Tap the record button 🎤 to start interacting with the AI agent.
