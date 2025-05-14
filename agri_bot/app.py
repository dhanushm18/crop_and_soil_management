import os
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure the Gemini API
genai.configure(api_key="AIzaSyApClWYweivPNmL4r2dT_6EwnmrZ1QzLqM")

# Set up the model
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 1024,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
    safety_settings=safety_settings
)

# Initialize the chat session with agriculture context
chat = model.start_chat(
    history=[
        {
            "role": "user",
            "parts": ["You are an agriculture expert chatbot. Your purpose is to provide farmers and agricultural professionals with accurate information about farming practices, crop management, pest control, soil health, weather impacts, sustainable agriculture, and related topics. Please provide detailed and helpful responses to agricultural queries."]
        },
        {
            "role": "model",
            "parts": ["I'm your agriculture expert assistant, ready to help with farming questions. I can provide information on:\n\n- Crop management and cultivation techniques\n- Pest and disease identification and control\n- Soil health and fertility management\n- Irrigation and water management\n- Weather impacts on agriculture\n- Sustainable and organic farming practices\n- Farm equipment and technology\n- Livestock management\n- Agricultural economics and market trends\n\nWhether you're a small-scale farmer, commercial producer, or gardening enthusiast, I'll do my best to provide accurate, practical information to help you succeed. What agricultural topic can I assist you with today?"]
        }
    ]
)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    user_message = request.json.get('message', '')
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    try:
        # Send the user's message to the Gemini model
        response = chat.send_message(user_message)
        
        # Return the model's response
        return jsonify({'response': response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
