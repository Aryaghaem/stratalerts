"""
STRATALERTS - Web Interface (Fixed Version)
============================================
Full Flask app with working strategy submission.
"""

from flask import Flask, request, jsonify
import sqlite3
import os
import re
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'stratalerts-secret')

# ============================================================================
# DATABASE
# ============================================================================
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trading_alerts.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS strategies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        ticker TEXT NOT NULL,
        strategy_type TEXT NOT NULL,
        condition TEXT NOT NULL,
        threshold REAL,
        parameters TEXT,
        raw_description TEXT,
        active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        triggered_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        strategy_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()
    print(f"✓ Database initialised at {DB_PATH}")

init_db()

def get_or_create_user(email):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (email) VALUES (?)', (email,))
        user_id = c.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        c.execute('SELECT id FROM users WHERE email = ?', (email,))
        user_id = c.fetchone()['id']
    conn.close()
    return user_id

def save_strategy(user_id, parsed):
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT INTO strategies
        (user_id, ticker, strategy_type, condition, threshold, parameters, raw_description)
        VALUES (?, ?, ?, ?, ?, ?, ?)''', (
        user_id,
        parsed['ticker'],
        parsed['type'],
        parsed['condition'],
        parsed['threshold'],
        json.dumps(parsed.get('parameters', {})),
        parsed['raw_description'],
    ))
    sid = c.lastrowid
    conn.commit()
    conn.close()
    return sid

# ============================================================================
# STRATEGY PARSING
# ============================================================================
OPENAI_API_KEY = "sk-yourkeyhere"

def parse_with_openai(text):
    try:
        import urllib.request
        payload = json.dumps({
            "model": "gpt-4o-mini",
            "max_tokens": 200,
            "temperature": 0,
            "messages": [{"role": "user", "content":
                'Parse this trading strategy into JSON. Return ONLY valid JSON.\n'
                'Fields: ticker (string), type (PRICE/RSI/MACD/VOLUME/MA_CROSS), '
                'condition (above/below), threshold (number), parameters (object).\n'
                'Strategy: "' + text + '"'
            }]
        }).encode()
        req = urllib.request.Request(
            'https://api.openai.com/v1/chat/completions',
            data=payload,
            headers={'Authorization': 'Bearer ' + OPENAI_API_KEY,'Content-Type':'application/json'}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        raw = data['choices'][0]['message']['content'].strip()
        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'): raw = raw[4:]
        parsed = json.loads(raw.strip())
        return {
            'ticker': str(parsed.get('ticker', 'UNKNOWN')).upper(),
            'type': str(parsed.get('type', 'PRICE')).upper(),
            'condition': str(parsed.get('condition', 'above')).lower(),
            'threshold': float(parsed.get('threshold', 0)),
            'parameters': parsed.get('parameters', {}),
            'raw_description': text,
        }
    except Exception as e:
        print(f"OpenAI parse failed: {e}")
        return None

def parse_rule_based(text):
    t = text.lower()
    tickers = {"apple":"AAPL","aapl":"AAPL","tesla":"TSLA","tsla":"TSLA",
               "microsoft":"MSFT","msft":"MSFT","google":"GOOGL","googl":"GOOGL",
               "amazon":"AMZN","amzn":"AMZN","nvidia":"NVDA","nvda":"NVDA",
               "meta":"META","facebook":"META","bitcoin":"BTC-USD","btc":"BTC-USD",
               "ethereum":"ETH-USD","eth":"ETH-USD","spy":"SPY","qqq":"QQQ",
               "s&p":"SPY","nasdaq":"QQQ","netflix":"NFLX","nflx":"NFLX"}
    ticker = next((sym for name, sym in tickers.items() if name in t), "UNKNOWN")
    condition = "below" if any(w in t for w in ["below","under","drop","fall","dips"]) else "above"
    nums = re.findall(r'\$?\d[\d,]*\.?\d*', text)
    threshold = float(nums[0].replace('$','').replace(',','')) if nums else 0.0
    stype = ("RSI" if "rsi" in t else "MACD" if "macd" in t else
             "VOLUME" if "volume" in t else
             "MA_CROSS" if "moving average" in t or " ma " in t else "PRICE")
    return {"ticker": ticker, "type": stype, "condition": condition,
            "threshold": threshold, "parameters": {}, "raw_description": text}

def parse_strategy(text):
    return parse_with_openai(text) or parse_rule_based(text)

# ============================================================================
# FLASK ROUTES
# ============================================================================
@app.route('/')
def landing():
    return LANDING

@app.route('/app')
def dashboard():
    return APP_PAGE

@app.route('/api/strategy', methods=['POST'])
def api_strategy():
    data = request.get_json()
    email = data.get('email')
    text = data.get('strategy')
    if not email or not text:
        return jsonify(success=False, message="Missing email or strategy")
    user_id = get_or_create_user(email)
    parsed = parse_strategy(text)
    if not parsed:
        return jsonify(success=False, message="Could not parse strategy")
    save_strategy(user_id, parsed)
    return jsonify(success=True, message="Strategy submitted successfully")

# ============================================================================
# HTML PAGES (truncated landing/app with working submit button)
# ============================================================================
LANDING = """<html><body><h1>StratAlerts Landing Page</h1><a href="/app">Launch App</a></body></html>"""

APP_PAGE = """<html>
<body>
<h1>Dashboard</h1>
<div class="field">
  <label for="strategy">Enter Strategy</label>
  <textarea id="strategy" placeholder="e.g., Buy AAPL above $180"></textarea>
  <button class="sbtn" id="submitStrategy">Submit Strategy</button>
  <div class="res" id="resBox"></div>
</div>
<script>
document.getElementById('submitStrategy').addEventListener('click', async () => {
    const txt = document.getElementById('strategy').value.trim();
    const resBox = document.getElementById('resBox');
    if (!txt) return;
    resBox.style.display = 'none';
    try {
        const resp = await fetch('/api/strategy', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email: 'test@example.com', strategy: txt})
        });
        const data = await resp.json();
        resBox.style.display = 'block';
        resBox.className = data.success ? 'res ok' : 'res err';
        resBox.textContent = data.message;
    } catch (e) {
        resBox.style.display = 'block';
        resBox.className = 'res err';
        resBox.textContent = 'Network error';
    }
});
</script>
</body></html>"""

# ============================================================================
# RUN
# ============================================================================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
