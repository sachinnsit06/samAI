import json
import os
import re

from dotenv import load_dotenv
from google import genai


load_dotenv()

DEFAULT_MODEL = "gemini-2.5-flash"
question_cache = {}
_gemini_ready = False
_client = None


def _configure_gemini():
    global DEFAULT_MODEL, _gemini_ready, _client

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("WARNING: GOOGLE_API_KEY not found in .env file")
        return

    _client = genai.Client(api_key=api_key)
    _gemini_ready = True
    print("Google Gemini API configured successfully")
    print(f"Using model: {DEFAULT_MODEL}")


def has_gemini_api_key():
    return bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))


def _extract_json_payload(response_text):
    cleaned = (response_text or "").strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    cleaned = cleaned.strip()
    if cleaned.startswith("[") and cleaned.endswith("]"):
        return cleaned

    match = re.search(r"\[[\s\S]*\]", cleaned)
    if match:
        return match.group(0)

    return cleaned


def generate_questions_from_ai(topic, level, count=12):
    cache_key = f"{topic}_{level}_{count}"
    if cache_key in question_cache:
        print(f"Using cached questions for {cache_key}")
        return question_cache[cache_key]

    if not _gemini_ready:
        _configure_gemini()

    if not has_gemini_api_key():
        return {"error": "GOOGLE_API_KEY is not configured for this app"}

    if not _gemini_ready:
        return {"error": "Gemini could not be initialized. Check the API key and model access."}

    prompt = f"""Generate exactly {count} multiple choice questions for the topic "{topic}" at {level} difficulty level.

Requirements:
1. Each question must be unique and valid for "{topic}"
2. Each question should have exactly 4 options
3. Clearly indicate the correct answer index (0-3)
4. Include a brief explanation for why the answer is correct
5. Return ONLY valid JSON, no markdown, no extra text
6. Keep the questions tightly focused on the requested topic and difficulty
7. If the topic sounds advanced, technical, or interview-style, match that tone in the questions

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

Now generate {count} questions for "{topic}" at {level} difficulty:"""

    response_text = ""
    try:
        print(f"Generating {count} questions for {topic} ({level}) using {DEFAULT_MODEL}...")
        response = _client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=prompt,
        )
        response_text = (response.text or "").strip()
        json_payload = _extract_json_payload(response_text)
        questions = json.loads(json_payload)

        if not isinstance(questions, list) or not questions:
            return {"error": "Gemini returned no usable questions"}

        for idx, question in enumerate(questions):
            question.setdefault("id", 1000 + idx)
            question.setdefault("correct", 0)
            question.setdefault("explanation", "Great question!")
            options = question.get("options") or []
            correct_index = int(question["correct"])

            # Some model outputs drift into 1-based indexing even when asked for 0-3.
            if not options:
                question["options"] = ["Option 1", "Option 2", "Option 3", "Option 4"]
                options = question["options"]

            if correct_index not in range(len(options)) and 1 <= correct_index <= len(options):
                correct_index -= 1

            if correct_index < 0 or correct_index >= len(options):
                correct_index = 0

            question["correct"] = correct_index

        question_cache[cache_key] = questions
        print(f"Successfully generated {len(questions)} questions")
        return questions
    except json.JSONDecodeError as exc:
        print(f"JSON Parse Error: {exc}")
        print(f"Response was: {response_text[:200]}")
        return {"error": "Gemini returned an unexpected format. Try a simpler topic or lower question count."}
    except Exception as exc:
        print(f"Error generating questions: {exc}")
        return {"error": f"Question generation failed: {exc}"}


_configure_gemini()
