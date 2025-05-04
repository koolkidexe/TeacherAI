import streamlit as st
import openai
import requests
from gtts import gTTS
from PyPDF2 import PdfReader
import uuid

# === Sidebar ===
st.sidebar.header("API Configuration")
api_key = st.sidebar.text_input("Enter your OpenAI-compatible API key", type="password")

# === Utility: Extract PDF text ===
def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    return "\n".join([page.extract_text() or "" for page in reader.pages])

# === Utility: Summarize text ===
def summarize_text(text, api_key):
    openai.api_key = api_key
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": f"Summarize this for a student:\n\n{text}"}]
    )
    return response.choices[0].message.content

# === Utility: Convert text to audio ===
def convert_to_audio(text):
    tts = gTTS(text[:3000])
    audio_path = f"/tmp/audio_{uuid.uuid4().hex}.mp3"
    tts.save(audio_path)
    return audio_path

# === Streamlit App ===
st.title("Teacher AI: PDF to Podcast")

uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
user_question = st.text_input("Ask something about your PDF")

if uploaded_file and not api_key:
    st.warning("Please enter your OpenAI-compatible API key.")

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
                openai.api_key = api_key
                response = openai.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": f"PDF content:\n{text}\n\nQuestion: {user_question}"}]
                )
                st.success(response.choices[0].message.content)
            except Exception as e:
                st.error(f"Error: {e}")
