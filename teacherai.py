import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import requests
import uuid
import time
import os

st.set_page_config(page_title="Teacher AI", page_icon="🎧")

# === Sidebar Configuration ===
st.sidebar.header("API Configuration")
gemini_api_key = st.sidebar.text_input("Enter your Gemini API key", type="password")
playht_user_id = st.sidebar.text_input("Enter your PlayHT User ID", type="password")
playht_api_key = st.sidebar.text_input("Enter your PlayHT API Key", type="password")
voice_id = st.sidebar.text_input("Voice ID (e.g., 's3://voice-cloning-zero-shot/anton.mp3')", value="en_us_male_1")

# === Gemini Setup ===
def configure_gemini(api_key):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.0-flash")

# === PDF Extraction ===
def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    return "\n".join([page.extract_text() or "" for page in reader.pages])

# === Summarization ===
def summarize_text(text, model):
    prompt = f"Summarize this PDF for a student:\n\n{text[:12000]}"
    response = model.generate_content(prompt)
    return response.text

# === PlayHT Audio Generation ===
def convert_to_audio_playht(text, user_id, api_key, voice_id="en_us_male_1"):
    url = "https://play.ht/api/v2/tts"

    headers = {
        "Authorization": api_key,
        "X-User-Id": user_id,
        "Content-Type": "application/json"
    }

    payload = {
        "voice": voice_id,
        "content": [text[:3000]],
        "speed": 1.0
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"PlayHT TTS request failed: {response.text}")

    audio_id = response.json()["transcriptionId"]

    # Poll until audio is ready
    audio_url = None
    for _ in range(30):
        status_res = requests.get(f"https://play.ht/api/v2/tts/{audio_id}", headers=headers)
        if status_res.status_code != 200:
            continue
        status_data = status_res.json()
        if status_data.get("status") == "completed":
            audio_url = status_data.get("audioUrl")
            break
        time.sleep(2)

    if not audio_url:
        raise Exception("Audio generation timed out.")

    audio_path = f"/tmp/audio_{uuid.uuid4().hex}.mp3"
    audio_data = requests.get(audio_url)
    with open(audio_path, "wb") as f:
        f.write(audio_data.content)

    return audio_path

# === Streamlit App ===
st.title("Teacher AI: PDF to Podcast")

uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
user_question = st.text_input("Ask something about your PDF")

if uploaded_file and not gemini_api_key:
    st.warning("Please enter your Gemini API key.")

if uploaded_file and not playht_api_key:
    st.warning("Please enter your PlayHT API key.")

if uploaded_file and gemini_api_key and playht_api_key and playht_user_id:
    try:
        model = configure_gemini(gemini_api_key)
    except Exception as e:
        st.error(f"Gemini error: {e}")
        st.stop()

    text = extract_text_from_pdf(uploaded_file)
    if not text.strip():
        st.error("Couldn't extract text. Try a different PDF.")
        st.stop()

    with st.spinner("Summarizing..."):
        try:
            summary = summarize_text(text, model)
            st.text_area("Summary", summary, height=200)
        except Exception as e:
            st.error(f"Summarization error: {e}")
            st.stop()

    with st.spinner("Generating audio with PlayHT..."):
        try:
            audio_file = convert_to_audio_playht(summary, playht_user_id, playht_api_key, voice_id)
            st.audio(audio_file, format="audio/mp3")
        except Exception as e:
            st.error(f"Audio generation failed: {e}")

    if user_question:
        with st.spinner("Answering your question..."):
            try:
                prompt = f"Based on this PDF:\n{text[:12000]}\n\nAnswer this question:\n{user_question}"
                response = model.generate_content(prompt)
                st.success(response.text)
            except Exception as e:
                st.error(f"Q&A error: {e}")
