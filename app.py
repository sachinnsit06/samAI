from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import yaml
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
import time

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize Google Gemini
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    print("⚠️ WARNING: GOOGLE_API_KEY not found in .env file")
else:
    genai.configure(api_key=api_key)
    print("✅ Google Gemini API configured successfully")
    
    # List available models
    print("\n📋 Available Models:")
    available_models = []
    try:
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                print(f"  ✅ {model.name}")
                available_models.append(model.name)
    except Exception as e:
        print(f"  Error listing models: {e}")
    
    if available_models:
        print(f"\nUsing model: {available_models[0]}")
        DEFAULT_MODEL = available_models[0]
    else:
        DEFAULT_MODEL = 'models/gemini-pro'
        print(f"\nUsing default model: {DEFAULT_MODEL}")

# In-memory storage
users = {}
scores = {}
question_cache = {}

def load_questions():
    try:
        with open('questions.yaml', 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        return {}

def generate_questions_from_ai(subject, level, count=12):
    """Generate questions using Google Gemini API (Free)"""
    
    # Check cache first
    cache_key = f"{subject}_{level}"
    if cache_key in question_cache:
        print(f"✅ Using cached questions for {cache_key}")
        return question_cache[cache_key]
    
    prompt = f"""Generate exactly {count} multiple choice questions for learning {subject} at {level} difficulty level.

Requirements:
1. Each question must be unique and valid for {subject}
2. Each question should have exactly 4 options
3. Clearly indicate the correct answer index (0-3)
4. Include a brief explanation for why the answer is correct
5. Return ONLY valid JSON, no markdown, no extra text

Return in this JSON format:
[
  {{
    "id": 1,
    "question": "What is question?",
    "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
    "correct": 0,
    "explanation": "This is why option 1 is correct"
  }}
]

Now generate {count} questions for {subject} at {level} difficulty:"""

    try:
        print(f"🔄 Generating {count} questions for {subject} ({level}) using {DEFAULT_MODEL}...")
        model = genai.GenerativeModel(DEFAULT_MODEL)
        response = model.generate_content(prompt)
        response_text = response.text
        
        # Clean up response
        response_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        elif response_text.startswith('```'):
            response_text = response_text[3:]
        
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        # Parse JSON
        questions = json.loads(response_text)
        
        # Validate questions
        for idx, q in enumerate(questions):
            if 'id' not in q:
                q['id'] = 1000 + idx
            if 'correct' not in q or q['correct'] is None:
                q['correct'] = 0
            if 'explanation' not in q:
                q['explanation'] = "Great question!"
            # Ensure correct is an integer
            q['correct'] = int(q['correct'])
        
        # Cache the questions
        question_cache[cache_key] = questions
        print(f"✅ Successfully generated {len(questions)} questions")
        return questions
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parse Error: {e}")
        print(f"Response was: {response_text[:200]}")
        return []
    except Exception as e:
        print(f"❌ Error generating questions: {e}")
        return []

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "✅ samAI is running!",
        "timestamp": datetime.now().isoformat(),
        "gemini_api": "Connected" if os.getenv('GOOGLE_API_KEY') else "Not configured"
    })

@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    subjects = {
        'python': {'icon': '🐍', 'name': 'Python'},
        'javascript': {'icon': '📜', 'name': 'JavaScript'},
        'sql': {'icon': '🗄️', 'name': 'SQL'},
        'linux': {'icon': '🐧', 'name': 'Linux'},
        'maths_4': {'icon': '🔢', 'name': 'Maths Grade 4'},
        'maths_5': {'icon': '🔢', 'name': 'Maths Grade 5'},
        'maths_6': {'icon': '🔢', 'name': 'Maths Grade 6'},
        'maths_7': {'icon': '🔢', 'name': 'Maths Grade 7'},
        'maths_8': {'icon': '🔢', 'name': 'Maths Grade 8'},
        'maths_9': {'icon': '🔢', 'name': 'Maths Grade 9'},
        'java': {'icon': '☕', 'name': 'Java'},
        'web_design': {'icon': '🎨', 'name': 'Web Design'},
        'react': {'icon': '⚛️', 'name': 'React'},
        'css': {'icon': '🎨', 'name': 'CSS'},
        'html': {'icon': '🏗️', 'name': 'HTML'}
    }
    return jsonify({"subjects": list(subjects.keys()), "subjectInfo": subjects})

@app.route('/api/questions', methods=['GET'])
def get_questions():
    level = request.args.get('level', 'easy')
    subject = request.args.get('subject', 'python')
    
    if not subject:
        return jsonify({"error": "Subject is required"}), 400
    
    ai_questions = generate_questions_from_ai(subject, level, count=12)
    
    if not ai_questions or 'error' in (ai_questions[0] if ai_questions else {}):
        return jsonify({"error": "Failed to generate questions. Please try again."}), 500
    
    return jsonify(ai_questions)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({"error": "Username is required"}), 400
    
    if username in users:
        return jsonify({"error": "User already exists"}), 400
    
    users[username] = {
        "username": username,
        "created_at": datetime.now().isoformat()
    }
    scores[username] = {}
    
    return jsonify({"message": f"✅ User {username} registered!", "user": users[username]}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({"error": "Username is required"}), 400
    
    if username not in users:
        users[username] = {
            "username": username,
            "created_at": datetime.now().isoformat()
        }
        scores[username] = {}
        return jsonify({"message": "✅ Account created and logged in!", "user": users[username]}), 201
    
    return jsonify({"message": "✅ Login successful!", "user": users[username]}), 200

@app.route('/api/submit-answer', methods=['POST'])
def submit_answer():
    data = request.json
    username = data.get('username')
    level = data.get('level', 'easy')
    subject = data.get('subject', 'python')
    correct_answer = data.get('correct_answer')
    user_answer = data.get('answer')
    
    if username not in users:
        return jsonify({"error": "User not found"}), 404
    
    is_correct = user_answer == correct_answer
    
    score_key = f"{subject}_{level}"
    if score_key not in scores[username]:
        scores[username][score_key] = 0
    
    if is_correct:
        scores[username][score_key] += 1
    
    return jsonify({
        "correct": is_correct,
        "correct_answer": correct_answer,
        "current_score": scores[username]
    }), 200

@app.route('/api/scores/<username>', methods=['GET'])
def get_scores(username):
    if username not in scores:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "username": username,
        "scores": scores[username],
        "total_questions_answered": sum(scores[username].values())
    }), 200

if __name__ == '__main__':
    print("🚀 Starting samAI Server...")
    print("📱 On Mobile: http://192.168.2.141:5000")
    print("💻 On Desktop: http://127.0.0.1:5000")
    print("\nPress Ctrl+C to stop the server")
    app.run(host='0.0.0.0', port=5000, debug=True)