# CodeTrack — Python Code Practice Tracker

A full-stack web app to practice and track Python coding sessions.

## Features
- User registration & login (unique usernames, hashed passwords)
- Admin panel to add/delete coding challenges
- In-browser Python code editor with live execution
- Track sessions with difficulty, status, time spent, and notes
- Dashboard with stats and session history

## Tech Stack
- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python (Flask)
- **Database**: SQLite
- **DevOps**: Docker, Docker Compose

## Default Admin Login
- Username: `admin`
- Password: `admin123`

## Run with Docker
```bash
docker compose up --build
```

Then open: [http://localhost:5000](http://localhost:5000)

## Run Locally (without Docker)
```bash
pip install -r requirements.txt
python app.py
```

## Project Structure
```
code-practice-tracker/
├── app.py               # Flask backend
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── instance/            # SQLite DB (auto-created)
├── templates/           # HTML templates
└── static/              # CSS & JS
```