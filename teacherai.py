import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import requests
import uuid
import os

# === Sidebar Configuration ===
st.sidebar.header("API Configuration")
gemini_api_key = st.sidebar.text_input("Enter your Gemini API key", type="password")
elevenlabs_api_key = st.sidebar.text_input("Enter your ElevenLabs API key", type="password")
voice_name = st.sidebar.text_input("Voice name (e.g., Rachel, Bella, Antoni)", value="Rachel")

# === Setup Gemini Client ===
def configure_gemini(api_key):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.0-flash")

# === PDF Text Extraction ===
def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    return "\n".join([page.extract_text() or "" for page in reader.pages])

# === Summarization ===
def summarize_text(text, model):
    prompt = f"Summarize this PDF for a student:\n\n{text[:12000]}"
    response = model.generate_content(prompt)
    return response.text

# === ElevenLabs Voice Lookup ===
def get_voice_id_by_name(api_key, name="Rachel"):
    response = requests.get(
        "https://api.elevenlabs.io/v1/voices",
        headers={"xi-api-key": api_key}
    )
    if response.status_code != 200:
        raise Exception("Failed to fetch voice list from ElevenLabs.")

    voices = response.json()["voices"]
    for voice in voices:
        if voice["name"].lower() == name.lower():
            return voice["voice_id"]
    raise Exception(f"Voice '{name}' not found in your ElevenLabs account.")

# === Text-to-Audio with ElevenLabs ===
def convert_to_audio_elevenlabs(text, api_key, voice_name="Rachel"):
    voice_id = get_voice_id_by_name(api_key, voice_name)
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "text": text[:3000],
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"ElevenLabs TTS failed: {response.text}")

    audio_path = f"/tmp/audio_{uuid.uuid4().hex}.mp3"
    with open(audio_path, "wb") as f:
        f.write(response.content)

    return audio_path

# === Streamlit App ===
st.set_page_config(page_title="Teacher AI", page_icon="🎧")
st.title("Teacher AI: PDF to Podcast")

uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
user_question = st.text_input("Ask something about your PDF")

if uploaded_file and not gemini_api_key:
    st.warning("Please enter your Gemini API key.")

if uploaded_file and not elevenlabs_api_key:
    st.warning("Please enter your ElevenLabs API key.")

if uploaded_file and gemini_api_key and elevenlabs_api_key:
    try:
        model = configure_gemini(gemini_api_key)
    except Exception as e:
        st.error(f"Failed to configure Gemini: {e}")
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
            st.error(f"Error during summarization: {e}")
            st.stop()

    with st.spinner("Generating audio..."):
        try:
            audio_file = convert_to_audio_elevenlabs(summary, elevenlabs_api_key, voice_name)
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
                st.error(f"Error during Q&A: {e}")
