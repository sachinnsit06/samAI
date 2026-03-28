# samAI

samAI is a small Flask-based learning app I built to generate quiz questions on demand and make practice a little more interactive.

The idea is simple: pick a subject, choose a difficulty level, and let the app generate a quiz for you. It keeps track of the current user's score in memory and gives quick feedback after every answer.

Right now the app supports subjects like Python, JavaScript, SQL, Linux, Java, React, HTML, CSS, Web Design, and a few school-level maths options.

## Why I made this

This project started when my daughter wanted to practice her math skills. After looking through iPad apps and finding mostly expensive subscriptions, I decided to build our own solution. What began as a simple math tool evolved into a broader learning platform as I added technical tracks like Python, SQL, and Web Dev for the community to practice.


## What it does

- Simple web interface for logging in and starting a quiz
- Subject and difficulty selection
- AI-generated multiple-choice questions
- Explanation shown after each answer
- In-memory score tracking per user
- Flask API backend with a small frontend served from templates
- Docker support for running the app in a container

## Stack

- Python
- Flask
- Flask-CORS
- Google Generative AI SDK
- HTML, CSS, JavaScript
- Docker

## Project structure

```text
samAI/
  app.py
  routes/
    api.py
    web.py
  services/
    question_service.py
    user_service.py
  data/
    subjects.py
  templates/
    index.html
  Dockerfile
  requirements.txt
  questions.yaml
```

## How it works

- `app.py` creates the Flask app and registers the routes
- `routes/web.py` serves the main page
- `routes/api.py` handles quiz, login, score, and health endpoints
- `services/question_service.py` deals with Gemini setup and question generation
- `services/user_service.py` manages users and score tracking in memory
- `data/subjects.py` stores the available subject list and labels

## Running locally

### 1. Create and activate a virtual environment

On Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Add environment variables

Create a `.env` file in the project root and add your keys:

```env
GOOGLE_API_KEY=your_google_api_key_here
```

### 4. Run the app

```powershell
python app.py
```

The app will be available at:

`http://127.0.0.1:5000`

## Running with Docker

Build the image:

```powershell
docker build -t samai:local .
```

Run the container:

```powershell
docker run --env-file .env -p 8080:5000 samai:local
```

Then open:

`http://localhost:8080`

## API routes

- `GET /` - main app page
- `GET /health` - health check
- `GET /api/subjects` - list available subjects
- `GET /api/questions?subject=python&level=easy` - generate quiz questions
- `POST /api/register` - register a user
- `POST /api/login` - log in or auto-create a user
- `POST /api/submit-answer` - submit an answer
- `GET /api/scores/<username>` - fetch score summary

## Current limitations

- User data and scores are stored in memory, so they reset when the app restarts
- Question generation depends on the AI API being available
- There is no database or persistent login yet
- The frontend is still a single template file and can be broken into smaller pieces later

## Next improvements I may add

- Persistent user and score storage with SQLite or PostgreSQL
- Cleaner frontend structure with separated static assets
- Better validation and error handling
- Admin view or analytics for quiz performance
- Support for more subjects and custom quiz lengths

## Notes

This project is still evolving, but the core flow is working and the codebase has now been split into smaller modules so it is easier to maintain.

If you clone it, add your own `.env` file before running it.
