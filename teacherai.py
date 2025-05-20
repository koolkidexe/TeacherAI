import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from gtts import gTTS
import uuid

# Set Streamlit page config
st.set_page_config(page_title="Teacher AI", page_icon="🎧")

# === Sidebar Configuration ===
st.sidebar.header("API Configuration")
gemini_api_key = st.sidebar.text_input("Enter your Gemini API key", type="password")

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
    clean_summary = response.text.replace("*", "")  # Remove asterisks
    return clean_summary

# === Text-to-Audio with gTTS ===
def convert_to_audio_gtts(text):
    tts = gTTS(text[:3000])  # gTTS char limit
    audio_path = f"/tmp/audio_{uuid.uuid4().hex}.mp3"
    tts.save(audio_path)
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
        try:
            audio_file = convert_to_audio_gtts(summary)
            st.audio(audio_file, format="audio/mp3")
        except Exception as e:
            st.error(f"Audio generation failed: {e}")

    if user_question:
        with st.spinner("Answering your question..."):
            try:
                prompt = f"{text[:12000]}\n\nAnswer this question:\n{user_question}"
                response = model.generate_content(prompt)
                answer = response.text.replace("*", "")
                st.success(answer)
            except Exception as e:
                st.error(f"Q&A error: {e}")
