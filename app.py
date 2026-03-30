from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, subprocess, sys, os

app = Flask(__name__)
app.secret_key = 'devops_secret_key_2024'
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
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (challenge_id) REFERENCES challenges(id)
    )''')
    existing = c.execute("SELECT id FROM users WHERE username='admin'").fetchone()
    if not existing:
        c.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, 1)",
                  ('admin', generate_password_hash('admin123')))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        if not username or not password:
            error = 'All fields are required.'
        else:
            try:
                conn = get_db()
                conn.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                             (username, generate_password_hash(password)))
                conn.commit()
                conn.close()
                return redirect(url_for('login', registered=1))
            except sqlite3.IntegrityError:
                error = 'Username already taken. Please choose another.'
    return render_template('register.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    registered = request.args.get('registered')
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        conn.close()
        if not user:
            error = 'No account found. Please register first.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password. Please try again.'
        else:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = bool(user['is_admin'])
            return redirect(url_for('index'))
    return render_template('login.html', error=error, registered=registered)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for('login'))
    conn = get_db()
    sessions = conn.execute(
        "SELECT s.*, c.title as challenge_title FROM sessions s LEFT JOIN challenges c ON s.challenge_id=c.id WHERE s.user_id=? ORDER BY s.created_at DESC",
        (session['user_id'],)).fetchall()
    challenges = conn.execute("SELECT * FROM challenges ORDER BY difficulty").fetchall()
    stats = conn.execute(
        "SELECT COUNT(*) as total, SUM(time_spent) as total_time FROM sessions WHERE user_id=?",
        (session['user_id'],)).fetchone()
    completed = conn.execute(
        "SELECT COUNT(*) as cnt FROM sessions WHERE user_id=? AND status='Completed'",
        (session['user_id'],)).fetchone()
    conn.close()
    return render_template('dashboard.html', sessions=sessions, challenges=challenges, stats=stats, completed=completed)

@app.route('/practice')
def practice():
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for('login'))
    challenge_id = request.args.get('challenge_id')
    challenge = None
    if challenge_id:
        conn = get_db()
        challenge = conn.execute("SELECT * FROM challenges WHERE id=?", (challenge_id,)).fetchone()
        conn.close()
    return render_template('practice.html', challenge=challenge)

@app.route('/run_code', methods=['POST'])
def run_code():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    code = request.json.get('code', '')
    try:
        result = subprocess.run(
            [sys.executable, '-c', code],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout or result.stderr or '(no output)'
    except subprocess.TimeoutExpired:
        output = 'Error: Code timed out (10s limit).'
    except Exception as e:
        output = f'Error: {str(e)}'
    return jsonify({'output': output})

@app.route('/save_session', methods=['POST'])
def save_session():
    if 'user_id' not in session or session.get('is_admin'):
        return jsonify({'error': 'Not logged in'}), 401
    data = request.json
    conn = get_db()
    conn.execute(
        "INSERT INTO sessions (user_id, challenge_id, topic, difficulty, status, code, notes, time_spent) VALUES (?,?,?,?,?,?,?,?)",
        (session['user_id'], data.get('challenge_id'), data['topic'], data['difficulty'],
         data['status'], data.get('code', ''), data.get('notes', ''), data.get('time_spent', 0))
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/delete_session/<int:sid>', methods=['POST'])
def delete_session(sid):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    conn.execute("DELETE FROM sessions WHERE id=? AND user_id=?", (sid, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/admin')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    conn = get_db()
    challenges = conn.execute("SELECT * FROM challenges").fetchall()
    users = conn.execute(
        "SELECT u.username, COUNT(s.id) as session_count FROM users u LEFT JOIN sessions s ON u.id=s.user_id WHERE u.is_admin=0 GROUP BY u.id"
    ).fetchall()
    conn.close()
    return render_template('admin.html', challenges=challenges, users=users)

@app.route('/admin/add_challenge', methods=['POST'])
def add_challenge():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    title = request.form['title'].strip()
    description = request.form['description'].strip()
    difficulty = request.form['difficulty']
    starter_code = request.form.get('starter_code', '').strip()
    conn = get_db()
    conn.execute("INSERT INTO challenges (title, description, difficulty, starter_code) VALUES (?,?,?,?)",
                 (title, description, difficulty, starter_code))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_challenge/<int:cid>', methods=['POST'])
def delete_challenge(cid):
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    conn = get_db()
    conn.execute("DELETE FROM challenges WHERE id=?", (cid,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
