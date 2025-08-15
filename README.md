
# 🎙️ Voice Agent

An intelligent voice-based AI assistant that can transcribe speech, understand context, and respond back with synthesized voice — powered by **AssemblyAI**, **Google Gemini**, and **Web Speech API**.

---

## 🚀 Features
- 🎤 **Voice Input** — Speak naturally, and the agent will listen.
- ✍️ **Real-time Transcription** — Converts speech to text with **AssemblyAI**.
- 🤖 **AI-Powered Responses** — Uses **Google Gemini** for contextual and intelligent answers.
- 🔊 **Text-to-Speech** — Speaks responses back using **Web Speech API**.
- 🌐 **Browser-Based** — No installation required for end users beyond a modern browser.

---

## 🧠 How It Works

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
````



## 📸 Screenshots

**Conversation View**
![Conversation View](https://github.com/PAYALTIWARI11/Voice-Agent/blob/main/Screenshot%202025-08-15%20122558.png)

**Voice Agent Panel**
![Voice Agent Panel](https://github.com/PAYALTIWARI11/Voice-Agent/blob/main/Screenshot%202025-08-09%20002950.png)


## ⚙️ Installation & Setup

### 1️⃣ Prerequisites

* A modern browser with microphone access.
* API keys for:

  * **AssemblyAI**
  * **Google Gemini**

---

### 2️⃣ Clone the Repository

```bash
git clone https://github.com/PAYALTIWARI11/Voice-Agent.git
cd Voice-Agent
```

---

### 3️⃣ Install Dependencies

```bash
pip install -r requirement.txt
```

---

### 4️⃣ Configure API Keys

Open `index.html` and replace:

```javascript
const GEMINI_API_KEY = "YOUR_GEMINI_API_KEY";
const ASSEMBLYAI_API_KEY = "YOUR_ASSEMBLYAI_API_KEY";
```

---

### 5️⃣ Run the Project

```bash
python app.py
```

Then open the provided link in your browser and **allow microphone access**. 🎤

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!
Feel free to fork the repo and submit pull requests.




## 👩‍💻 Author

**Payal Tiwari**
📧 \[2payaltiwari@gmail.coml]
🌐 \[https://www.linkedin.com/in/payal-tiwari-428785240/]




