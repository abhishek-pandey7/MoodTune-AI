# 🎵 MoodTune – Mood to Music Web App

MoodTune is an interactive web application that detects a user’s mood from **voice**, **text**, or **manual selection**, and generates a personalized music playlist using **AI-powered emotion detection** and **Gemini song recommendations**.

---

## ✨ Features

* 🎤 **Voice-based mood detection**

  * Records audio from the browser
  * Converts speech to text using **Vosk**
  * Extracts emotion using **Google Gemini API**

* ✍️ **Text-based mood detection**

  * Users describe their feelings in text
  * Gemini analyzes and returns the dominant emotion

* 🎭 **Quick Mood Picker**

  * Instantly select a mood (Joy, Sadness, Anger, Love, etc.)

* 🎶 **AI-generated playlists**

  * Generates 5 mood-matching songs dynamically
  * Each request returns a fresh set of recommendations

* 🎨 **Animated & immersive UI**

  * Particle effects, gradients, glowing cards
  * Emotion-based backgrounds on playlist page

---

## 🗂️ Project Structure

```
MOODTUNE/
│
├── static/
│   ├── styles.css        # Main landing page styles
│   ├── styles2.css       # Playlist page styles
│   ├── microphone-alt.png
│   ├── pause-circle.png
│   └── (emotion images)
│
├── templates/
│   ├── index.html        # Main mood input page
│   └── index2.html       # Playlist results page
│
├── vosk-model-small-en-us-0.15/  # Speech recognition model
├── app.py                # Flask backend
├── emotion_log.txt       # (Optional) logging
├── .env                  # API keys (not committed)
└── .gitignore
```

---

## 🧠 How It Works

### 1. Voice Input Flow

1. User records voice (10 seconds)
2. Audio is sent to `/upload_audio`
3. Backend:

   * Converts `.webm` → `.wav` using **FFmpeg**
   * Transcribes speech with **Vosk**
   * Sends transcript to **Gemini API**
4. Detected emotion is returned to frontend

### 2. Text Input Flow

1. User types how they feel
2. Sent to `/process_text`
3. Gemini extracts the dominant emotion

### 3. Quick Mood Picker

1. User clicks a mood emoji
2. Backend simply echoes the mood for instant results

### 4. Song Generation

1. Mood is submitted to `/generate_songs`
2. Gemini generates 5 matching songs
3. Songs are rendered on `index2.html`

---

## 🚀 Setup & Installation

### Prerequisites

* Python 3.9+
* FFmpeg installed and accessible in PATH
* Google Gemini API key

### Install Dependencies

```bash
pip install flask vosk python-dotenv google-generativeai requests
```

### Environment Variables

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_api_key_here
```

### Run the App

```bash
python app.py
```

Open your browser at:

```
http://127.0.0.1:5000
```

---

## 🔌 API Endpoints

| Route             | Method | Description             |
| ----------------- | ------ | ----------------------- |
| `/`               | GET    | Home page               |
| `/upload_audio`   | POST   | Voice emotion detection |
| `/process_text`   | POST   | Text emotion detection  |
| `/quick_mood`     | POST   | Manual mood selection   |
| `/generate_songs` | POST   | Playlist generation     |

---

## 🎨 Frontend Technologies

* HTML5 + CSS3 (Glassmorphism UI)
* Vanilla JavaScript
* MediaRecorder API
* Fetch API

---


## ⚠️ Notes & Limitations

* Audio recordings are temporary and deleted after processing
* Requires internet access for Gemini API calls
* Emotion detection depends on speech clarity and text quality

---


## 👨‍💻 Author

Built with ❤️ using Flask, Gemini AI, and Vosk.

Feel free to extend, remix, or enhance MoodTune!
