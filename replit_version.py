"""
STRATALERTS - Replit Deployment Version
========================================
Single file for easy Replit deployment
"""

from flask import Flask, render_template_string, request, jsonify
import json
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-in-production')

# Get API key from environment variable (set in Replit Secrets)
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# ============================================================================
# DATABASE
# ============================================================================

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
            raw_description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()


def add_strategy_to_db(email, strategy):
    conn = sqlite3.connect('alerts.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO strategies (email, ticker, strategy_type, condition, threshold, raw_description)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (email, strategy.get('ticker'), strategy.get('type'), strategy.get('condition'), 
          strategy.get('threshold'), strategy.get('raw_description')))
    strategy_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return strategy_id


# ============================================================================
# AI PARSER (Simplified for Replit)
# ============================================================================

def parse_strategy(text):
    """Simple fallback parser - works without AI"""
    import re
    
    text_lower = text.lower()
    
    # Extract ticker
    tickers = {
        "apple": "AAPL", "aapl": "AAPL",
        "tesla": "TSLA", "tsla": "TSLA",
        "microsoft": "MSFT", "msft": "MSFT",
        "google": "GOOGL", "googl": "GOOGL",
        "amazon": "AMZN", "amzn": "AMZN",
        "nvidia": "NVDA", "nvda": "NVDA",
        "meta": "META", "facebook": "META",
        "bitcoin": "BTC-USD", "btc": "BTC-USD",
    }
    
    ticker = "UNKNOWN"
    for name, symbol in tickers.items():
        if name in text_lower:
            ticker = symbol
            break
    
    # Detect condition
    if any(word in text_lower for word in ["above", "over", "exceed", "break"]):
        condition = "above"
    elif any(word in text_lower for word in ["below", "under", "drop"]):
        condition = "below"
    else:
        condition = "above"
    
    # Extract threshold
    numbers = re.findall(r'\d+\.?\d*', text)
    threshold = float(numbers[0]) if numbers else 100.0
    
    # Detect type
    if "rsi" in text_lower:
        strategy_type = "RSI"
    elif "volume" in text_lower:
        strategy_type = "VOLUME"
    else:
        strategy_type = "PRICE"
    
    return {
        "ticker": ticker,
        "type": strategy_type,
        "condition": condition,
        "threshold": threshold,
        "raw_description": text
    }


# ============================================================================
# WEB PAGES
# ============================================================================

LANDING_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StratAlerts - Never Miss a Trade</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #0a0a0f;
            color: white;
        }
        .navbar {
            position: fixed;
            top: 0;
            width: 100%;
            background: rgba(10, 10, 15, 0.95);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid #27272a;
            padding: 16px 0;
            z-index: 1000;
        }
        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .logo {
            font-size: 24px;
            font-weight: 800;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .btn-primary {
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            padding: 10px 24px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
        }
        .hero {
            padding: 180px 24px 120px;
            text-align: center;
        }
        .hero h1 {
            font-size: 72px;
            font-weight: 900;
            line-height: 1.1;
            margin-bottom: 24px;
        }
        .hero p {
            font-size: 20px;
            color: #a1a1aa;
            margin-bottom: 40px;
        }
        @media (max-width: 768px) {
            .hero h1 { font-size: 48px; }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <div class="logo">StratAlerts</div>
            <a href="/app" class="btn-primary">Get Started →</a>
        </div>
    </nav>
    
    <div class="hero">
        <h1>Never Miss a Trade.<br>Ever Again.</h1>
        <p>AI-powered trading alerts that monitor markets 24/7</p>
        <a href="/app" class="btn-primary" style="padding: 16px 32px; font-size: 16px;">Start Free Trial →</a>
    </div>
</body>
</html>
"""

APP_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Create Alert - StratAlerts</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #0a0a0f;
            color: white;
            padding: 100px 24px;
        }
        .card {
            max-width: 700px;
            margin: 0 auto;
            background: #12121a;
            border: 1px solid #27272a;
            border-radius: 16px;
            padding: 48px;
        }
        h1 { font-size: 32px; margin-bottom: 12px; }
        .subtitle { color: #a1a1aa; margin-bottom: 40px; }
        .input-group { margin-bottom: 24px; }
        label { display: block; font-weight: 600; margin-bottom: 8px; font-size: 14px; }
        input, textarea {
            width: 100%;
            padding: 14px;
            background: #1a1a24;
            border: 1px solid #27272a;
            border-radius: 10px;
            color: white;
            font-size: 16px;
            font-family: 'Inter', sans-serif;
        }
        textarea { min-height: 120px; }
        button {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            border: none;
            border-radius: 10px;
            font-weight: 700;
            cursor: pointer;
            font-size: 16px;
        }
        .result {
            margin-top: 24px;
            padding: 20px;
            border-radius: 12px;
            display: none;
        }
        .success {
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid #10b981;
            color: #10b981;
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>Create Your First Alert</h1>
        <p class="subtitle">Describe your trading strategy in plain English</p>
        
        <form id="form">
            <div class="input-group">
                <label>Email</label>
                <input type="email" id="email" required placeholder="you@example.com">
            </div>
            <div class="input-group">
                <label>Trading Strategy</label>
                <textarea id="strategy" required placeholder="Alert me when Apple goes above $220"></textarea>
            </div>
            <button type="submit">🚀 Create Alert</button>
        </form>
        
        <div class="result" id="result"></div>
    </div>
    
    <script>
        document.getElementById('form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('email').value;
            const strategy = document.getElementById('strategy').value;
            
            const response = await fetch('/add-strategy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, strategy })
            });
            
            const data = await response.json();
            const result = document.getElementById('result');
            result.style.display = 'block';
            
            if (data.success) {
                result.className = 'result success';
                result.innerHTML = `
                    <h3>✅ Alert Created!</h3>
                    <p><strong>Ticker:</strong> ${data.parsed.ticker}</p>
                    <p>We're monitoring 24/7!</p>
                `;
                document.getElementById('strategy').value = '';
            }
        });
    </script>
</body>
</html>
"""


@app.route('/')
def landing():
    return LANDING_PAGE

@app.route('/app')
def app_page():
    return APP_PAGE

@app.route('/add-strategy', methods=['POST'])
def add_strategy():
    try:
        data = request.json
        email = data.get('email')
        strategy_text = data.get('strategy')
        
        parsed = parse_strategy(strategy_text)
        strategy_id = add_strategy_to_db(email, parsed)
        
        return jsonify({'success': True, 'parsed': parsed})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    # Replit uses port from environment
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
