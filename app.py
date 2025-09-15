# app.py - Flask app for StyleMate AI Fashion Advisor.
# Handles routes, auth, SQLite, rule-based suggestions, optional OpenAI.

from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
try:
    from openai import OpenAI
    import httpx  # For custom HTTP client
except ImportError:
    OpenAI = None

load_dotenv()  # Load .env variables
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')  # For session/flash

# Database init - creates users table.
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)''')
    conn.commit()
    conn.close()

init_db()  # Run on startup

# Rule-based suggestion engine.
# Detects colors, categorizes clothes, composes suggestion based on event.
def suggest_rule_based(event: str, clothes_text: str) -> str:
    # Detect colors in clothes text.
    colors = ['red', 'blue', 'green', 'black', 'white', 'gray', 'yellow', 'pink']
    detected_colors = [c for c in colors if c in clothes_text.lower()]

    # Categorize clothes (comma-separated).
    items = [item.strip().lower() for item in clothes_text.split(',')]
    categories = {'tops': [], 'bottoms': [], 'dresses': [], 'outer': [], 'shoes': [], 'accessories': []}
    for item in items:
        if 'shirt' in item or 'top' in item: categories['tops'].append(item)
        elif 'jeans' in item or 'pants' in item or 'skirt' in item: categories['bottoms'].append(item)
        elif 'dress' in item: categories['dresses'].append(item)
        elif 'jacket' in item or 'coat' in item: categories['outer'].append(item)
        elif 'shoes' in item or 'sneakers' in item or 'boots' in item: categories['shoes'].append(item)
        else: categories['accessories'].append(item)

    # Event-based suggestion (from Streamlit app).
    event = event.lower()
    if 'interview' in event:
        outfit = "Professional: Button-up shirt with slacks or skirt."
        color_tip = "Neutral colors (black, navy, gray)."
        accessories = "Minimal: Watch, simple earrings, polished shoes."
    elif 'party' in event:
        outfit = "Fun and vibrant: Stylish top with jeans."
        color_tip = "Bright or metallic colors to stand out."
        accessories = "Statement jewelry, clutch, heels or boots."
    elif 'college' in event:
        outfit = "Casual: Jeans with t-shirt or hoodie."
        color_tip = "Mix casual colors; earth tones for relaxed vibe."
        accessories = "Backpack, sneakers, cap or scarf."
    elif 'wedding' in event:
        outfit = "Elegant dress or suit."
        color_tip = "Pastels or jewel tones."
        accessories = "Delicate jewelry, dress shoes, small bag."
    else:
        outfit = "Comfortable and confident: Mix and match your clothes."
        color_tip = "Neutrals work for any occasion."
        accessories = "Keep it simple."

    # Personalize with detected items/colors.
    if detected_colors: color_tip += f" Detected: {', '.join(detected_colors)}."
    if categories['tops'] or categories['bottoms']:
        outfit += f" Use your {', '.join(categories['tops'] + categories['bottoms'])}."

    return f"<b>Outfit:</b> {outfit}<br><b>Color Tip:</b> {color_tip}<br><b>Accessories:</b> {accessories}<br><b>Tip:</b> Match your vibe to the event!"

# OpenAI wrapper - returns None if unavailable or fails.
def call_openai(event: str, clothes_text: str, temperature: float = 0.7) -> str | None:
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or OpenAI is None:
        return None
    try:
        client = OpenAI(api_key=api_key, http_client=httpx.Client(proxies=None))  # Disable proxies
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"""
                Suggest a stylish outfit for {event} using clothes: {clothes_text}.
                Format as:
                - Outfit: [suggestion]
                - Color Tip: [tip]
                - Accessories: [accessories]
                - Tip: [styling tip]
            """}],
            temperature=temperature,
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI error: {e}")  # For debugging
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    suggestion = None
    use_ai_notice = None
    if request.method == 'POST':
        event = request.form.get('event')
        clothes_text = request.form.get('clothes')
        use_ai = request.form.get('use_ai') == 'on'
        if not event or not clothes_text:
            flash('Please enter event and clothes.')
            return redirect(url_for('index'))
        if use_ai:
            ai_suggestion = call_openai(event, clothes_text)
            if ai_suggestion:
                suggestion = ai_suggestion
            else:
                use_ai_notice = "AI unavailable — using rule-based suggestions."
                suggestion = suggest_rule_based(event, clothes_text)
        else:
            suggestion = suggest_rule_based(event, clothes_text)
    return render_template('index.html', suggestion=suggestion, use_ai_notice=use_ai_notice)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Username and password required.')
            return redirect(url_for('signup'))
        hashed_pw = generate_password_hash(password)
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
            conn.commit()
            flash('Signup successful! Please login.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already taken.')
        finally:
            conn.close()
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            flash('Login successful!')
            return redirect(url_for('profile'))
        flash('Invalid username or password.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out.')
    return redirect(url_for('index'))

@app.route('/profile')
def profile():
    if 'user_id' in session:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT username FROM users WHERE id = ?", (session['user_id'],))
        username = c.fetchone()[0]
        conn.close()
        return render_template('profile.html', username=username)
    flash('Please login.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
