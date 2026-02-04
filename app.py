import os
import random
import time
import requests
from vosk import Model, KaldiRecognizer
import wave
import google.generativeai as genai
from dotenv import load_dotenv
# Explicitly load .env from the Backend directory
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)
from flask import Flask, request, jsonify, render_template
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


# --- App Setup ---
app = Flask(__name__)

# Directory to save uploaded audio files
UPLOAD_FOLDER = 'uploads'
# Create the uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# List of emotions used for simulation
EMOTIONS = ["Joy", "Sadness", "Anger", "Calmness", "Fear", "Disgust", "Surprise", "Neutral", "Excitement", "Love"]

def detect_emotion_from_audio(filepath):
    """
    Converts audio to text, sends text to Gemini API, and returns detected emotion.
    """
    print(f"[INFO] Audio file: {os.path.basename(filepath)} received for processing.")
    transcript = ""
    # Convert .webm to .wav using ffmpeg
    wav_path = filepath.replace('.webm', '.wav')
    try:
        import subprocess
        ffmpeg_cmd = [
            'ffmpeg', '-y', '-i', filepath, wav_path
        ]
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"[INFO] Converted {filepath} to {wav_path}")
    except Exception as e:
        print(f"[ERROR] ffmpeg conversion failed: {e}")
        wav_path = None

    # Transcribe the .wav file using Vosk
    if wav_path and os.path.exists(wav_path):
        try:
            # Download Vosk model if not present (small English model)
            model_path = "vosk-model-small-en-us-0.15"
            if not os.path.exists(model_path):
                print("[INFO] Downloading Vosk model (this may take a while)...")
                import urllib.request
                import tarfile
                url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
                zip_path = "vosk-model-small-en-us-0.15.zip"
                urllib.request.urlretrieve(url, zip_path)
                import zipfile
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall('.')
                os.remove(zip_path)
            model = Model(model_path)
            wf = wave.open(wav_path, "rb")
            rec = KaldiRecognizer(model, wf.getframerate())
            rec.SetWords(True)
            results = []
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    res = rec.Result()
                    results.append(res)
            final_res = rec.FinalResult()
            import json
            try:
                final_json = json.loads(final_res)
                transcript = final_json.get("text", "")
            except Exception:
                transcript = ""
            print(f"[INFO] Transcribed text: {transcript}")
            wf.close()
        except Exception as e:
            print(f"[ERROR] Vosk speech-to-text failed: {e}")
            transcript = ""
        # Clean up the wav file
        try:
            os.remove(wav_path)
            print(f"[INFO] Cleaned up file: {os.path.basename(wav_path)}")
        except Exception as e:
            print(f"[ERROR] Error removing file {wav_path}: {e}")
    else:
        print(f"[ERROR] .wav file not found for transcription.")

    # Clean up the uploaded .webm file
    try:
        os.remove(filepath)
        print(f"[INFO] Cleaned up file: {os.path.basename(filepath)}")
    except Exception as e:
        print(f"[ERROR] Error removing file {filepath}: {e}")

    if not transcript:
        return "Unknown"

    # Use provided Gemini API key and model
    gemini_api_key = os.getenv("GEMINI_API_KEY", "")
    print("[DEBUG] GEMINI_API_KEY:", gemini_api_key)
    gemini_model = "gemini-2.5-flash-preview-09-2025"
    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={gemini_api_key}"
    prompt = f"Extract the dominant emotion or word from this text. Check for emotion first but if no convincing emotion found then use the dominant word. Reply with ONE WORD only.Text: {transcript}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        response = requests.post(gemini_url, json=payload)
        result = response.json()
        # Extract emotion from Gemini response
        emotion = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "Unknown")
        print(f"[GEMINI LOG] Emotion detected: {emotion}")
        return emotion
    except Exception as e:
        print(f"[ERROR] Gemini API call failed: {e}")
        return "Unknown"

# --- Simulated Emotion Detection for Text ---
def detect_emotion_from_text(text_input):
    """
    Uses Gemini API to detect emotion from text input (same as audio).
    """
    gemini_api_key = os.getenv("GEMINI_API_KEY", "")
    gemini_model = "gemini-2.5-flash-preview-09-2025"
    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={gemini_api_key}"
    prompt = f"Identify the main subject or topic noun of this text. Reply with ONE WORD only. Text: {text_input}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        response = requests.post(gemini_url, json=payload)
        result = response.json()
        emotion = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "Unknown")
        print(f"[GEMINI LOG] Text input: '{text_input[:50]}...' -> Detected Emotion: {emotion}")
        return emotion
    except Exception as e:
        print(f"[ERROR] Gemini API call failed (text): {e}")
        return "Unknown"

# ----------------------------------------------------------------------
#                             FLASK ROUTES
# ----------------------------------------------------------------------

# --- Route to Handle Audio Upload (Voice Input) ---
@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    # 1. Check for the file key 'audio_blob' as defined in the frontend JS
    if 'audio_blob' not in request.files:
        # NOTE: Using a placeholder path here as the function requires one. 
        # The first instance of detect_emotion_from_audio was redundant and removed.
        return jsonify({"success": False, "message": "No audio file in request."}), 400

    audio_file = request.files['audio_blob']
    if audio_file.filename == '':
        return jsonify({"success": False, "message": "No file selected."}), 400

    # 2. Save uploaded file with a unique name
    filename = f"recording_{int(time.time())}_{random.randint(100, 999)}.webm"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    audio_file.save(filepath)

    # 3. Convert audio to text and detect emotion using Gemini
    emotion_result = detect_emotion_from_audio(filepath)

    # 4. Return JSON response to the frontend
    return jsonify({"success": True, "emotion": emotion_result})


# --- Route to Handle Text Submission (Describe Your Vibe) ---
@app.route('/process_text', methods=['POST'])
def process_text():
    data = request.get_json()
    text = data.get('text_input', '').strip()

    if not text:
        return jsonify({"success": False, "message": "No text provided."}), 400

    # Use Vosk to predict emotion from text (simulate speech-to-text for text input)
    # For text input, just use the same logic as detect_emotion_from_text
    emotion_result = detect_emotion_from_text(text)

    return jsonify({"success": True, "emotion": emotion_result})

# --- Route to Handle Quick Mood Picker ---
@app.route('/quick_mood', methods=['POST'])
def quick_mood():
    """
    Handles mood selection from the quick picker. 
    It receives the mood key and immediately returns it as the 'detected emotion'.
    """
    data = request.get_json()
    mood_key = data.get('mood', '').strip()

    if not mood_key:
        return jsonify({"success": False, "message": "No mood selected."}), 400
    
    # Capitalize for consistency with other route outputs (e.g., 'joy' -> 'Joy')
    detected_emotion = mood_key.capitalize()

    print(f"[QUICK PICK LOG] Mood Selected: {detected_emotion}")

    # The result is the mood itself, ready to be processed by the frontend JS
    return jsonify({"success": True, "emotion": detected_emotion})



# --- Route to serve HTML ---
@app.route('/')
def index():
    # Serve the index.html from the 'templates' folder
    return render_template('index.html')

# --- Route to generate songs based on mood ---
# --- Route to generate songs based on mood ---

def get_supported_model():
    return "gemini-2.5-flash-preview-09-2025"

def recommend_songs_by_mood(mood, api_key):
    genai.configure(api_key=api_key)
    model_name = get_supported_model()
    if not model_name:
        print("No models support generateContent in your setup.")
        return None, None
    print("Using model:", model_name)
    model = genai.GenerativeModel(model_name)
    prompt = f"Recommend 5 popular songs that match the mood: {mood}. Make sure to give a different set of songs every time, do not repeat songs from previous responses. List only the song title and artist. Format your response as a list."
    try:
        response = model.generate_content(prompt)
        songs_text = None
        if hasattr(response, "text") and response.text.strip():
            songs_text = response.text.strip()
        elif hasattr(response, "parts") and response.parts:
            songs_text = "\n".join([p.get("text", "") for p in response.parts if p.get("text")])
        elif hasattr(response, "candidates") and response.candidates:
            try:
                songs_text = response.candidates[0].content.parts[0].text.strip()
            except Exception:
                songs_text = None
        if songs_text:
            return songs_text
        else:
            print("No response text received from Gemini API.")
            return None
    except Exception as e:
        print("Error while generating content:", str(e))
        return None

@app.route('/generate_songs', methods=['POST'])
def generate_songs():
    mood = request.form.get('mood', '').strip()
    if not mood:
        return render_template('index2.html', songs=[], mood="Unknown", error="No mood provided.")

    api_key = os.getenv("GEMINI_API_KEY", "")
    songs_text = recommend_songs_by_mood(mood, api_key)
    songs = []
    error = None
    if songs_text:
        for line in songs_text.split('\n'):
            line = line.strip()
            if not line or line.lower().startswith('songs:'):
                continue
            if line[0:2].isdigit() and line[2] in ['.', ')']:
                line = line[3:].strip()
            elif line[0].isdigit() and line[1] in ['.', ')']:
                line = line[2:].strip()
            elif line.startswith('-'):
                line = line.lstrip('-').strip()
            elif line.startswith('*'):
                line = line.lstrip('*').strip()
            songs.append(line)
        if not songs and songs_text:
            songs = [l.strip().lstrip('*').strip() for l in songs_text.split('\n') if l.strip() and not l.lower().startswith('songs:')]
    else:
        error = "Could not fetch recommendations. Please check your API key, internet connection, and Gemini API access."

    return render_template('index2.html', songs=songs, mood=mood, error=error)

if __name__ == '__main__':
    # use_reloader=False is kept as per your original prompt
    app.run(debug=True, use_reloader=False)