# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import streamlit as st
import openai
from gtts import gTTS
from PyPDF2 import PdfReader
import uuid

# Sidebar: User inputs OpenAI API key
st.sidebar.header("API Key")
api_key = st.sidebar.text_input("Enter your OpenAI API key:", type="password")

def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text

def summarize_text(text, api_key):
    openai.api_key = api_key
    prompt = f"Summarize this PDF content for a student in a simple and clear way:\n\n{text}"
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def convert_to_audio(text):
    tts = gTTS(text[:3000])  # Limit to 3000 characters for gTTS
    audio_path = f"/tmp/audio_{uuid.uuid4().hex}.mp3"
    tts.save(audio_path)
    return audio_path

# Main UI
st.title("Teacher AI: Convert PDFs to Podcasts")
st.markdown("Upload a PDF to get a student-friendly audio summary!")

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file and not api_key:
    st.warning("Please enter your OpenAI API key in the sidebar.")

if uploaded_file and api_key:
    with st.spinner("Reading and summarizing PDF..."):
        text = extract_text_from_pdf(uploaded_file)
        if not text.strip():
            st.error("Couldn't extract text from the PDF. Please try a different file.")
            st.stop()

        try:
            summary = summarize_text(text, api_key)
            st.text_area("Summary", summary, height=200)
        except Exception as e:
            st.error(f"Error during summarization: {e}")
            st.stop()

    with st.spinner("Generating audio..."):
        audio_file = convert_to_audio(summary)
        st.audio(audio_file, format='audio/mp3')

st.markdown("---")
st.header("Ask the AI about your PDF")
user_question = st.text_input("What do you want to know?")

if user_question and uploaded_file and api_key:
    with st.spinner("Answering your question..."):
        pdf_text = extract_text_from_pdf(uploaded_file)
        if not pdf_text.strip():
            st.error("Couldn't extract text to answer your question.")
            st.stop()

        question_prompt = f"Here is the content from a PDF:\n\n{pdf_text}\n\nAnswer this question: {user_question}"
        try:
            openai.api_key = api_key
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": question_prompt}]
            )
            answer = response.choices[0].message.content
            st.success(answer)
        except Exception as e:
            st.error(f"Error during question answering: {e}")
