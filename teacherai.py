import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import uuid
import requests
import time

# Set Streamlit page config
st.set_page_config(page_title="Teacher AI", page_icon="🎧")

# === Sidebar Configuration ===
st.sidebar.header("API Configuration")
gemini_api_key = st.sidebar.text_input("Enter your Gemini API key", type="password")
st.sidebar.subheader("PlayHT Configuration")
playht_user_id = st.sidebar.text_input("PlayHT User ID", type="password")
playht_api_key = st.sidebar.text_input("PlayHT API Key", type="password")

# === Gemini Setup ===
def configure_gemini(api_key):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.0-flash")

# === PDF Text Extraction ===
def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    return "\n".join([page.extract_text() or "" for page in reader.pages])

# === Summarization (clean prompt + remove asterisks after) ===
def summarize_text(text, model):
    prompt = text[:12000]  # Just the raw PDF content, no instructions
    response = model.generate_content(prompt)
    return response.text.replace("*", "")  # Remove asterisks from summary

# === Text-to-Audio with PlayHT (Alfonso voice) ===
def convert_to_audio_playht(text, user_id, api_key):
    url = "https://play.ht/api/v2/tts"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "X-User-Id": user_id
    }
    payload = {
        "text": text[:3000],
        "voice": "s3://voice-cloning-zero-shot/Mikael",  # Alfonso voice
        "output_format": "mp3"
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    transcription_id = response.json()["transcriptionId"]

    # Poll until audio is ready
    status_url = f"https://play.ht/api/v2/tts/{transcription_id}"
    while True:
        status_response = requests.get(status_url, headers=headers)
        status_data = status_response.json()
        if status_data.get("audioUrl"):
            break
        time.sleep(2)

    audio_url = status_data["audioUrl"]
    audio_data = requests.get(audio_url).content
    audio_path = f"/tmp/audio_{uuid.uuid4().hex}.mp3"
    with open(audio_path, "wb") as f:
        f.write(audio_data)

    return audio_path

# === Streamlit App ===
st.title("Teacher AI: PDF to Podcast")

uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
user_question = st.text_input("Ask something about your PDF")

if uploaded_file and not gemini_api_key:
    st.warning("Please enter your Gemini API key.")

if uploaded_file and gemini_api_key:
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

    with st.spinner("Generating audio..."):
        if not playht_user_id or not playht_api_key:
            st.error("Please enter your PlayHT User ID and API Key.")
        else:
            try:
                audio_file = convert_to_audio_playht(summary, playht_user_id, playht_api_key)
                st.audio(audio_file, format="audio/mp3")
            except Exception as e:
                st.error(f"Audio generation failed: {e}")

    if user_question:
        with st.spinner("Answering your question..."):
            try:
                prompt = f"{text[:12000]}\n\nAnswer this question:\n{user_question}"
                response = model.generate_content(prompt)
                answer = response.text.replace("*", "")  # Remove asterisks from answer
                st.success(answer)
            except Exception as e:
                st.error(f"Q&A error: {e}")
