from datetime import datetime


users = {}
scores = {}


def register_user(username):
    if username in users:
        raise ValueError("User already exists")

    user = {
        "username": username,
        "created_at": datetime.now().isoformat(),
    }
    users[username] = user
    scores[username] = {}
    return user


def login_user(username):
    if username not in users:
        return register_user(username), True
    return users[username], False


def submit_user_answer(username, subject, level, correct_answer, user_answer):
    if username not in users:
        raise KeyError(username)

    is_correct = user_answer == correct_answer
    score_key = f"{subject}_{level}"
    scores[username].setdefault(score_key, 0)

    if is_correct:
        scores[username][score_key] += 1

    return {
        "correct": is_correct,
        "correct_answer": correct_answer,
        "current_score": scores[username],
    }


def get_scores_for_user(username):
    if username not in scores:
        raise KeyError(username)

    return {
        "username": username,
        "scores": scores[username],
        "total_questions_answered": sum(scores[username].values()),
    }
