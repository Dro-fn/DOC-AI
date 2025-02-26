from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import boto3
import uuid
from fastapi import HTTPException, Depends
from pydantic import BaseModel, EmailStr
from anthropic import AnthropicBedrock
from PyPDF2 import PdfReader
from typing import Optional, List
from typing import Optional
# from serverless_wsgi import handle_request

import os

from fastapi import FastAPI, HTTPException, UploadFile, File
import fitz  # PyMuPDF
from starlette.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pydantic import EmailStr

import pandas as pd


from fastapi import FastAPI, Request, HTTPException, Form,WebSocket, WebSocketDisconnect, Query
from fastapi import Depends, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from starlette.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm


from datetime import datetime

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# import spacy
import os
import io

from dotenv import load_dotenv
import boto3
# from openai import OpenAI
from pydantic import BaseModel
# from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr

from database import get_db_connection
from passlib.hash import bcrypt
from passlib.context import CryptContext

import pandas as pd
from datetime import datetime, timedelta
# from binance.client import Client
import logging
from mangum import Mangum
from anthropic import AnthropicBedrock
from PyPDF2 import PdfReader


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if config.env exists (for local testing)
if os.path.exists("config.env"):
    load_dotenv("config.env")
    print("Loaded environment variables from config.env (local testing).")
else:
    print("Using Vercel environment variables.")

# # Load environment variables
# # load_dotenv("config.env")
# OPENAI_API_KEY = os.getenv("open_ai_key")

# if not OPENAI_API_KEY:
#     raise ValueError("OpenAI API key not found. Check your config.env file.")

# # Initialize OpenAI client
# openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize FastAPI app

app = FastAPI(root_path="/prod")

# JWT Configuration
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
import uuid

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates directory
templates = Jinja2Templates(directory="templates")




app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
allow_origins=["http://127.0.0.1:8000", "https://crypto-ai-pi.vercel.app","https://cryptoai.drofn.com","https://doctor-ai.drofn.com"]
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize FastAPI app
# app = FastAPI()

# Serve static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize AWS STS client
# sts_client = boto3.client("sts")
# role_arn = "arn:aws:iam::888577066858:role/lambda_er"
# response = sts_client.assume_role(
#     RoleArn=role_arn,
#     RoleSessionName="lambdaERSession"
# )


# credentials = response["Credentials"]
# print(credentials)
AWS_REGION = os.getenv("AWS_REGION", "us-east-1") 
# Initialize AWS Polly client
# polly_client = boto3.client(
#     "polly",
#     aws_access_key_id=credentials["AccessKeyId"],
#     aws_secret_access_key=credentials["SecretAccessKey"],
#     aws_session_token=credentials["SessionToken"],region_name=AWS_REGION
# )
# translate_client = boto3.client("translate", aws_access_key_id=credentials["AccessKeyId"],
#     aws_secret_access_key=credentials["SecretAccessKey"],
#     aws_session_token=credentials["SessionToken"], region_name="us-east-1")  # AWS Translate
polly_client = boto3.client("polly", region_name=AWS_REGION)
translate_client = boto3.client("translate", region_name="us-east-1")

language_codes = {
    "en-US": "Joanna",
    "hi-IN": "Kajal",
    "es-ES": "Lucia",
    "fr-FR": "Lea",
    "de-DE": "Vicki"
}

# Initialize Anthropic client
client = AnthropicBedrock()
# Store previous conversations in memory
conversation_history: List[dict] = []
# Define request model
class PromptRequest(BaseModel):
    prompt: str
    report_text: Optional[str] = None
sessions = {}
FRONTEND_BASE_URL = "https://doctor-ai.drofn.com/"


@app.get("/", response_class=HTMLResponse)
async def serve_homepage():
    """
    Serve the homepage with options for Chat or Talk with AI Doctor.
    """
    return """
    <!DOCTYPE html>
    <html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Doctor AI</title>
    <link rel="stylesheet" href="/static/css/styles2.css">
    <style>
   .modal {
    display: none;  /* Hidden by default */
    position: fixed;
    z-index: 1000;
    left: 50%;
    top: 50%;
    width: 60%;
    max-width: 500px; /* Limits width for better readability */
    background-color: white; /* Pure white background */
    padding: 20px;
    border-radius: 10px; /* Rounded corners */
    transform: translate(-50%, -50%); /* Centers the modal */
}

.modal-content {
    text-align: center;
    font-family: Arial, sans-serif;
}

#agree-button {
    background-color: #007BFF; /* Blue button */
    color: white;
    border: none;
    padding: 10px 20px;
    margin-top: 20px;
    font-size: 16px;
    cursor: pointer;
    border-radius: 5px;
}

#agree-button:hover {
    background-color: #0056b3;
}

</style>
</head>
<body>

    <!-- Medical Disclaimer Modal -->
    <div id="disclaimer-modal" class="modal" style="display: none;">
        <div class="modal-content">
            <h2>Important Medical Disclaimer</h2>
            <p>
                The information and recommendations provided by this AI system are for <strong>informational and educational purposes only</strong>.
                This tool does <strong>not</strong> provide medical diagnosis, treatment, or medical advice.
            </p>
            <p><strong>Before relying on any information:</strong></p>
            <ul>
                <li><strong>Consult a Licensed Healthcare Professional:</strong> Always seek advice from a qualified doctor regarding medical conditions.</li>
                <li><strong>Do Not Ignore Medical Advice:</strong> Never disregard professional medical advice or delay seeking it because of information provided by AI.</li>
                <li><strong>Emergency Situations:</strong> If you experience a medical emergency, call emergency services or visit a hospital immediately.</li>
            </ul>
            <p>
                By proceeding, you acknowledge that this AI system is <strong>not a substitute for professional medical consultation</strong>. 
                You assume full responsibility for any actions taken based on the insights provided.
            </p>
            <button id="agree-button">I Understand and Agree</button>
        </div>
    </div>

    <!-- Header -->
    <div class="header">
        <h1>Doctor AI</h1>
        <p>For your health-related queries</p>
    </div>
     <main>
        <p id="user-email" style="display: none; font-weight: bold; background-color: #00ff55"></p> <!-- User email display -->
        <button
            id="logout-button"
            style="display: none; background-color: red; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">
            Logout
        </button>
    </main>

    <!-- AI Options -->
    <div class="content">
        <div class="options">
            <button onclick="location.href='/chat-with-ai'">Chat with AI Doctor</button>
            <button onclick="location.href='/talk-with-ai'">Talk to AI Doctor</button>
        </div>
    </div>

    <!-- Hero Section -->
    <div class="hero">
        <img src="/static/images/doctor.jpg" alt="Doctor" class="doctor-image">
    </div>
    
    <footer>
        <p>Made with ❤️ by Drofn's Team</p>
    </footer>

    <script>
        const API_BASE_URL =
    window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost"
        ? "http://127.0.0.1:8000" // Local API URL
        : window.location.hostname.includes("s3") || window.location.hostname.includes("amazonaws")
        ? "https://2vw6nl2cxg.execute-api.us-east-1.amazonaws.com/prod" // API Gateway URL for S3-hosted frontend
        : window.location.hostname.includes("lambda-url.us-east-1.on.aws")
        ? "https://rqr7l4e2exi4vtfsd7azrlabtu0bdfev.lambda-url.us-east-1.on.aws" // Lambda Function URL
        : window.location.hostname.includes("doctor-ai.drofn.com")
        # ? "https://2vw6nl2cxg.execute-api.us-east-1.amazonaws.com/prod" // Same API Gateway for CloudFront custom domain
        # : "https://crypto-ai-pi.vercel.app"; // Fallback production API URL

        console.log("Resetting inactivity timeout...", API_BASE_URL);
        document.addEventListener("DOMContentLoaded", () => {
            console.log("DOM fully loaded");

            const modal = document.getElementById("disclaimer-modal");
            const agreeButton = document.getElementById("agree-button");
            const userEmailDisplay = document.getElementById("user-email");
            const logoutButton = document.getElementById("logout-button");

            if (!localStorage.getItem("disclaimerAccepted")) {
                modal.style.display = "block";
            }

            // Function to check login status
            const checkLoginStatus = () => {
                const token = localStorage.getItem("token");
                const email = localStorage.getItem("email");

                if (!token || !email) {
                    console.log("User not logged in. Redirecting to login page.");
                    window.location.href = "/login.html"; // Redirect to login if not logged in
                    return false;
                }

                console.log("User is logged in:", email);
                userEmailDisplay.textContent = `Logged in as: ${email}`;
                userEmailDisplay.style.display = "block";
                logoutButton.style.display = "block";

                return true;
            };

            // Handle disclaimer modal
            if (modal && agreeButton) {
                console.log("Disclaimer modal and agree button found");
    
                // Show modal on page load
                modal.style.display = "block";
    
                agreeButton.addEventListener("click", () => {
                    console.log("Agree button clicked");
                    modal.style.display = "none"; // Hide modal
                    localStorage.setItem("disclaimerAccepted", "true");
    
                    if (!checkLoginStatus()) {
                        console.log("Redirecting to login page after disclaimer.");
                    } else {
                        console.log("User already logged in, showing dashboard.");
                        modal.style.display = "none";
                    }
                });
            } else {
                console.error("Modal or agree button not found");
            }

            // Handle logout functionality
            logoutButton?.addEventListener("click", () => {
                console.log("Logout button clicked");
                localStorage.removeItem("token");
                localStorage.removeItem("email");
                alert("Logged out successfully!");
                window.location.href = "/login.html";
            });
        }); 
    </script> 
    
</body>
</html>"""

@app.get("/chat-with-ai", response_class=HTMLResponse)
async def chat_with_ai():
    """
    Serve the Chat with AI Doctor page.
    """
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Chat with AI Doctor</title>
        <link rel="stylesheet" href="/static/css/styles.css">
    </head>
    <body>
        <div class="header">
            <h1>Chat with AI Doctor</h1>
        </div>
        <div class="content">
            <div class="chat-container">
                <div class="control-buttons">
                    <button onclick="startChat()">Start Chat</button>
                    <button onclick="endChat()">End Chat</button>
                </div>
                <div id="chat-history" class="chat-history">
                    <!-- Conversation history will be displayed here -->
                </div>
                <div class="form-container">
                    <textarea id="prompt" name="prompt" placeholder="Type your message here..."></textarea>

                    <label for="file-upload">Upload a PDF report (optional):</label>
                    
                    <input type="file" id="file-upload" name="file-upload" accept="application/pdf" multiple onchange="showUploadedFiles()"></input>

                    <div id="file-list" class="file-list">
                        <!-- File names will appear here -->
                    </div>
                    <button type="button" onclick="sendMessage()">Send</button>
                </div>
            </div>
        </div>
        <script>


           const API_BASE_URL =
    window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost"
        ? "http://127.0.0.1:8000" // Local API URL
        : window.location.hostname.includes("s3") || window.location.hostname.includes("amazonaws")
        ? "https://2vw6nl2cxg.execute-api.us-east-1.amazonaws.com/prod" // API Gateway URL for S3-hosted frontend
        : window.location.hostname.includes("lambda-url.us-east-1.on.aws")
        ? "https://rqr7l4e2exi4vtfsd7azrlabtu0bdfev.lambda-url.us-east-1.on.aws" // Lambda Function URL
        : window.location.hostname.includes("doctor-ai.drofn.com")
        # ? "https://2vw6nl2cxg.execute-api.us-east-1.amazonaws.com/prod" // Same API Gateway for CloudFront custom domain
        # : "https://crypto-ai-pi.vercel.app"; // Fallback production API URL

            console.log("Resetting inactivity timeout...", API_BASE_URL);
            let isChatActive = false;

            function startChat() {
                isChatActive = true;
                document.getElementById('chat-history').innerHTML = '<div class="chat-bubble ai">"Hello, I am your AI Doctor. I’m here to assist you with any health-related questions or concerns you might have. Feel free to ask about symptoms, conditions, or treatments. You can also upload your medical reports or previous doctor consultations to help me provide more personalized and accurate insights. How may I assist you today?" </div>';
            }

           function endChat() {
                fetch(API_BASE_URL+'/clear-conversation', { method: 'POST' })
                    .then(response => response.json())
                    .then(() => {
                        document.getElementById('chat-history').innerHTML = '<div class="chat-bubble ai">Chat ended. Have a great day!</div>';
                        alert('Conversation history cleared.');
                    });
            }

            function showUploadedFiles() {
                const fileInput = document.getElementById('file-upload');
                const fileListContainer = document.getElementById('file-list');
                const files = Array.from(fileInput.files);

                // Display all uploaded file names
                files.forEach((file, index) => {
                    const listItem = document.createElement('div');
                    listItem.textContent = `${index + 1}. ${file.name}`;
                    fileListContainer.appendChild(listItem);
                });
            }


            async function sendMessage() {
                if (!isChatActive) {
                    alert('Please start the chat first.');
                    return;
                }

                const prompt = document.getElementById('prompt').value;
                const fileInput = document.getElementById('file-upload');
                const chatHistory = document.getElementById('chat-history');

                // Append user message to chat history
                const userMessage = document.createElement('div');
                userMessage.className = 'chat-bubble user';
                userMessage.textContent = prompt;
                chatHistory.appendChild(userMessage);

                let reportTexts = [];
                const errorMessages = [];

                if (fileInput.files.length > 0) {
                    for (const file of fileInput.files) {
                        const formData = new FormData();
                        formData.append('file', file);

                        try {
                            const pdfResponse = await fetch(API_BASE_URL+'/upload-pdf', {
                                method: 'POST',
                                body: formData
                            });

                            if (!pdfResponse.ok) {
                                const errorData = await pdfResponse.json();
                                errorMessages.push(`${file.name}: ${errorData.detail}`);
                            } else {
                                const pdfData = await pdfResponse.json();
                                reportTexts.push(pdfData.text);
                            }
                        } catch (error) {
                            errorMessages.push(`${file.name}: Failed to process.`);
                        }
                    }
                }

                const response = await fetch(API_BASE_URL+'/generate-response', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt, report_text: reportTexts }) // Send as an array
                });


                const reader = response.body.getReader();
                const decoder = new TextDecoder("utf-8");

                let content = "";
                let isFirstUpdate = true;

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    content += decoder.decode(value, { stream: true });

                    if (isFirstUpdate) {
                        // Create AI response bubble on the first update
                        const liveResponse = document.createElement('div');
                        liveResponse.className = 'chat-bubble ai';
                        liveResponse.innerHTML = content.replace(/\\n/g, '<br>'); // Convert line breaks
                        chatHistory.appendChild(liveResponse);
                        isFirstUpdate = false;
                    } else {
                        // Update the last AI response bubble
                        const existingAiBubble = document.querySelector('.chat-bubble.ai:last-child');
                        if (existingAiBubble) {
                            existingAiBubble.innerHTML = content.replace(/\\n/g, '<br>');
                        }
                    }

                    chatHistory.scrollTop = chatHistory.scrollHeight;
                }

                // Ensure only one final AI response bubble
                const aiMessage = document.querySelector('.chat-bubble.ai:last-child');
                if (aiMessage) {
                    aiMessage.innerHTML = content.replace(/\\n/g, '<br>'); // Convert line breaks
                }

                // Scroll to the bottom of chat history
                chatHistory.scrollTop = chatHistory.scrollHeight;

                // Clear the prompt input
                document.getElementById('prompt').value = '';
            }
        </script>
    </body>
    </html>
    """


@app.post("/generate-response")
async def generate_response(data: dict):
    """
    Generate a conversation response using Claude AI and incorporate conversation history.
    """
    try:
        # Doctor-specific prompt
        doctor_prompt = (
            "As an AI doctor, your tone should be empathetic, clear, and professional. "
            "Use plain, non-technical language when explaining medical concepts to ensure the patient understands. "
            "Maintain a calm and supportive demeanor, acknowledging the patient's concerns. "
            "When responding:\n"
            "1. Begin with a  acknowledgment of the patient’s question.\n"
            "2. Provide an explanation or advice in a concise manner, avoiding unnecessary jargon.\n"
            "3. If relevant, explain the condition, procedure, or treatment options in simple terms.\n"
            "4. Ask leading and open-ended questions that can help gather additional context or details about the patient’s condition, such as:\n"
            "   - 'Can you tell me more about the symptoms you’ve been experiencing?'\n"
            "   - 'When did this issue start, and has it worsened over time?'\n"
            "   - 'Are there any additional concerns or questions you’d like me to address?'\n"
            "Adapt your tone to the context, offering reassurance if the patient expresses worry or anxiety. "
            "Use follow-up questions to ensure the response is tailored to the patient's needs.\n\n"
        )

        

        

        prompt = data.get("prompt", "")
        report_texts = data.get("report_text", [])
        print(report_texts)
        combined_reports = "\n\n".join(report_texts)
        combined_prompt =  f"{doctor_prompt}\n,user question: {prompt}\n\nAdditional Context from report:\n{combined_reports}"
        # Add previous conversation history
        for convo in conversation_history:
            combined_prompt = f"{convo['user']}: {convo['message']}\n{combined_prompt}"

        # # Generate AI response
        message = client.messages.create(
            max_tokens=4096,
            temperature=0.0,
            top_k=250,
            top_p=1,
            messages=[{"role": "user", "content": combined_prompt}],
            model="anthropic.claude-3-sonnet-20240229-v1:0",
        )
 
        ai_response = message.content[0].text 
        print(ai_response) 

        # Format response with line breaks and spacing
        formatted_response = ai_response.replace("\n", "<br>")
        # formatted_response = "<br>".join([line.strip() for line in ai_response.split("\n") if line.strip()])

        # Save to conversation history
        conversation_history.append({"user": "User", "message": prompt})
        conversation_history.append({"user": "AI", "message": formatted_response})

        return  formatted_response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {e}")







# ===============================
# 🚀 SESSION MANAGEMENT
# ===============================
@app.post("/begin_conversation")
async def begin_conversation(request: Request):
    """Start a new conversation session."""
    data = await request.json()
    user_id = data.get("user_id", "default")
    sessions[user_id] = []
    return {"message": "Conversation started."}


@app.post("/end_conversation")
async def end_conversation(request: Request):
    """End the conversation and clear history."""
    data = await request.json()
    user_id = data.get("user_id", "default")
    sessions.pop(user_id, None)
    return {"message": "Conversation ended."}


@app.post("/reset")
async def reset(user_id: str = "default"):
    """Reset conversation history."""
    sessions.pop(user_id, None)
    return {"message": "Conversation and data fetching stopped successfully."}





# ===============================
# 🗣️ TEXT-TO-SPEECH (AWS POLLY)
# ===============================


@app.post("/speak")
async def speak(request: Request):
    """Generate speech using AWS Polly with correct gender and voice."""
    data = await request.json()
    text = data.get("text", "").strip()
    voice_id = data.get("voiceId", "Joanna")  # Default Polly voice
    target_language = data.get("language", "en")  # Default language English

    if not text:
        raise HTTPException(status_code=400, detail="No text provided")

    try:
        # ✅ Translate AI response to the chosen language
        if target_language != "en":
            translated_text = translate_client.translate_text(
                Text=text,
                SourceLanguageCode="en",
                TargetLanguageCode=target_language
            )["TranslatedText"]
        else:
            translated_text = text  # Keep English if selected

        print(f"Polly speaking in {target_language} ({voice_id}): {translated_text}")

        # ✅ Generate speech using AWS Polly
        response = polly_client.synthesize_speech(
            Text= translated_text,
            OutputFormat="mp3",
            VoiceId=voice_id,
            Engine="neural",
        )

        audio_stream = io.BytesIO(response["AudioStream"].read())
        
        return StreamingResponse(audio_stream, media_type="audio/mpeg")

    except Exception as e:
        print(f"Error in Polly: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AWS Polly error: {str(e)}")

# ===============================
# 🤖 AI RESPONSE GENERATION
# ===============================

comprehend_client = boto3.client("comprehendmedical", region_name="us-east-1")

# ✅ Map Polly voice IDs to gender
voice_gender_map = {
    "Joanna": "female",
    "Kajal": "female",
    "Lea": "female",
    "Lucia": "female",
    "Vicki": "female",
    "Hans": "male",
    "Matthew": "male",
    "Raveena": "female",
    "Aditi": "female",
}



conversation_sessions = {}

class AIRequest(BaseModel):
   
    user_id: str = "default"   # ✅ Default value
    prompt: str
    report_texts: Optional[List[str]] = []  # ✅ Default empty list
    language: str = "en"  # ✅ Default to English
    voiceId: Optional[str] = "Joanna"  # ✅ Default Polly voice
    conversation_history: Optional[List[dict]] = []  # ✅ Store chat history




   
@app.post("/generate-response2")
def generate_response2(request_data: AIRequest):
    print("Received request:", request_data.dict())

    if not request_data.prompt:
        raise HTTPException(status_code=400, detail="Missing 'prompt' field.")

    print("meeeeeeeeeeeeeeeeeeeeeeeeeeeee")

    user_id = request_data.user_id
    prompt = request_data.prompt
    report_texts = request_data.report_texts or []  # ✅ Ensure list
    selected_language = request_data.language or "en"  # ✅ Default to "en"
    voice_id = request_data.voiceId or "Joanna"  # ✅ Default Polly voice
    conversation_history = request_data.conversation_history or []

    print(f"Received prompt: {prompt}")

    # ✅ Map Polly Voices to Gender
    voice_gender_map = {
        "Joanna": ("female", "en"),
        "Matthew": ("male", "en"),
        "Kajal": ("female", "hi"),
        "Raveena": ("female", "hi"),
        "Lucia": ("female", "es"),
        "Lea": ("female", "fr"),
        "Vicki": ("female", "de"),
        "Hans": ("male", "de"),
        "Cristiano": ("male", "es"),
    }
    
    speaker_gender, detected_language = voice_gender_map.get(voice_id, ("neutral", selected_language))

    # ✅ Multi-language Doctor Introduction
    doctor_intro = {
        "en": {
            "male": "Hello! I am Doctor AI, your virtual health assistant. How can I assist you today?",
            "female": "Hello! I am Doctor AI, your virtual health assistant. Please tell me your symptoms.",
            "neutral": "Hello! I am Doctor AI, here to help you understand your symptoms better."
        },
        "hi": {
            "male": "नमस्ते! मैं डॉक्टर एआई हूँ, आपका वर्चुअल हेल्थ असिस्टेंट। मैं आपकी कैसे सहायता कर सकता हूँ?",
            "female": "नमस्ते! मैं डॉक्टर एआई हूँ, आपका वर्चुअल हेल्थ असिस्टेंट। कृपया मुझे अपने लक्षण बताएं।",
            "neutral": "नमस्ते! मैं डॉक्टर एआई हूँ, आपकी स्वास्थ्य सहायता के लिए।"
        },
        "es": {
            "male": "¡Hola! Soy Doctor AI, tu asistente de salud virtual. ¿Cómo puedo ayudarte hoy?",
            "female": "¡Hola! Soy Doctor AI, tu asistente de salud virtual. Por favor, dime tus síntomas.",
            "neutral": "¡Hola! Soy Doctor AI, aquí para ayudarte con tus síntomas."
        },
        "fr": {
            "male": "Bonjour ! Je suis le Docteur AI, votre assistant de santé virtuel. Comment puis-je vous aider aujourd'hui ?",
            "female": "Bonjour ! Je suis le Docteur AI, votre assistant de santé virtuel. Veuillez me dire vos symptômes.",
            "neutral": "Bonjour ! Je suis le Docteur AI, ici pour vous aider avec vos symptômes."
        },
        "de": {
            "male": "Hallo! Ich bin Doktor AI, Ihr virtueller Gesundheitsassistent. Wie kann ich Ihnen heute helfen?",
            "female": "Hallo! Ich bin Doktor AI, Ihr virtueller Gesundheitsassistent. Bitte sagen Sie mir Ihre Symptome.",
            "neutral": "Hallo! Ich bin Doktor AI, hier um Ihnen mit Ihren Symptomen zu helfen."
        }
    }

    # ✅ Select the correct introduction message
    intro_message = doctor_intro.get(selected_language, doctor_intro["en"]).get(speaker_gender, doctor_intro["en"]["neutral"])

    # ✅ Doctor-specific prompt
    doctor_prompt = (
        "As an AI doctor, your tone should be empathetic, clear, and professional. "
        "Use plain, non-technical language when explaining medical concepts to ensure the patient understands. "
        "Maintain a calm and supportive demeanor, acknowledging the patient's concerns. "
        "When responding:\n"
        "1. Begin with an acknowledgment of the patient’s question.\n"
        "2. Provide an explanation or advice in a concise manner, avoiding unnecessary jargon.\n"
        "3. If relevant, explain the condition, procedure, or treatment options in simple terms.\n"
        "4. Ask open-ended questions to gather additional context, such as:\n"
        "   - 'Can you tell me more about the symptoms you’ve been experiencing?'\n"
        "   - 'When did this issue start, and has it worsened over time?'\n"
        "   - 'Are there any additional concerns or questions you’d like me to address?'\n"
        "Adapt your tone to the context, offering reassurance if the patient expresses worry or anxiety. "
        "Use follow-up questions to ensure the response is tailored to the patient's needs.\n\n"
    )

    # ✅ Translate User Input to English (if necessary)
    if selected_language != "en":
        translation_params = {"SourceLanguageCode": selected_language, "TargetLanguageCode": "en"}
        prompt = translate_client.translate_text(Text=prompt, **translation_params)["TranslatedText"]

    # ✅ Translate PDF Texts to English
    translated_texts = []
    for text in report_texts:
        if selected_language != "en":
            translated_text = translate_client.translate_text(Text=text, **translation_params)["TranslatedText"]
            translated_texts.append(translated_text)
        else:
            translated_texts.append(text)

           

    # ✅ Construct the full prompt
    translated_reports = "\n".join(translated_texts)
    # Construct the full prompt with explicit language instruction
    language_map = {
    "en": "English",
    "hi": "Hindi",
    "es": "Spanish",
    "fr": "French",
    "de": "German"
}

    language_name = language_map.get(selected_language, "English")  # Default to English
    if user_id not in conversation_sessions:
        conversation_sessions[user_id] = []

    # Append new user message to history
    conversation_sessions[user_id].append({"role": "user", "text": prompt})

    # ✅ Construct full AI prompt
    conversation_text = "\n".join([f"{msg['role'].capitalize()}: {msg['text']}" for msg in conversation_sessions[user_id]])
    
    full_prompt = (
        f"{doctor_prompt}\nprevious chat history{conversation_text}\n"
        f"User ({language_name}, {speaker_gender} voice): {prompt}\n\n"
        f"Medical Report:\n{translated_reports}\n"
        f"AI ({language_name}, {speaker_gender} voice): Please respond in {language_name}."
    )


    print("Generated Full Prompt:")
    print(full_prompt)

    # ✅ Generate AI response directly in the selected language
    message = client.messages.create(
        max_tokens=2046,
        temperature=0.0,
        top_k=250,
        top_p=1,
        messages=[{"role": "user", "content": full_prompt}],
       # model="anthropic.claude-3-sonnet-20240229-v1:0"
        model="us.anthropic.claude-3-5-haiku-20241022-v1:0"
    )

    ai_response = message.content[0].text
    conversation_sessions[user_id].append({"role": "ai", "text": ai_response})
    
        # ✅ Translate AI response to the chosen language
    if selected_language != "en":
        translated_ai_text = translate_client.translate_text(
            Text=ai_response,
            SourceLanguageCode="en",
            TargetLanguageCode=selected_language
        )["TranslatedText"]
    else:
        translated_ai_text = ai_response  # Keep English if selected

    return {"response": ai_response,"translated_ai_text":translated_ai_text, "intro": intro_message,"conversation_history": conversation_sessions[user_id] }

# ===============================
# 🖥️ HTML FRONTEND
# ===============================
@app.get("/talk-with-ai", response_class=HTMLResponse)
async def talk_with_ai():
    """Serve the AI Doctor Chat Interface."""
    return """

   
    

    <html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Talk to AI Doctor</title>
    <link rel="stylesheet" href="/static/css/styles.css">
</head>
<body>
    <div class="header">
        <h1>Talk to AI Doctor</h1>
    </div>
    
    <div class="content">
        <div class="avatar-container">
            <img src="static/images/DOCTORAI2.webp" alt="AI Avatar" class="avatar-image" style="width: 800px; height: 500px;">

        </div>

        <div class="controls">
            <button id="start-consultation">Start Conversation</button>
            <button id="stop">Stop AI reply</button>
            <button id="end-consultation">End Conversation</button>
            <label for="language-select">Choose Language:</label>
    <select id="language-select">
        <option value="en-US|Joanna" selected>English (Joanna)</option>
        <option value="hi-IN|Kajal">Hindi (Kajal)</option>
        <option value="es-ES|Lucia">Spanish (Lucia)</option>
        <option value="fr-FR|Lea">French (Lea)</option>
        <option value="de-DE|Vicki">German (Vicki)</option>
    </select>
        </div>

        <p id="status" class="status">Click Start Conversation to begin.</p>

        <div class="file-upload">
            <button id="uploadButton">📄 Select & Upload Medical Reports PDF(s)</button>
            <input type="file" id="pdf-upload" name="file-upload" accept="application/pdf" multiple style="display: none;">
        </div>



        <div id="file-list"></div>
        <div id="chat"></div>
    </div>

<script>
   const API_BASE_URL =
    window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost"
        ? "http://127.0.0.1:8000" // Local API URL
        : window.location.hostname.includes("s3") || window.location.hostname.includes("amazonaws")
        ? "https://2vw6nl2cxg.execute-api.us-east-1.amazonaws.com/prod" // API Gateway URL for S3-hosted frontend
        : window.location.hostname.includes("lambda-url.us-east-1.on.aws")
        ? "https://rqr7l4e2exi4vtfsd7azrlabtu0bdfev.lambda-url.us-east-1.on.aws" // Lambda Function URL
        : window.location.hostname.includes("doctor-ai.drofn.com")
        ? "https://2vw6nl2cxg.execute-api.us-east-1.amazonaws.com/prod" // Same API Gateway for CloudFront custom domain
        : "https://crypto-ai-pi.vercel.app"; // Fallback production API URL

console.log("Resetting inactivity timeout...", API_BASE_URL);
    document.addEventListener("DOMContentLoaded", function () {
        console.log("DOM Loaded, initializing event listeners...");

        // ✅ Select all required elements
        const startBtn = document.getElementById("start-consultation");
        const stopBtn = document.getElementById("stop");
        const endBtn = document.getElementById("end-consultation");
        const uploadButton = document.getElementById("uploadButton");
        const fileInput = document.getElementById("pdf-upload");
        const fileListDiv = document.getElementById("file-list");
        const chatDiv = document.getElementById("chat");
        const languageSelect = document.getElementById("language-select");

        if (!startBtn || !stopBtn || !endBtn || !uploadButton || !fileInput || !fileListDiv || !chatDiv || !languageSelect) {
            console.error("One or more elements are missing from the DOM!");
            return;
        }

        let recognition;
        let audio = null;
        let conversationHistory = []; // Store conversation history
        let extractedTexts = []; // Store extracted PDF texts
        let inactivityTimer = null;
        
        let selectedLanguage = "en"; // Default language
        let voiceId = "Joanna"; // Default Polly voice

        
        languageSelect.addEventListener("change", function () {
        const [languageCode, selectedVoice] = languageSelect.value.split("|");
        selectedLanguage = languageCode;
        voiceId = selectedVoice;
        console.log(`Selected Language: ${selectedLanguage}, Voice: ${voiceId}`);
    });

        // ✅ Start conversation: Play Polly introduction, then start listening
        startBtn.addEventListener("click", async function () {
            console.log("Start button clicked. Playing introduction...");

            // Ensure audio can play after user interaction
            const introText = "Hello! I am Doctor AI, your virtual health assistant. "
                + "I can help you understand your symptoms, provide general health insights, "
                + "and guide you on when to seek medical attention. "
                + "Please describe your symptoms, and I will do my best to assist you with reliable information.";

            await playPolly(introText);  // Polly starts speaking
            setTimeout(startListening, 1000); // Start listening **after** Polly
            resetInactivityTimer();
        });
        // ✅ Stop Polly and Start Listening
        stopBtn.addEventListener("click", function () {
            console.log("Stop button clicked. Stopping Polly and starting listening...");
            stopPolly(true); // Stop Polly and immediately start listening
        });

        // ✅ End conversation (clear conversation history)
        // ✅ End conversation (clear conversation history & uploaded PDFs)

        endBtn.addEventListener("click", async function () {
            console.log("🔴 Ending conversation...");

            try {
                await fetch(`${API_BASE_URL}/reset`, { method: "POST" }); // ✅ Reset session on the server
            } catch (error) {
                console.error("❌ Error resetting session:", error);
            }

            // ✅ Reset UI to initial state
            chatDiv.innerHTML = "<p>Click 'Start Conversation' to begin.</p>"; // Reset chat UI
            fileListDiv.innerHTML = ""; // Clear uploaded files
            fileInput.value = ""; // Reset file input field
            conversationHistory = []; // Clear stored conversation
            extractedTexts = []; // Clear extracted PDF texts

            // ✅ Stop Everything (Polly, Speech Recognition & Timers)
            stopPolly2();
            stopListening();
            resetTimers();

            // ✅ Ensure speech recognition cannot restart
            if (recognition) {
                recognition.onend = null;  // Prevent recognition from restarting
            }

            console.log("✅ Conversation fully reset. Polly, Listening, and Timers Stopped.");
        });

        // ✅ Stop Polly Completely
        function stopPolly2() {
            if (audio) {
                console.log("🔴 Stopping Polly audio...");
                audio.pause();
                audio = null;
            }
        }

            // ✅ Reset All Timers to Prevent Further Messages
        function resetTimers() {
            clearTimeout(inactivityTimer); // Stop inactivity timer
            inactivityTimer = null;
        }

            // ✅ Clear conversation history & uploaded files
            conversationHistory = [];
            extractedTexts = [];
            fileInput.value = "";  // Clear selected files
            fileListDiv.innerHTML = ""; // Clear file list display
            chatDiv.innerHTML = "<p>Click 'Start Conversation' to begin.</p>"; // Reset UI to initial state

            // ✅ Stop Everything (Polly, Speech Recognition & Timers)
            stopPolly2(false);
            stopListening();
            resetTimers(); // ✅ Ensure inactivity reminders stop

            console.log("Conversation fully reset. Polly, Listening, and Timers Stopped.");
        

        // ✅ Function to start listening for user input
        function startListening() {
            console.log("Starting speech recognition...");
            recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.lang = selectedLanguage;
            recognition.interimResults = false;

            recognition.onresult = async (event) => {
                const userSpeech = event.results[0][0].transcript.trim();
                console.log("User said:", userSpeech);

                chatDiv.innerHTML += `<p><b>You:</b> ${userSpeech}</p>`;
                conversationHistory.push({ role: "user", text: userSpeech });

                await sendMessage(userSpeech);
                resetInactivityTimer();
            };

            recognition.start();
        }


        // ✅ Stop Listening Function
    function stopListening() {
        if (recognition) {
            console.log("Stopping speech recognition...");
            recognition.stop();
            recognition = null;
        }
    }

        // ✅ Send message to AI and store response
         async function sendMessage(message) {
    console.log("Sending message to AI:", message);
    stopPolly();

    const response = await fetch(`${API_BASE_URL}/generate-response2`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            user_id: "default",
            prompt: message,
            conversation_history: conversationHistory,
            report_texts: extractedTexts,
            language: selectedLanguage // ✅ Send language to backend
        })
    });

    const data = await response.json();
    console.log("AI response:", data.response);

    conversationHistory.push({ role: "ai", text: data.response });
    chatDiv.innerHTML += `<p><b>AI:</b> ${data.response}</p>`;

    await playPolly(data.response);
}

        // ✅ Play text-to-speech using AWS Polly
        async function playPolly(text) {
            stopPolly(); // Stop any previous audio
            console.log("Playing Polly response...");

            const response = await fetch(`${API_BASE_URL}/speak`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    text,
                    voiceId,
                    language: selectedLanguage, // ✅ Ensure Polly speaks in chosen language
                })
            });

            if (!response.ok) {
                console.error("Error fetching Polly response:", response.statusText);
                return;
            }

            const blob = await response.blob();
            audio = new Audio(URL.createObjectURL(blob));

            audio.onerror = function () {
                console.error("Audio playback error: Unsupported format");
            };

            audio.play().catch(error => {
                console.error("Error playing Polly response:", error);
            });

            return new Promise(resolve => {
                audio.onended = () => {
                    resolve();
                    console.log("Polly finished speaking. Now starting listening...");
                    startListening(); // ✅ Start listening after Polly finishes
                };
            });
        }
        // ✅ Stop Polly (and start listening if `forceListen` is true)
        function stopPolly(forceListen = false) {
            if (audio) {
                console.log("Stopping Polly audio...");
                audio.pause();
                audio = null;
            }
            if (forceListen) {
                startListening();
            }
        }

        // ✅ Handle user inactivity
        function resetInactivityTimer() {
            clearTimeout(inactivityTimer);
            inactivityTimer = setTimeout(() => {
                console.log("User inactive for 5 minutes. Ending conversation.");
                playPolly("I haven't heard from you in a while. I am ending the conversation now. Have a great day!");
                endBtn.click();
            }, 5 * 60 * 1000);

            setTimeout(() => playPolly("I am still here. Let me know if you have any more questions!"), 1 * 60 * 1000);
            setTimeout(() => playPolly("If you need any further assistance, just say something!"), 2 * 60 * 1000);
            setTimeout(() => playPolly("I will end this session soon if there's no response."), 3 * 60 * 1000);
        }

        async function uploadPDFs() {
            if (fileInput.files.length === 0) {
                console.warn("No file selected.");
                return;
            }

            fileListDiv.innerHTML += "<p>Uploading files...</p>";
            extractedTexts = []; // Reset extracted texts

            for (const file of fileInput.files) {
                const formData = new FormData();
                formData.append("file", file);

                try {
                    const response = await fetch(`${API_BASE_URL}/upload-pdf`, {
                        method: "POST",
                        body: formData
                    });

                    const responseData = await response.json();

                    if (!response.ok) {
                        throw new Error(responseData.detail || `Upload failed for ${file.name}`);
                    }

                    // Store extracted text
                    extractedTexts.push(responseData.text);

                    // Success message
                    const fileText = document.createElement("p");
                    fileText.textContent = `✅ Uploaded: ${file.name}`;
                    fileListDiv.appendChild(fileText);

                } catch (error) {
                    console.error(`Error uploading PDF (${file.name}):`, error);
                    const errorMsg = document.createElement("p");
                    errorMsg.textContent = `❌ Upload failed for ${file.name}: ${error.message}`;
                    errorMsg.style.color = "red";
                    fileListDiv.appendChild(errorMsg);
                }
            }
        }


        // ✅ Open file picker when clicking upload button
        uploadButton.addEventListener("click", function () {
            fileInput.click();
        });

        fileInput.addEventListener("change", uploadPDFs);
        
    });
</script>





</body>
</html>

    """



@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Extract text from uploaded PDF and return extracted text."""
    try:
        logger.info(f"Received PDF file: {file.filename}")

        # Check if the file is a PDF
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="File must be a PDF.")

        # Read file contents
        contents = await file.read()

        # Try PyPDF2 first
        try:
            pdf_reader = PdfReader(io.BytesIO(contents))
            extracted_text = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
        except Exception as e:
            logger.warning(f"PyPDF2 failed for {file.filename}: {e}")
            extracted_text = ""

        # Fallback to PyMuPDF (fitz) if PyPDF2 fails
        if not extracted_text.strip():
            logger.info(f"Trying PyMuPDF for {file.filename}...")
            try:
                pdf_document = fitz.open(stream=contents, filetype="pdf")
                extracted_text = "\n".join([page.get_text() for page in pdf_document])
            except Exception as e:
                logger.error(f"PyMuPDF also failed for {file.filename}: {e}")
                raise HTTPException(status_code=500, detail="Failed to extract text from PDF.")

        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="PDF contains no extractable text.")

        logger.info(f"Successfully extracted text from {file.filename}")
        print(extracted_text)
        return {"text": extracted_text}

    except HTTPException as http_ex:
        logger.error(f"HTTP Error: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        logger.error(f"Unexpected error processing {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
async def send_reset_email(email: str, reset_link: str):
    try:
        # Email server configuration
        print(email)
        print(reset_link)
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email =  os.getenv("MAIL_FROM")
        print(sender_email)
        sender_password = os.getenv("MAIL_PASSWORD")
        print(sender_password)

        # Create email message
        message = MIMEMultipart("alternative")
        message["Subject"] = "Password Reset Request"
        message["From"] = sender_email
        message["To"] = email

        # Email body
        text = f"""\
        Hi,
        
        Click the link below to reset your password:
        {reset_link}
        
        If you did not request this, please ignore this email.
        """
        message.attach(MIMEText(text, "plain"))

        # Connect to the email server and send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, message.as_string())
        server.quit()

        print(f"Password reset email sent successfully to {email}.")
    except Exception as e:
        print(f"Failed to send password reset email: {str(e)}")
        raise


fake_users_db = {
    "test@example.com": {
        "username": "test",
        "hashed_password": "password123",  # Example hashed password
        "disabled": False,
    }
}

# Helper Functions
# def verify_password(plain_password, hashed_password):
#     return plain_password == hashed_password  # Replace with hashing logic

def get_user(username: str):
    return fake_users_db.get(username)

# def create_access_token(data: dict, expires_delta: timedelta = None):
#     to_encode = data.copy()
#     expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    """Hash a plain text password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=15)) -> str:
    """Generate a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")



@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Serve the login page."""
    with open("templates/login.html", "r") as file:
        return HTMLResponse(content=file.read())
    
# @app.get("/login", response_class=HTMLResponse)
# async def login_page(request: Request):
#     access_token = request.cookies.get("access_token")
#     if access_token:
#         return RedirectResponse(url="/dashboard")
#     return templates.TemplateResponse("login.html", {"request": request})    
    
# @app.post("/api/login")
# async def login(email: str = Form(...), password: str = Form(...)):
#     """
#     Handle user login.
#     """
#     # Check if the email exists in the database
#     user = users_db.get(email)
#     if not user:
#         raise HTTPException(
#             status_code=404,
#             detail="Email not found. Please register an account."
#         )
#     # Validate the password
#     if user["password"] != password:
#         raise HTTPException(
#             status_code=401,
#             detail="Incorrect password. Please try again."
#         )

#     # Successful login
#     return {"message": "Login successful!", "username": user["username"]}   
 
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/login")
async def login_user(
    email: str = Form(...),
    password: str = Form(...),
):
    """
    Log in the user and validate credentials.
    """
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Fetch the user from the database
        cursor.execute("SELECT id, password_hash FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if not user:
            # return {"error": "Invalid email or user does not exist"}
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid email or user does not exist"}
            )

        user_id, hashed_password = user

        # Verify the password
        if not pwd_context.verify(password, hashed_password):
            # return {"error": "Invalid password"}
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid password"}
            )


        # Generate an access token
        access_token = create_access_token(data={"sub": str(user_id)})

        # Include success message
        return {
            "message": "Login successful!",
            "redirect_url": "/dashboard",
            "access_token": access_token
        }

    except Exception as e:
        print(f"Error during login: {str(e)}")
        # return {"error": "An unexpected error occurred. Please try again later."}
        return JSONResponse(
            status_code=500,
            content={"error": "An unexpected error occurred. Please try again later."}
        )

    finally:
        cursor.close()
        connection.close()


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and generate JWT token."""
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        # raise HTTPException(status_code=400, detail="Invalid username or password")
        return {"error": "Invalid username or password"}
    
    token = create_access_token(data={"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/app")
async def main_app(current_user: str = Depends(get_current_user)):
    """Main application logic, protected by login."""
    return {"message": f"Welcome to the app, {current_user}!"}

users_db={}

@app.get("/register", response_class=HTMLResponse)
async def get_register_page(request: Request):
    """
    Serve the registration page.
    """
    return templates.TemplateResponse("register.html", {"request": request})


# Handle registration form submission
# @app.post("/api/register")
# async def register_user(
#     username: str = Form(...),
#     email: EmailStr = Form(...),
#     password: str = Form(...)
# ):
#     """
#     Handle the user registration process.
#     """
#     # Check if the user already exists
#     if email in users_db:
#         raise HTTPException(status_code=400, detail="User already exists")

#     # Save the user to the "database" (in-memory for this example)
#     users_db[email] = {"username": username, "password": password}

#     return {"message": "Account created successfully!", "user": {"username": username, "email": email}}
# sessions = {}
@app.post("/api/register")
async def register_user(
    username: str = Form(...),
    email: EmailStr = Form(...),
    password: str = Form(...)
):
    """
    Register a new user in the PostgreSQL database.
    """
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Check if the email already exists
        cursor.execute("SELECT 1 FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return {"error": "User already exists"}

        # Hash the password
        password_hash = pwd_context.hash(password)

        # Insert the user into the database
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (username, email, password_hash)
        )
        connection.commit()

        # Fetch the inserted user ID
        user_id = cursor.fetchone()[0]
        print(f"New user created with ID: {user_id}")

        return {"message": "Account created successfully!", "user_id": user_id}
    except Exception as e:
        connection.rollback()
        print(f"Database error: {e}")
        return {"error": "An unexpected error occurred. Please try again later."}
    finally:
        cursor.close()
        connection.close()

users_db = {
    "user@example.com": {"username": "user", "password": "hashed_password"},
    # Add other users as needed
}

import uuid

import uuid
from fastapi import HTTPException, Depends
from pydantic import BaseModel, EmailStr

# async def send_reset_email(email: str, reset_link: str):
#     # Your email sending logic here
#     print(f"Email sent to {email} with link: {reset_link}")

@app.get("/terms", response_class=HTMLResponse)
async def terms_of_service(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})

@app.get("/privacy", response_class=HTMLResponse)
async def privacy_policy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})

# Define the request model
class ForgetPasswordRequest(BaseModel):
    email: EmailStr

@app.post("/api/forget-password")
async def forget_password(
    request: ForgetPasswordRequest,  # Use Pydantic model
    db=Depends(get_db_connection)
):
    try:
        cursor = db.cursor()

        # Access the email from the request model
        email = request.email

        # Check if email exists in the database
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user:
            return {"error": "Email not found"}

        # Generate a unique reset token
        reset_token = str(uuid.uuid4())
        frontend_base_url = os.getenv("FRONTEND_BASE_URL", "http://127.0.0.1:8000")
        reset_link = f"{frontend_base_url}reset-password.html?token={reset_token}"
        # reset_link = f"http://127.0.0.1:8000/reset-password?token={reset_token}"
        print("Reset Link:", reset_link)

        # Save the reset token in the database
        cursor.execute(
            "UPDATE users SET reset_token = %s WHERE email = %s",
            (reset_token, email),
        )
        db.commit()
        print(email)
        print("Reset token saved in the database.")
        # Send the email with the reset link
      
        await send_reset_email(email, reset_link)

        return {"message": "Password reset link has been sent to your email."}
    except Exception as e:
        db.rollback()
        return {"error": f"Database error: {str(e)}"}
    finally:
        cursor.close()
        db.close()

# @app.get("/forget-password", response_class=HTMLResponse)
# async def get_forget_password_page():
#     with open("forget-password.html", "r") as file:
#         return HTMLResponse(content=file.read())
@app.get("/forget-password", response_class=HTMLResponse)
async def get_forget_password_page(request: Request):
    return templates.TemplateResponse("forget-password.html", {"request": request})    

@app.get("/reset-password")
async def reset_password_page(request: Request, token: str):
    # Validate the token and render the reset password page
    return templates.TemplateResponse("reset-password.html", {"request": request, "token": token})    
@app.post("/api/reset-password")
async def reset_password(new_password: str = Form(...), token: str = Form(...), db=Depends(get_db_connection)):
    try:
        cursor = db.cursor()

        # Check if the token exists and fetch the user
        cursor.execute("SELECT email FROM users WHERE reset_token = %s", (token,))
        user = cursor.fetchone()

        if not user:
            return {"error": "Invalid or expired token"}

        email = user[0]

        # Update the user's password and clear the token
        hashed_password = pwd_context.hash(new_password)
        cursor.execute(
            "UPDATE users SET password_hash = %s, reset_token = NULL WHERE email = %s",
            (hashed_password, email),
        )
        db.commit()

        return {"message": "Password reset successfully!"}
    except Exception as e:
        db.rollback()
        return {"error": f"Database error: {str(e)}"}
    finally:
        cursor.close()
        db.close()


handler = Mangum(app)
# Simulated AWS Lambda Event

