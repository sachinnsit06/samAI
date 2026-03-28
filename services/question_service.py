import json
import os

from dotenv import load_dotenv
import google.generativeai as genai


load_dotenv()

DEFAULT_MODEL = "models/gemini-pro"
question_cache = {}
_gemini_ready = False


def _configure_gemini():
    global DEFAULT_MODEL, _gemini_ready

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("WARNING: GOOGLE_API_KEY not found in .env file")
        return

    genai.configure(api_key=api_key)
    _gemini_ready = True
    print("Google Gemini API configured successfully")

    available_models = []
    try:
        for model in genai.list_models():
            if "generateContent" in model.supported_generation_methods:
                available_models.append(model.name)
    except Exception as exc:
        print(f"Error listing models: {exc}")

    if available_models:
        DEFAULT_MODEL = available_models[0]
        print(f"Using model: {DEFAULT_MODEL}")
    else:
        print(f"Using default model: {DEFAULT_MODEL}")


def has_gemini_api_key():
    return bool(os.getenv("GOOGLE_API_KEY"))


def generate_questions_from_ai(subject, level, count=12):
    cache_key = f"{subject}_{level}"
    if cache_key in question_cache:
        print(f"Using cached questions for {cache_key}")
        return question_cache[cache_key]

    if not _gemini_ready:
        _configure_gemini()

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

    response_text = ""
    try:
        print(f"Generating {count} questions for {subject} ({level}) using {DEFAULT_MODEL}...")
        model = genai.GenerativeModel(DEFAULT_MODEL)
        response = model.generate_content(prompt)
        response_text = (response.text or "").strip()

        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]

        if response_text.endswith("```"):
            response_text = response_text[:-3]

        questions = json.loads(response_text.strip())

        for idx, question in enumerate(questions):
            question.setdefault("id", 1000 + idx)
            question.setdefault("correct", 0)
            question.setdefault("explanation", "Great question!")
            question["correct"] = int(question["correct"])

        question_cache[cache_key] = questions
        print(f"Successfully generated {len(questions)} questions")
        return questions
    except json.JSONDecodeError as exc:
        print(f"JSON Parse Error: {exc}")
        print(f"Response was: {response_text[:200]}")
        return []
    except Exception as exc:
        print(f"Error generating questions: {exc}")
        return []


_configure_gemini()
