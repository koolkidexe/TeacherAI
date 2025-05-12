import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from gtts import gTTS
import uuid
import os

# === Page Config ===
st.set_page_config(page_title="📚 Teacher AI: PDF to Podcast", page_icon="🎧", layout="centered")

# === Sidebar ===
st.sidebar.markdown("## 🔐 API Configuration")
api_key = st.sidebar.text_input("Enter your Gemini API key", type="password")

st.sidebar.markdown("---")
st.sidebar.markdown("Made with ❤️")

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

# === Text-to-Audio ===
def convert_to_audio(text):
    tts = gTTS(text[:3000])
    audio_path = f"/tmp/audio_{uuid.uuid4().hex}.mp3"
    tts.save(audio_path)
    return audio_path

# === Header ===
st.markdown("<h1 style='text-align: center;'>🎧 Teacher AI: Turn Your PDF into a Podcast</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Upload a PDF. Get a summary. Listen to it as audio. Ask questions. Easy!</p>", unsafe_allow_html=True)
st.markdown("---")

# === Main App ===
uploaded_file = st.file_uploader("📄 Upload a PDF file", type="pdf")
user_question = st.text_input("❓ Have a question about your PDF? Ask here!")

if uploaded_file and not api_key:
    st.warning("⚠️ Please enter your Gemini API key in the sidebar.")

if uploaded_file and api_key:
    try:
        model = configure_gemini(api_key)
    except Exception as e:
        st.error(f"❌ Failed to configure Gemini: {e}")
        st.stop()

    text = extract_text_from_pdf(uploaded_file)

    if not text.strip():
        st.error("❌ Couldn't extract text. Try a different PDF.")
        st.stop()

    with st.spinner("🧠 Summarizing your PDF..."):
        try:
            summary = summarize_text(text, model)
            summary = summary.replace("*", "")  # Remove asterisks from summary
            st.success("✅ Summary complete!")
            st.markdown("### ✍️ Summary")
            st.text_area("Summary Text", summary, height=250)
        except Exception as e:
            st.error(f"❌ Error during summarization: {e}")
            st.stop()

    with st.spinner("🔊 Converting to audio..."):
        audio_file = convert_to_audio(summary)
        st.audio(audio_file, format="audio/mp3")
        st.success("✅ Audio ready!")

    if user_question:
        with st.spinner("💬 Answering your question..."):
            try:
                prompt = f"Based on this PDF:\n{text[:12000]}\n\nAnswer this question:\n{user_question}"
                response = model.generate_content(prompt)
                st.markdown("### 🧾 Answer")
                st.success(response.text)
            except Exception as e:
                st.error(f"❌ Error during Q&A: {e}")
