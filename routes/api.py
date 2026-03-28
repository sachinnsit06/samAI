from datetime import datetime

from flask import Blueprint, jsonify, request

from data.subjects import SUBJECTS
from services.question_service import generate_questions_from_ai, has_gemini_api_key
from services.user_service import (
    get_scores_for_user,
    login_user,
    register_user,
    submit_user_answer,
)


api_bp = Blueprint("api", __name__)


@api_bp.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "samAI is running!",
            "timestamp": datetime.now().isoformat(),
            "gemini_api": "Connected" if has_gemini_api_key() else "Not configured",
        }
    )


@api_bp.route("/api/subjects", methods=["GET"])
def get_subjects():
    return jsonify({"subjects": list(SUBJECTS.keys()), "subjectInfo": SUBJECTS})


@api_bp.route("/api/questions", methods=["GET"])
def get_questions():
    level = request.args.get("level", "easy")
    subject = request.args.get("subject", "python")

    if not subject:
        return jsonify({"error": "Subject is required"}), 400

    ai_questions = generate_questions_from_ai(subject, level, count=12)

    if not ai_questions or "error" in (ai_questions[0] if ai_questions else {}):
        return jsonify({"error": "Failed to generate questions. Please try again."}), 500

    return jsonify(ai_questions)


@api_bp.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()

    if not username:
        return jsonify({"error": "Username is required"}), 400

    try:
        user = register_user(username)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"message": f"User {username} registered!", "user": user}), 201


@api_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()

    if not username:
        return jsonify({"error": "Username is required"}), 400

    user, created = login_user(username)
    message = "Account created and logged in!" if created else "Login successful!"
    status_code = 201 if created else 200
    return jsonify({"message": message, "user": user}), status_code


@api_bp.route("/api/submit-answer", methods=["POST"])
def submit_answer():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    level = data.get("level", "easy")
    subject = data.get("subject", "python")
    correct_answer = data.get("correct_answer")
    user_answer = data.get("answer")

    try:
        result = submit_user_answer(
            username=username,
            subject=subject,
            level=level,
            correct_answer=correct_answer,
            user_answer=user_answer,
        )
    except KeyError:
        return jsonify({"error": "User not found"}), 404

    return jsonify(result), 200


@api_bp.route("/api/scores/<username>", methods=["GET"])
def get_scores(username):
    try:
        score_summary = get_scores_for_user(username)
    except KeyError:
        return jsonify({"error": "User not found"}), 404

    return jsonify(score_summary), 200
