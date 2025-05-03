# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import streamlit as st
import os
import openai
import tempfile
from gtts import gTTS
from PyPDF2 import PdfReader
import uuid

# Set your OpenAI API key
openai.api_key = "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"

def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text

def summarize_text(text):
    prompt = f"Summarize this PDF content for a student in a simple and clear way: {text}"
    response = openai.chat.completions.create(
        model="o3",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def convert_to_audio(text):
    tts = gTTS(text[:3000])  # Limit to 3000 characters for gTTS
    audio_path = f"/tmp/audio_{uuid.uuid4().hex}.mp3"
    tts.save(audio_path)
    return audio_path

st.title("Teacher AI: Convert PDFs to Podcasts")
st.markdown("Upload a PDF to get a student-friendly audio summary!")

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file:
    with st.spinner("Reading and summarizing PDF..."):
        text = extract_text_from_pdf(uploaded_file)
        if not text.strip():
            st.error("Couldn't extract text from the PDF. Please try a different file.")
            st.stop()

        summary = summarize_text(text)
        st.text_area("Summary", summary, height=200)

    with st.spinner("Generating audio..."):
        audio_file = convert_to_audio(summary)
        st.audio(audio_file, format='audio/mp3')

st.markdown("---")
st.header("Ask the AI about your PDF")
user_question = st.text_input("What do you want to know?")

if user_question and uploaded_file:
    with st.spinner("Answering your question..."):
        pdf_text = extract_text_from_pdf(uploaded_file)
        if not pdf_text.strip():
            st.error("Couldn't extract text to answer your question.")
            st.stop()

        question_prompt = f"Here is the content from a PDF: {pdf_text}\n\nAnswer this question based on that: {user_question}"
        response = openai.chat.completions.create(
            model="o3",
            messages=[{"role": "user", "content": question_prompt}]
        )
        answer = response.choices[0].message.content
        st.success(answer)
