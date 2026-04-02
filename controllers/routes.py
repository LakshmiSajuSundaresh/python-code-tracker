from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models.db import (
    get_user_by_username, create_user,
    get_all_challenges, get_challenge_by_id, create_challenge, delete_challenge,
    get_user_sessions, get_session_by_id, create_session, update_session,
    delete_session, get_user_stats, get_all_users_with_counts
)
import subprocess, sys, sqlite3

main = Blueprint('main', __name__)

# --- AUTH ---
@main.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    if session.get('is_admin'):
        return redirect(url_for('main.admin_dashboard'))
    return redirect(url_for('main.dashboard'))

@main.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        if not username or not password:
            error = 'All fields are required.'
        else:
            try:
                create_user(username, generate_password_hash(password))
                return redirect(url_for('main.login', registered=1))
            except sqlite3.IntegrityError:
                error = 'Username already taken. Please choose another.'
    return render_template('register.html', error=error)

@main.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    registered = request.args.get('registered')
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        user = get_user_by_username(username)
        if not user:
            error = 'No account found. Please register first.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password. Please try again.'
        else:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = bool(user['is_admin'])
            return redirect(url_for('main.index'))
    return render_template('login.html', error=error, registered=registered)

@main.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))

# --- USER ---
@main.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for('main.login'))
    sessions = get_user_sessions(session['user_id'])
    challenges = get_all_challenges()
    stats, completed = get_user_stats(session['user_id'])
    return render_template('dashboard.html', sessions=sessions, challenges=challenges, stats=stats, completed=completed)

@main.route('/practice')
def practice():
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for('main.login'))
    challenge_id = request.args.get('challenge_id')
    challenge = get_challenge_by_id(challenge_id) if challenge_id else None
    return render_template('practice.html', challenge=challenge, resume_session=None)

@main.route('/practice/resume/<int:sid>')
def resume_session(sid):
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for('main.login'))
    s = get_session_by_id(sid, session['user_id'])
    if not s:
        return redirect(url_for('main.dashboard'))
    challenge = get_challenge_by_id(s['challenge_id']) if s['challenge_id'] else None
    return render_template('practice.html', challenge=challenge, resume_session=s)

@main.route('/run_code', methods=['POST'])
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

@main.route('/save_session', methods=['POST'])
def save_session():
    if 'user_id' not in session or session.get('is_admin'):
        return jsonify({'error': 'Not logged in'}), 401
    data = request.json
    sid = data.get('session_id')
    if sid:
        update_session(
            sid, session['user_id'],
            data['topic'], data['difficulty'], data['status'],
            data.get('code', ''), data.get('notes', ''), data.get('time_spent', 0)
        )
        return jsonify({'success': True, 'session_id': sid})
    else:
        new_id = create_session(
            session['user_id'], data.get('challenge_id'),
            data['topic'], data['difficulty'], data['status'],
            data.get('code', ''), data.get('notes', ''), data.get('time_spent', 0)
        )
        return jsonify({'success': True, 'session_id': new_id})

@main.route('/session/<int:sid>')
def view_session(sid):
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for('main.login'))
    s = get_session_by_id(sid, session['user_id'])
    if not s:
        return redirect(url_for('main.dashboard'))
    return render_template('view_session.html', s=s)

@main.route('/delete_session/<int:sid>', methods=['POST'])
def delete_session_route(sid):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    delete_session(sid, session['user_id'])
    return redirect(url_for('main.dashboard'))

# --- ADMIN ---
@main.route('/admin')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('main.login'))
    challenges = get_all_challenges()
    users = get_all_users_with_counts()
    return render_template('admin.html', challenges=challenges, users=users)

@main.route('/admin/add_challenge', methods=['POST'])
def add_challenge():
    if not session.get('is_admin'):
        return redirect(url_for('main.login'))
    create_challenge(
        request.form['title'].strip(),
        request.form['description'].strip(),
        request.form['difficulty'],
        request.form.get('starter_code', '').strip()
    )
    return redirect(url_for('main.admin_dashboard'))

@main.route('/admin/delete_challenge/<int:cid>', methods=['POST'])
def delete_challenge_route(cid):
    if not session.get('is_admin'):
        return redirect(url_for('main.login'))
    delete_challenge(cid)
    return redirect(url_for('main.admin_dashboard'))