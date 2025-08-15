# 🤖🎙️ Voice Agent – Your AI-Powered Conversational Assistant  

> 🚀 **Part of my 30 Days of AI Voice Agents Challenge** – A smart, voice-controlled AI assistant powered by **MURF AI**, **AssemblyAI**, and **Google Gemini API**. Talk to it, and it talks back – just like chatting with a friend!  

---

## ✨ **What is Voice Agent?**  
The **Voice Agent** listens to your voice 🎤, understands your question 🧠, and responds with natural speech 🔊.  
It combines **Speech-to-Text (STT)**, **Large Language Models (LLM)**, and **Text-to-Speech (TTS)** in one seamless, interactive application.  

---

## 🌟 **Key Features**  

- 🎙️ **Real-Time Conversation** – Ask questions, get instant answers.  
- 🗣️ **Speech-to-Text** – Powered by **AssemblyAI** for accurate transcription.  
- 🔊 **Text-to-Speech** – Uses **Web Speech API** for lifelike voice output.  
- 💬 **Chat History** – Keeps track of the entire conversation.  
- 🎨 **Modern UI** – Beautiful, responsive, and mobile-friendly with Tailwind CSS.  
- 🛡️ **Robust Error Handling** – Gracefully manages API failures.  

---

## 🛠 **Tech Stack**  

**Frontend**:  
- HTML, CSS, JavaScript  
- Tailwind CSS 🎨  

**Backend**:  
- Python (Flask) 🐍  
- Murf AI Integration  

**APIs**:  
- [AssemblyAI](https://www.assemblyai.com/) – Speech-to-Text  
- [Google Gemini API](https://ai.google/) – Conversational AI  
- Web Speech API – Text-to-Speech  

---

## 🧠 **How It Works**  

```mermaid
sequenceDiagram
    participant User
    participant Browser
    participant AssemblyAI
    participant Gemini
    participant WebSpeechAPI

    User->>Browser: 🎤 Record voice
    Browser->>AssemblyAI: Send audio for transcription
    AssemblyAI-->>Browser: Return transcribed text
    Browser->>Gemini: Send text + chat history
    Gemini-->>Browser: Return AI response
    Browser->>WebSpeechAPI: Convert text to speech
    Browser-->>User: 🔊 Play audio response
