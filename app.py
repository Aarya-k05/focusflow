from flask import Flask, render_template, request, redirect, session, url_for
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'focusflowsecret'

cred = credentials.Certificate('firebase_config.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route('/')
def home():
    if 'user' in session:
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        user_ref = db.collection('users').document(email)
        user = user_ref.get()
        if user.exists:
            session['user'] = email
            session['name'] = user.to_dict().get('name', 'User')
            return redirect('/dashboard')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        user_ref = db.collection('users').document(email)
        user_ref.set({'name': name})
        session['user'] = email
        session['name'] = name
        return redirect('/dashboard')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    
    email = session['user']
    today = datetime.now().strftime('%Y-%m-%d')
    sessions_ref = db.collection('users').document(email).collection('sessions')
    today_sessions = sessions_ref.where('date', '==', today).stream()
    sessions_list = [{
        'subject': s.to_dict()['subject'],
        'minutes': s.to_dict()['minutes'],
        'time': s.to_dict()['time']
    } for s in today_sessions]

    weekly_stats = {}
    for i in range(7):
        day = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        daily_sessions = sessions_ref.where('date', '==', day).stream()
        count = 0
        total_minutes = 0
        for s in daily_sessions:
            data = s.to_dict()
            count += 1
            total_minutes += data['minutes']
        weekly_stats[day] = {'sessions': count, 'minutes': total_minutes}

    return render_template('dashboard.html', name=session['name'], today_sessions=sessions_list, weekly_stats=weekly_stats)

@app.route('/start', methods=['GET', 'POST'])
def start():
    if 'user' not in session:
        return redirect('/login')
    if request.method == 'POST':
        subject = request.form['subject']
        duration = int(request.form['duration'])
        session_data = {
            'subject': subject,
            'minutes': 25,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M')
        }
        user_sessions = db.collection('users').document(session['user']).collection('sessions')
        user_sessions.add(session_data)
        return redirect('/dashboard')
    return render_template('index.html')