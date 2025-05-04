import streamlit as st
import requests
from gtts import gTTS
from PyPDF2 import PdfReader
import uuid

# === Sidebar ===
st.sidebar.header("API Configuration")
api_key = st.sidebar.text_input("Enter your Gemini API key", type="password")

# === Utility: Extract PDF text ===
def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    return "\n".join([page.extract_text() or "" for page in reader.pages])

# === Utility: Summarize text using Gemini API ===
def summarize_text(text, api_key):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    endpoint = "https://api.gemini.com/v1/completions"  # Replace with actual Gemini API endpoint

    # Assuming the Gemini API uses similar parameters to OpenAI's API for summarization
    payload = {
        "model": "gemini-2.0-flash",  # Replace with the correct model name for Gemini
        "prompt": f"Summarize this for a student:\n\n{text}",
        "max_tokens": 150,  # You can adjust this based on your needs
    }

    response = requests.post(endpoint, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()["choices"][0]["text"]
    else:
        raise Exception(f"Error during summarization: {response.text}")

# === Utility: Convert text to audio ===
def convert_to_audio(text):
    tts = gTTS(text[:3000])  # Limit to 3000 characters for gTTS
    audio_path = f"/tmp/audio_{uuid.uuid4().hex}.mp3"
    tts.save(audio_path)
    return audio_path

# === Streamlit App ===
st.title("Teacher AI: PDF to Podcast")

uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
user_question = st.text_input("Ask something about your PDF")

if uploaded_file and not api_key:
    st.warning("Please enter your Gemini API key.")

if uploaded_file and api_key:
    text = extract_text_from_pdf(uploaded_file)

    if not text.strip():
        st.error("Couldn't extract text. Try a different PDF.")
        st.stop()

    with st.spinner("Summarizing..."):
        try:
            summary = summarize_text(text, api_key)
            st.text_area("Summary", summary, height=200)
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()

    with st.spinner("Generating audio..."):
        audio_file = convert_to_audio(summary)
        st.audio(audio_file, format="audio/mp3")

    if user_question:
        with st.spinner("Answering your question..."):
            try:
                # Using Gemini API for answering questions
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                endpoint = "https://api.gemini.com/v1/completions"  # Replace with actual Gemini API endpoint

                payload = {
                    "model": "gemini-2.0-flash",  # Replace with the correct model name for Gemini
                    "prompt": f"PDF content:\n{text}\n\nQuestion: {user_question}",
                    "max_tokens": 150,
                }

                response = requests.post(endpoint, headers=headers, json=payload)

                if response.status_code == 200:
                    answer = response.json()["choices"][0]["text"]
                    st.success(answer)
                else:
                    st.error(f"Error during question answering: {response.text}")

            except Exception as e:
                st.error(f"Error: {e}")
