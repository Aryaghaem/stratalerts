from flask import Flask, render_template_string, request, jsonify
import json
import sqlite3
import os
import re

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('alerts.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS strategies (
            id INTEGER PRIMARY KEY,
            email TEXT,
            ticker TEXT,
            strategy_type TEXT,
            condition TEXT,
            threshold REAL,
            raw_description TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def parse_strategy(text):
    text_lower = text.lower()
    tickers = {"apple": "AAPL", "tesla": "TSLA", "microsoft": "MSFT", "bitcoin": "BTC-USD"}
    ticker = next((symbol for name, symbol in tickers.items() if name in text_lower), "UNKNOWN")
    condition = "above" if any(w in text_lower for w in ["above", "over"]) else "below"
    numbers = re.findall(r'\d+', text)
    threshold = float(numbers[0]) if numbers else 0
    return {"ticker": ticker, "type": "PRICE", "condition": condition, "threshold": threshold, "raw_description": text}

@app.route('/')
def home():
    return "<h1>StratAlerts</h1><p><a href='/app'>Create Alert</a></p>"

@app.route('/app')
def app_page():
    return """<html><body><h1>Create Alert</h1><form id='f'><input id='e' placeholder='Email'><textarea id='s' placeholder='Strategy'></textarea><button type='submit'>Create</button></form><div id='r'></div><script>document.getElementById('f').onsubmit=async(e)=>{e.preventDefault();const res=await fetch('/add-strategy',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:document.getElementById('e').value,strategy:document.getElementById('s').value})});const data=await res.json();document.getElementById('r').innerHTML=data.success?'✅ Created!':'❌ Error';}</script></body></html>"""

@app.route('/add-strategy', methods=['POST'])
def add_strategy():
    try:
        data = request.json
        parsed = parse_strategy(data['strategy'])
        conn = sqlite3.connect('alerts.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO strategies (email, ticker, strategy_type, condition, threshold, raw_description) VALUES (?, ?, ?, ?, ?, ?)',
                      (data['email'], parsed['ticker'], parsed['type'], parsed['condition'], parsed['threshold'], parsed['raw_description']))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'parsed': parsed})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
