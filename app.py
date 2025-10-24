from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import openai

# Extra imports for reminders
from apscheduler.schedulers.background import BackgroundScheduler
from twilio.rest import Client

DATABASE = 'health_fitness.db'
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = "change_this_secret_for_production"

# OpenAI configuration - set your OPENAI_API_KEY in the environment (do NOT put it in client-side code)
openai.api_key = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Twilio credentials (set as environment variables!)
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_FROM = "whatsapp:+13262010859"  # Twilio Sandbox number
twilio_client = Client(TWILIO_SID, TWILIO_AUTH)
print(os.getenv("TWILIO_SID"))
print(os.getenv("TWILIO_AUTH"))

scheduler = BackgroundScheduler()
scheduler.start()


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.executescript(f.read())
    # Add reminders table if not exists
    db.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            tablet_name TEXT,
            phone TEXT,
            time TEXT,
            days INTEGER,
            created_at TIMESTAMP
        )
    """)
    db.commit()
    


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/')
def index():
    # Basic landing page
    return render_template('index.html')


@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        age = request.form.get('age')
        gender = request.form.get('gender')
        height = request.form.get('height')
        weight = request.form.get('weight')
        goal = request.form.get('goal')
        photo = request.form.get('photo')  # base64 or url (optional)

        db = get_db()
        cur = db.execute("SELECT id FROM users WHERE username=?", (username,))
        if cur.fetchone():
            return "User exists", 400
        pw_hash = generate_password_hash(password)
        db.execute("INSERT INTO users (username, password_hash, age, gender, height, weight, goal, photo, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                   (username, pw_hash, age, gender, height, weight, goal, photo, datetime.utcnow()))
        db.commit()
        return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        db = get_db()
        cur = db.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cur.fetchone()
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('health_dashboard'))
        return "Invalid credentials", 401
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapper


@app.route('/health')
@login_required
def health_dashboard():
    return render_template('dashboard_health.html')


@app.route('/fitness')
@login_required
def fitness_dashboard():
    return render_template('dashboard_fitness.html')


@app.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    db = get_db()
    uid = session['user_id']
    if request.method == 'POST':
        age = request.form.get('age')
        gender = request.form.get('gender')
        height = request.form.get('height')
        weight = request.form.get('weight')
        goal = request.form.get('goal')
        photo = request.form.get('photo')
        db.execute("UPDATE users SET age=?, gender=?, height=?, weight=?, goal=?, photo=? WHERE id=?",
                   (age, gender, height, weight, goal, photo, uid))
        db.commit()
        return redirect(url_for('profile'))
    cur = db.execute("SELECT * FROM users WHERE id=?", (uid,))
    user = cur.fetchone()
    return render_template('profile.html', user=user)


# ================= WATER API =================
@app.route('/api/water', methods=['GET','POST'])
@login_required
def api_water():
    db = get_db()
    uid = session['user_id']
    if request.method == 'POST':
        amount = int(request.json.get('amount',0))
        ts = datetime.utcnow()
        db.execute("INSERT INTO water_logs (user_id, amount_ml, ts) VALUES (?,?,?)", (uid, amount, ts))
        db.commit()
        return jsonify(success=True)
    else:
        cur = db.execute("SELECT amount_ml, ts FROM water_logs WHERE user_id=? ORDER BY ts DESC LIMIT 50", (uid,))
        rows = [dict(r) for r in cur.fetchall()]
        return jsonify(rows)


# ================= TABLET API =================
@app.route('/api/tablet', methods=['GET','POST'])
@login_required
def api_tablet():
    db = get_db()
    uid = session['user_id']
    if request.method == 'POST':
        name = request.json.get('name')
        dosage = request.json.get('dosage')
        time = request.json.get('time')
        db.execute("INSERT INTO tablets (user_id, name, dosage, time, added_at) VALUES (?,?,?,?,?)",
                   (uid, name, dosage, time, datetime.utcnow()))
        db.commit()
        return jsonify(success=True)
    else:
        cur = db.execute("SELECT * FROM tablets WHERE user_id=?", (uid,))
        return jsonify([dict(r) for r in cur.fetchall()])


# ================= GLUCOSE API =================
@app.route('/api/glucose', methods=['GET','POST'])
@login_required
def api_glucose():
    db = get_db()
    uid = session['user_id']
    if request.method == 'POST':
        value = float(request.json.get('value'))
        ts = datetime.utcnow()
        db.execute("INSERT INTO glucose (user_id, value, ts) VALUES (?,?,?)", (uid, value, ts))
        db.commit()
        return jsonify(success=True)
    else:
        cur = db.execute("SELECT * FROM glucose WHERE user_id=? ORDER BY ts DESC LIMIT 50", (uid,))
        return jsonify([dict(r) for r in cur.fetchall()])


# ================= BLOOD PRESSURE API =================
@app.route('/api/bp', methods=['GET', 'POST'])
@login_required
def api_bp():
    db = get_db()
    uid = session['user_id']

    if request.method == 'POST':
        data = request.get_json()
        systolic = float(data.get('systolic'))
        diastolic = float(data.get('diastolic'))
        ts = datetime.utcnow()
        db.execute(
            "INSERT INTO blood_pressure (user_id, systolic, diastolic, ts) VALUES (?,?,?,?)",
            (uid, systolic, diastolic, ts)
        )
        db.commit()
        return jsonify(success=True)

    else:
        cur = db.execute(
            "SELECT systolic, diastolic, ts FROM blood_pressure WHERE user_id=? ORDER BY ts DESC LIMIT 50",
            (uid,)
        )
        rows = [dict(r) for r in cur.fetchall()]
        return jsonify(rows)


# ================= LEADERBOARD =================
@app.route('/api/leaderboard')
def api_leaderboard():
    db = get_db()
    cur = db.execute("""
        SELECT u.id, u.username,
            IFNULL(SUM(w.amount_ml),0) as total_water_ml,
            (SELECT COUNT(*) FROM tablets t WHERE t.user_id=u.id) as tablets_count,
            (SELECT COUNT(*) FROM glucose g WHERE g.user_id=u.id) as glucose_count
        FROM users u
        LEFT JOIN water_logs w ON w.user_id = u.id
        GROUP BY u.id
        ORDER BY (IFNULL(SUM(w.amount_ml),0)/1000 + (SELECT COUNT(*) FROM tablets t WHERE t.user_id=u.id) + (SELECT COUNT(*) FROM glucose g WHERE g.user_id=u.id)) DESC
        LIMIT 100
    """)
    rows = [dict(r) for r in cur.fetchall()]
    for r in rows:
        r['score'] = round((r['total_water_ml']/1000.0) + r['tablets_count'] + r['glucose_count'],2)
    return jsonify(rows)


@app.route('/leaderboard')
def leaderboard_page():
    return render_template('leaderboard.html')


# ================= AI COACH =================
@app.route('/api/coach', methods=['POST'])
@login_required
def api_coach():
    db = get_db()
    uid = session['user_id']
    cur = db.execute("SELECT SUM(amount_ml) as today_ml FROM water_logs WHERE user_id=? AND date(ts)=date('now')", (uid,))
    today = cur.fetchone()
    ml = today['today_ml'] or 0
    msgs = []
    if ml < 2000:
        msgs.append(f"You've had {int(ml)} ml water today. Try to reach at least 2000 ml.")
    else:
        msgs.append(f"Great — you've had {int(ml)} ml water today. Keep it up!")
    cur2 = db.execute("SELECT COUNT(*) as c FROM tablets WHERE user_id=?", (uid,))
    tab_count = cur2.fetchone()['c']
    if tab_count>0:
        msgs.append("You have active tablet reminders. Mark as taken when you do.")
    return jsonify({ "messages": msgs })


# ================= CHAT API =================
@app.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    data = request.get_json() or {}
    user_message = data.get('message', '').strip()
    if not user_message:
        return jsonify({'error': 'message required'}), 400

    try:
        messages = [
            { 'role': 'system', 'content': 'You are a helpful assistant for a Health & Fitness web application. Keep answers concise and friendly.'},
            { 'role': 'user', 'content': user_message}
        ]
        resp = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=512,
            temperature=0.7,
        )
        reply = resp['choices'][0]['message']['content'].strip()
        return jsonify({'reply': reply})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ================= REMINDER API (NEW) =================
def send_whatsapp_message(to, message):
    twilio_client.messages.create(
        from_=TWILIO_FROM,
        body=message,
        to=f'whatsapp:{to}'
    )

def schedule_reminder(reminder_id, phone, tablet_name, time_str, days):
    now = datetime.now()
    reminder_time = datetime.strptime(time_str, "%H:%M").replace(
        year=now.year, month=now.month, day=now.day
    )
    for i in range(days):
        run_time = reminder_time + timedelta(days=i)
        scheduler.add_job(
            send_whatsapp_message,
            'date',
            run_date=run_time,
            args=[phone, f"💊 Reminder: Take your tablet {tablet_name}"]
        )

@app.route('/api/reminder', methods=['POST'])
@login_required
def api_reminder():
    db = get_db()
    uid = session['user_id']
    data = request.json
    tablet_name = data.get('tablet_name')
    time_str = data.get('time')
    days = int(data.get('days',1))
    phone = data.get('phone')

    db.execute("INSERT INTO reminders (user_id, tablet_name, phone, time, days, created_at) VALUES (?,?,?,?,?,?)",
               (uid, tablet_name, phone, time_str, days, datetime.utcnow()))
    db.commit()
    rid = db.execute("SELECT last_insert_rowid() as id").fetchone()['id']

    schedule_reminder(rid, phone, tablet_name, time_str, days)
    return jsonify(success=True, message="Reminder scheduled!")


if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        with app.app_context():
            init_db()
        print("Initialized DB")
    app.run(debug=True)
