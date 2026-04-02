import sqlite3, os
from werkzeug.security import generate_password_hash

DB = 'instance/tracker.db'

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs('instance', exist_ok=True)
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS challenges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        starter_code TEXT DEFAULT ""
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        challenge_id INTEGER,
        topic TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        status TEXT NOT NULL,
        code TEXT,
        notes TEXT,
        time_spent INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (challenge_id) REFERENCES challenges(id)
    )''')
    existing = c.execute("SELECT id FROM users WHERE username='admin'").fetchone()
    if not existing:
        c.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, 1)",
                  ('admin', generate_password_hash('admin123')))
    conn.commit()
    conn.close()

# --- USER MODEL ---
def get_user_by_username(username):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    return user

def create_user(username, hashed_password):
    conn = get_db()
    conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
    conn.commit()
    conn.close()

# --- CHALLENGE MODEL ---
def get_all_challenges():
    conn = get_db()
    challenges = conn.execute("SELECT * FROM challenges ORDER BY difficulty").fetchall()
    conn.close()
    return challenges

def get_challenge_by_id(cid):
    conn = get_db()
    c = conn.execute("SELECT * FROM challenges WHERE id=?", (cid,)).fetchone()
    conn.close()
    return c

def create_challenge(title, description, difficulty, starter_code):
    conn = get_db()
    conn.execute("INSERT INTO challenges (title, description, difficulty, starter_code) VALUES (?,?,?,?)",
                 (title, description, difficulty, starter_code))
    conn.commit()
    conn.close()

def delete_challenge(cid):
    conn = get_db()
    conn.execute("DELETE FROM challenges WHERE id=?", (cid,))
    conn.commit()
    conn.close()

# --- SESSION MODEL ---
def get_user_sessions(user_id):
    conn = get_db()
    sessions = conn.execute(
        "SELECT s.*, c.title as challenge_title FROM sessions s LEFT JOIN challenges c ON s.challenge_id=c.id WHERE s.user_id=? ORDER BY s.updated_at DESC",
        (user_id,)).fetchall()
    conn.close()
    return sessions

def get_session_by_id(sid, user_id):
    conn = get_db()
    s = conn.execute(
        "SELECT s.*, c.title as challenge_title FROM sessions s LEFT JOIN challenges c ON s.challenge_id=c.id WHERE s.id=? AND s.user_id=?",
        (sid, user_id)).fetchone()
    conn.close()
    return s

def create_session(user_id, challenge_id, topic, difficulty, status, code, notes, time_spent):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO sessions (user_id, challenge_id, topic, difficulty, status, code, notes, time_spent) VALUES (?,?,?,?,?,?,?,?)",
        (user_id, challenge_id, topic, difficulty, status, code, notes, time_spent)
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def update_session(sid, user_id, topic, difficulty, status, code, notes, time_spent):
    conn = get_db()
    conn.execute(
        "UPDATE sessions SET topic=?, difficulty=?, status=?, code=?, notes=?, time_spent=?, updated_at=CURRENT_TIMESTAMP WHERE id=? AND user_id=?",
        (topic, difficulty, status, code, notes, time_spent, sid, user_id)
    )
    conn.commit()
    conn.close()

def delete_session(sid, user_id):
    conn = get_db()
    conn.execute("DELETE FROM sessions WHERE id=? AND user_id=?", (sid, user_id))
    conn.commit()
    conn.close()

def get_user_stats(user_id):
    conn = get_db()
    stats = conn.execute(
        "SELECT COUNT(*) as total, SUM(time_spent) as total_time FROM sessions WHERE user_id=?",
        (user_id,)).fetchone()
    completed = conn.execute(
        "SELECT COUNT(*) as cnt FROM sessions WHERE user_id=? AND status='Completed'",
        (user_id,)).fetchone()
    conn.close()
    return stats, completed

def get_all_users_with_counts():
    conn = get_db()
    users = conn.execute(
        "SELECT u.username, COUNT(s.id) as session_count FROM users u LEFT JOIN sessions s ON u.id=s.user_id WHERE u.is_admin=0 GROUP BY u.id"
    ).fetchall()
    conn.close()
    return users