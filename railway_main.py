"""
STRATALERTS - Railway Deployment Version
=========================================
Optimized for Railway deployment
"""

from flask import Flask, render_template_string, request, jsonify
import json
import sqlite3
from datetime import datetime
import os
import re

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# ============================================================================
# DATABASE SETUP
# ============================================================================

def init_db():
    """Initialize database"""
    conn = sqlite3.connect('alerts.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            ticker TEXT NOT NULL,
            strategy_type TEXT NOT NULL,
            condition TEXT NOT NULL,
            threshold REAL,
            raw_description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("✓ Database initialized")

init_db()


def add_strategy_to_db(email, strategy):
    """Save strategy to database"""
    conn = sqlite3.connect('alerts.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO strategies (email, ticker, strategy_type, condition, threshold, raw_description)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        email,
        strategy.get('ticker', 'UNKNOWN'),
        strategy.get('type', 'PRICE'),
        strategy.get('condition', 'above'),
        strategy.get('threshold', 0),
        strategy.get('raw_description', '')
    ))
    strategy_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return strategy_id


# ============================================================================
# STRATEGY PARSER (Simple Version - No API Required)
# ============================================================================

def parse_strategy(text):
    """Parse trading strategy from natural language"""
    text_lower = text.lower()
    
    # Common tickers
    tickers = {
        "apple": "AAPL", "aapl": "AAPL",
        "tesla": "TSLA", "tsla": "TSLA",
        "microsoft": "MSFT", "msft": "MSFT",
        "google": "GOOGL", "googl": "GOOGL",
        "amazon": "AMZN", "amzn": "AMZN",
        "nvidia": "NVDA", "nvda": "NVDA",
        "meta": "META", "facebook": "META",
        "bitcoin": "BTC-USD", "btc": "BTC-USD",
        "ethereum": "ETH-USD", "eth": "ETH-USD",
    }
    
    # Find ticker
    ticker = "UNKNOWN"
    for name, symbol in tickers.items():
        if name in text_lower:
            ticker = symbol
            break
    
    # Detect condition
    if any(word in text_lower for word in ["above", "over", "exceed", "break", "hit"]):
        condition = "above"
    elif any(word in text_lower for word in ["below", "under", "drop", "fall"]):
        condition = "below"
    else:
        condition = "above"
    
    # Extract price/threshold
    numbers = re.findall(r'\$?\d+[\d,]*\.?\d*', text)
    threshold = 0
    if numbers:
        # Clean number (remove $ and commas)
        num_str = numbers[0].replace('$', '').replace(',', '')
        try:
            threshold = float(num_str)
        except:
            threshold = 0
    
    # Detect indicator type
    if "rsi" in text_lower:
        strategy_type = "RSI"
    elif "macd" in text_lower:
        strategy_type = "MACD"
    elif "volume" in text_lower:
        strategy_type = "VOLUME"
    elif "moving average" in text_lower or "ma" in text_lower:
        strategy_type = "MA"
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
# HTML TEMPLATES
# ============================================================================

LANDING_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StratAlerts - Never Miss a Trade</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #0a0a0f; color: white; }
        .navbar {
            position: fixed; top: 0; width: 100%; background: rgba(10, 10, 15, 0.95);
            backdrop-filter: blur(10px); border-bottom: 1px solid #27272a; padding: 16px 0; z-index: 1000;
        }
        .nav-container {
            max-width: 1200px; margin: 0 auto; padding: 0 24px;
            display: flex; justify-content: space-between; align-items: center;
        }
        .logo {
            font-size: 24px; font-weight: 800;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .btn { 
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white; padding: 10px 24px; border-radius: 8px;
            text-decoration: none; font-weight: 600;
        }
        .hero { padding: 180px 24px 120px; text-align: center; }
        .hero h1 { font-size: 72px; font-weight: 900; line-height: 1.1; margin-bottom: 24px; }
        .hero p { font-size: 20px; color: #a1a1aa; margin-bottom: 40px; max-width: 600px; margin-left: auto; margin-right: auto; }
        @media (max-width: 768px) { .hero h1 { font-size: 48px; } }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <div class="logo">StratAlerts</div>
            <a href="/app" class="btn">Get Started →</a>
        </div>
    </nav>
    <div class="hero">
        <h1>Never Miss a Trade.<br>Ever Again.</h1>
        <p>AI-powered trading alerts that monitor markets 24/7. Set your strategy once, we handle the rest.</p>
        <a href="/app" class="btn" style="padding: 16px 32px; font-size: 16px; display: inline-block;">Start Free Trial →</a>
    </div>
</body>
</html>
"""

APP_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Create Alert - StratAlerts</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #0a0a0f; color: white; padding: 100px 24px 60px; }
        .card {
            max-width: 700px; margin: 0 auto; background: #12121a;
            border: 1px solid #27272a; border-radius: 16px; padding: 48px;
        }
        h1 { font-size: 32px; font-weight: 800; margin-bottom: 12px; }
        .subtitle { color: #a1a1aa; margin-bottom: 40px; }
        .input-group { margin-bottom: 24px; }
        label { display: block; font-weight: 600; margin-bottom: 8px; font-size: 14px; }
        input, textarea {
            width: 100%; padding: 14px; background: #1a1a24;
            border: 1px solid #27272a; border-radius: 10px;
            color: white; font-size: 16px; font-family: 'Inter', sans-serif;
        }
        input:focus, textarea:focus {
            outline: none; border-color: #6366f1;
            box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
        }
        textarea { min-height: 120px; resize: vertical; }
        button {
            width: 100%; padding: 16px;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white; border: none; border-radius: 10px;
            font-weight: 700; cursor: pointer; font-size: 16px;
        }
        button:hover { opacity: 0.9; }
        .result {
            margin-top: 24px; padding: 20px; border-radius: 12px; display: none;
        }
        .success {
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid #10b981; color: #10b981;
        }
        .error {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid #ef4444; color: #ef4444;
        }
        .examples {
            background: #1a1a24; border: 1px solid #27272a;
            padding: 24px; border-radius: 12px; margin-top: 32px;
        }
        .example-item {
            background: #12121a; padding: 12px 16px; border-radius: 8px;
            margin-top: 10px; cursor: pointer; font-size: 14px; color: #a1a1aa;
            transition: all 0.2s;
        }
        .example-item:hover { color: white; border-color: #6366f1; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Create Your First Alert</h1>
        <p class="subtitle">Describe your trading strategy in plain English</p>
        
        <form id="alertForm">
            <div class="input-group">
                <label>Email Address</label>
                <input type="email" id="email" required placeholder="you@example.com">
            </div>
            <div class="input-group">
                <label>Trading Strategy</label>
                <textarea id="strategy" required placeholder="E.g., Alert me when Apple goes above $220"></textarea>
            </div>
            <button type="submit">🚀 Create Alert</button>
        </form>
        
        <div class="result" id="result"></div>
        
        <div class="examples">
            <h3 style="margin-bottom: 12px;">💡 Try These Examples</h3>
            <div class="example-item" onclick="fill('Alert me when Apple goes above $220')">
                Alert me when Apple goes above $220
            </div>
            <div class="example-item" onclick="fill('Tell me if Tesla drops below $400')">
                Tell me if Tesla drops below $400
            </div>
            <div class="example-item" onclick="fill('Notify me when Bitcoin hits $100,000')">
                Notify me when Bitcoin hits $100,000
            </div>
        </div>
    </div>
    
    <script>
        function fill(text) {
            document.getElementById('strategy').value = text;
        }
        
        document.getElementById('alertForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const strategy = document.getElementById('strategy').value;
            const result = document.getElementById('result');
            
            try {
                const response = await fetch('/add-strategy', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, strategy })
                });
                
                const data = await response.json();
                result.style.display = 'block';
                
                if (data.success) {
                    result.className = 'result success';
                    result.innerHTML = `
                        <h3 style="margin-bottom: 12px;">✅ Alert Created Successfully!</h3>
                        <p><strong>Ticker:</strong> ${data.parsed.ticker}</p>
                        <p><strong>Type:</strong> ${data.parsed.type}</p>
                        <p><strong>Condition:</strong> ${data.parsed.condition} ${data.parsed.threshold}</p>
                        <p style="margin-top: 12px;">We're now monitoring the market 24/7. You'll get an email when it triggers!</p>
                    `;
                    document.getElementById('strategy').value = '';
                } else {
                    result.className = 'result error';
                    result.innerHTML = '<h3>❌ Error</h3><p>' + data.error + '</p>';
                }
            } catch (error) {
                result.style.display = 'block';
                result.className = 'result error';
                result.innerHTML = '<h3>❌ Connection Error</h3><p>Please try again.</p>';
            }
        });
    </script>
</body>
</html>
"""


# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def home():
    """Landing page"""
    return LANDING_PAGE

@app.route('/app')
def app_page():
    """App page"""
    return APP_PAGE

@app.route('/add-strategy', methods=['POST'])
def add_strategy():
    """API endpoint to add strategy"""
    try:
        data = request.json
        email = data.get('email')
        strategy_text = data.get('strategy')
        
        if not email or not strategy_text:
            return jsonify({'success': False, 'error': 'Email and strategy required'})
        
        # Parse strategy
        parsed = parse_strategy(strategy_text)
        
        # Save to database
        strategy_id = add_strategy_to_db(email, parsed)
        
        print(f"✓ Strategy #{strategy_id} created for {email}")
        
        return jsonify({
            'success': True,
            'strategy_id': strategy_id,
            'parsed': parsed
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'StratAlerts is running!'})


# ============================================================================
# RUN APP
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "="*70)
    print("🚀 STRATALERTS STARTING")
    print("="*70)
    print(f"Port: {port}")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=False)
