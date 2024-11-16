import os
import cv2
import threading
import pyttsx3
import speech_recognition as sr
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify, redirect, url_for
import PyPDF2
import pandas as pd

app = Flask(__name__)

# Set base path and Excel path
base_path = os.path.dirname(os.path.abspath(__file__))
excel_path = os.path.join(base_path, 'company_faqs.xlsx')

# Configure Google Generative AI
genai.configure(api_key="AIzaSyAgmlM70rVc9g-lMtu8NIBD9hYqVRk0dVI")
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

# Text-to-Speech engine setup
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 1.0)
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)

# Extract text from a PDF file
def extract_text_from_file(file_path):
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in range(len(reader.pages)):
                text += reader.pages[page].extract_text()
        return text.strip() if text else None
    except Exception as e:
        return str(e)

# Load company-specific questions
def load_company_questions(company_name):
    try:
        df = pd.read_excel(excel_path)
        if company_name in df.columns:
            faqs = df[company_name].dropna().tolist()
            return faqs
        return None
    except Exception as e:
        return str(e)

# Start the interview session
def start_chat_session(resume_text, round_type, company_name=None, user_role=None):
    interview_instructions = {
        "HR": "Ask questions about communication skills, leadership qualities, and teamwork experiences.",
        "TR": "Ask questions focusing on technical skills, coding knowledge, and problem-solving ability.",
        "MR": "Ask questions related to managerial skills, decision-making, and team management.",
    }

    instructions = interview_instructions[round_type]

    if company_name:
        faqs = load_company_questions(company_name)
        if faqs:
            custom_questions = " ".join(faqs)
            instructions += f" Here are some frequently asked questions: {custom_questions}."

    if user_role:
        instructions += f" The candidate is applying for the role of {user_role}."

    return model.start_chat(
        history=[{
            "role": "user",
            "parts": [
                f"You are conducting a {round_type} interview. {instructions} "
                "Here is the resume: " + resume_text + ". "
                "Ask 15 questions one by one, stick to the interview format, and provide feedback at the end."
            ],
        }]
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    try:
        resume_file = request.files.get('resume')
        round_type = request.form.get('round_type')
        company_name = request.form.get('company_name')
        user_role = request.form.get('user_role')

        if resume_file:
            resume_path = os.path.join(base_path, 'uploaded_resume.pdf')
            resume_file.save(resume_path)
            resume_text = extract_text_from_file(resume_path)

            if resume_text:
                return jsonify({'success': True, 'message': "Resume uploaded successfully.", 'resume_text': resume_text})
            else:
                return jsonify({'success': False, 'message': "Could not extract text from the resume."})
        return jsonify({'success': False, 'message': "No file selected."})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/start_interview', methods=['POST'])
def start_interview():
    try:
        resume_text = request.json.get('resume_text')
        round_type = request.json.get('round_type')
        company_name = request.json.get('company_name')
        user_role = request.json.get('user_role')

        # Start the chat session with LLM
        chat_session = start_chat_session(resume_text, round_type, company_name, user_role)
        if chat_session:
            response = chat_session.send_message("Let's begin.")
            response_text = response.text

            # Text-to-speech for the response
            def speak_response(text):
                engine.say(text)
                engine.runAndWait()

            # Run TTS in a separate thread to avoid blocking the server
            tts_thread = threading.Thread(target=speak_response, args=(response_text,))
            tts_thread.start()

            return jsonify({'success': True, 'response': response_text})
        return jsonify({'success': False, 'message': "Failed to start interview session."})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Start the Flask server
if __name__ == '__main__':
    app.run(debug=True)
