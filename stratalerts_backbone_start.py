"""
STRATALERTS - COMPLETE PROFESSIONAL WEB APP
===========================================
Professional multi-page trading platform
"""

from flask import Flask, render_template_string, request, jsonify, redirect, url_for
from complete_trading_system import TradingAlertSystem

app = Flask(__name__)
app.secret_key = 'change-this-in-production'

system = TradingAlertSystem()


# ============================================================================
# SHARED STYLES & COMPONENTS
# ============================================================================

BASE_STYLES = """
<style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    :root {
        --primary: #6366f1;
        --primary-dark: #4f46e5;
        --accent: #8b5cf6;
        --bg-dark: #0a0a0f;
        --bg-secondary: #12121a;
        --bg-tertiary: #1a1a24;
        --text-primary: #ffffff;
        --text-secondary: #a1a1aa;
        --border: #27272a;
        --success: #10b981;
    }
    
    body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: var(--bg-dark);
        color: var(--text-primary);
        line-height: 1.6;
    }
    
    .navbar {
        position: fixed;
        top: 0;
        width: 100%;
        background: rgba(10, 10, 15, 0.95);
        backdrop-filter: blur(10px);
        border-bottom: 1px solid var(--border);
        z-index: 1000;
        padding: 16px 0;
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
        background: linear-gradient(135deg, var(--primary), var(--accent));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-decoration: none;
    }
    
    .nav-links {
        display: flex;
        gap: 32px;
        align-items: center;
    }
    
    .nav-links a {
        color: var(--text-secondary);
        text-decoration: none;
        font-weight: 500;
        font-size: 14px;
        transition: color 0.2s;
    }
    
    .nav-links a:hover {
        color: var(--text-primary);
    }
    
    .btn-primary {
        background: linear-gradient(135deg, var(--primary), var(--accent));
        color: white;
        padding: 10px 24px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 600;
        font-size: 14px;
        border: none;
        cursor: pointer;
        transition: all 0.3s;
        display: inline-block;
    }
    
    .btn-primary:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4);
    }
</style>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
"""

NAVBAR = """
<nav class="navbar">
    <div class="nav-container">
        <a href="/" class="logo">StratAlerts</a>
        <div class="nav-links">
            <a href="/#features">Features</a>
            <a href="/#how-it-works">How It Works</a>
            <a href="/pricing">Pricing</a>
            <a href="/app" class="btn-primary">Get Started →</a>
        </div>
    </div>
</nav>
"""


# ============================================================================
# LANDING PAGE
# ============================================================================

@app.route('/')
def landing():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StratAlerts - Never Miss a Trade Again</title>
    """ + BASE_STYLES + """
    <style>
        .hero {
            padding: 180px 24px 120px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .hero::before {
            content: '';
            position: absolute;
            top: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 800px;
            height: 800px;
            background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
        }
        
        .hero-badge {
            display: inline-block;
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 24px;
            color: var(--primary);
        }
        
        .hero h1 {
            font-size: 72px;
            font-weight: 900;
            line-height: 1.1;
            margin-bottom: 24px;
            letter-spacing: -2px;
            position: relative;
        }
        
        .gradient-text {
            background: linear-gradient(135deg, white, var(--text-secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .hero-subtitle {
            font-size: 20px;
            color: var(--text-secondary);
            max-width: 600px;
            margin: 0 auto 40px;
        }
        
        .hero-cta {
            display: flex;
            gap: 16px;
            justify-content: center;
            flex-wrap: wrap;
        }
        
        .btn-large {
            padding: 16px 32px;
            font-size: 16px;
            border-radius: 12px;
        }
        
        .btn-secondary {
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            color: var(--text-primary);
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 48px;
            max-width: 900px;
            margin: 80px auto 0;
        }
        
        .stat-number {
            font-size: 48px;
            font-weight: 800;
            background: linear-gradient(135deg, var(--primary), var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .stat-label {
            font-size: 14px;
            color: var(--text-secondary);
            margin-top: 8px;
        }
        
        .section {
            padding: 120px 24px;
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .section-title {
            font-size: 48px;
            font-weight: 800;
            text-align: center;
            margin-bottom: 60px;
        }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 32px;
        }
        
        .feature-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 40px;
            transition: all 0.3s;
        }
        
        .feature-card:hover {
            transform: translateY(-4px);
            border-color: var(--primary);
        }
        
        .feature-icon {
            font-size: 48px;
            margin-bottom: 20px;
        }
        
        .feature-title {
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 12px;
        }
        
        .feature-description {
            color: var(--text-secondary);
        }
        
        .cta-section {
            background: linear-gradient(135deg, var(--primary), var(--accent));
            padding: 80px 24px;
            text-align: center;
            border-radius: 24px;
            margin: 80px 24px;
        }
        
        .cta-section h2 {
            font-size: 48px;
            font-weight: 800;
            margin-bottom: 16px;
        }
        
        .btn-white {
            background: white;
            color: var(--primary);
        }
        
        @media (max-width: 768px) {
            .hero h1 { font-size: 48px; }
            .stats { grid-template-columns: 1fr; }
            .features-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    """ + NAVBAR + """
    
    <section class="hero">
        <div class="hero-badge">✨ Powered by AI</div>
        <h1>Never Miss a Trade.<br><span class="gradient-text">Ever Again.</span></h1>
        <p class="hero-subtitle">
            AI-powered trading alerts that monitor markets 24/7. Set your strategy once, we handle the rest.
        </p>
        <div class="hero-cta">
            <a href="/app" class="btn-primary btn-large">Start Free Trial →</a>
            <a href="/pricing" class="btn-secondary btn-large">View Pricing</a>
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-number">24/7</div>
                <div class="stat-label">Market Monitoring</div>
            </div>
            <div class="stat">
                <div class="stat-number">&lt;1s</div>
                <div class="stat-label">Alert Speed</div>
            </div>
            <div class="stat">
                <div class="stat-number">100%</div>
                <div class="stat-label">Uptime</div>
            </div>
        </div>
    </section>
    
    <section class="section" id="features">
        <h2 class="section-title">Everything You Need</h2>
        <div class="features-grid">
            <div class="feature-card">
                <div class="feature-icon">🤖</div>
                <h3 class="feature-title">AI-Powered</h3>
                <p class="feature-description">Describe strategies in plain English. Our AI understands complex conditions instantly.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">⚡</div>
                <h3 class="feature-title">Real-Time</h3>
                <p class="feature-description">Continuous monitoring. Never miss an opportunity, day or night.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <h3 class="feature-title">All Indicators</h3>
                <p class="feature-description">RSI, MACD, Moving Averages, Volume - all major technical indicators.</p>
            </div>
        </div>
    </section>
    
    <section class="cta-section">
        <h2>Ready to Get Started?</h2>
        <p style="margin-bottom: 32px;">Join traders who never miss opportunities</p>
        <a href="/app" class="btn-white btn-large">Create Your First Alert →</a>
    </section>
</body>
</html>
    """)


# ============================================================================
# APP PAGE (Create Alerts)
# ============================================================================

@app.route('/app')
def app_page():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Create Alert - StratAlerts</title>
    """ + BASE_STYLES + """
    <style>
        .app-container {
            min-height: 100vh;
            padding: 100px 24px 60px;
        }
        
        .card {
            max-width: 700px;
            margin: 0 auto;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 48px;
        }
        
        .card-title {
            font-size: 32px;
            font-weight: 800;
            margin-bottom: 12px;
        }
        
        .card-subtitle {
            color: var(--text-secondary);
            margin-bottom: 40px;
        }
        
        .input-group {
            margin-bottom: 24px;
        }
        
        label {
            display: block;
            font-weight: 600;
            margin-bottom: 8px;
            font-size: 14px;
        }
        
        input, textarea {
            width: 100%;
            padding: 14px 16px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 10px;
            color: white;
            font-size: 16px;
            font-family: 'Inter', sans-serif;
            transition: all 0.2s;
        }
        
        input:focus, textarea:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
        }
        
        textarea {
            min-height: 120px;
            resize: vertical;
        }
        
        button[type="submit"] {
            width: 100%;
            padding: 16px;
            margin-top: 12px;
        }
        
        .examples {
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            padding: 24px;
            border-radius: 12px;
            margin-top: 32px;
        }
        
        .example-item {
            background: var(--bg-secondary);
            padding: 12px 16px;
            border-radius: 8px;
            margin-top: 10px;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 14px;
            color: var(--text-secondary);
        }
        
        .example-item:hover {
            border-color: var(--primary);
            color: white;
        }
        
        .result {
            margin-top: 24px;
            padding: 20px;
            border-radius: 12px;
            display: none;
        }
        
        .success {
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid var(--success);
            color: var(--success);
        }
        
        .error {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid #ef4444;
            color: #ef4444;
        }
        
        .loading {
            text-align: center;
            padding: 30px;
            display: none;
        }
        
        .spinner {
            border: 3px solid var(--border);
            border-top: 3px solid var(--primary);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 12px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    """ + NAVBAR + """
    
    <div class="app-container">
        <div class="card">
            <h1 class="card-title">Create Your First Alert</h1>
            <p class="card-subtitle">Describe your trading strategy in plain English</p>
            
            <form id="strategyForm">
                <div class="input-group">
                    <label>Email Address</label>
                    <input type="email" id="email" required placeholder="you@example.com">
                </div>
                
                <div class="input-group">
                    <label>Your Trading Strategy</label>
                    <textarea id="strategy" required placeholder="E.g., Alert me when Apple goes above $220"></textarea>
                </div>
                
                <button type="submit" class="btn-primary">🚀 Create Alert</button>
            </form>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p style="color: var(--text-secondary);">Processing...</p>
            </div>
            
            <div class="result" id="result"></div>
            
            <div class="examples">
                <h3 style="margin-bottom: 12px;">💡 Example Strategies</h3>
                <div class="example-item" onclick="fillExample('Alert me when Apple goes above $220')">
                    Alert me when Apple goes above $220
                </div>
                <div class="example-item" onclick="fillExample('Tell me if Tesla drops below $400')">
                    Tell me if Tesla drops below $400
                </div>
                <div class="example-item" onclick="fillExample('Notify me when Bitcoin hits $100,000')">
                    Notify me when Bitcoin hits $100,000
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function fillExample(text) {
            document.getElementById('strategy').value = text;
        }
        
        document.getElementById('strategyForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const strategy = document.getElementById('strategy').value;
            const resultDiv = document.getElementById('result');
            const loadingDiv = document.getElementById('loading');
            
            loadingDiv.style.display = 'block';
            resultDiv.style.display = 'none';
            
            try {
                const response = await fetch('/add-strategy', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, strategy })
                });
                
                const data = await response.json();
                loadingDiv.style.display = 'none';
                resultDiv.style.display = 'block';
                
                if (data.success) {
                    resultDiv.className = 'result success';
                    resultDiv.innerHTML = `
                        <h3 style="margin-bottom: 12px;">✅ Alert Created!</h3>
                        <p><strong>Ticker:</strong> ${data.parsed.ticker}</p>
                        <p><strong>Type:</strong> ${data.parsed.type}</p>
                        <p style="margin-top: 12px;">We're monitoring 24/7. You'll get an email when it triggers!</p>
                    `;
                    document.getElementById('strategy').value = '';
                } else {
                    resultDiv.className = 'result error';
                    resultDiv.innerHTML = `<h3>❌ Error</h3><p>${data.error}</p>`;
                }
            } catch (error) {
                loadingDiv.style.display = 'none';
                resultDiv.style.display = 'block';
                resultDiv.className = 'result error';
                resultDiv.innerHTML = '<h3>❌ Connection Error</h3><p>Please try again.</p>';
            }
        });
    </script>
</body>
</html>
    """)


# ============================================================================
# PRICING PAGE
# ============================================================================

@app.route('/pricing')
def pricing():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pricing - StratAlerts</title>
    """ + BASE_STYLES + """
    <style>
        .pricing-hero {
            padding: 120px 24px 60px;
            text-align: center;
        }
        
        .pricing-hero h1 {
            font-size: 56px;
            font-weight: 900;
            margin-bottom: 16px;
        }
        
        .pricing-hero p {
            font-size: 20px;
            color: var(--text-secondary);
        }
        
        .pricing-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 32px;
            max-width: 1100px;
            margin: 60px auto;
            padding: 0 24px;
        }
        
        .pricing-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 40px;
            position: relative;
        }
        
        .pricing-card.featured {
            border-color: var(--primary);
            transform: scale(1.05);
        }
        
        .badge {
            position: absolute;
            top: -12px;
            right: 24px;
            background: linear-gradient(135deg, var(--primary), var(--accent));
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
        }
        
        .plan-name {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 8px;
        }
        
        .plan-price {
            font-size: 48px;
            font-weight: 900;
            margin-bottom: 8px;
        }
        
        .plan-price span {
            font-size: 20px;
            color: var(--text-secondary);
        }
        
        .plan-description {
            color: var(--text-secondary);
            margin-bottom: 32px;
        }
        
        .feature-list {
            list-style: none;
            margin-bottom: 32px;
        }
        
        .feature-list li {
            padding: 12px 0;
            border-bottom: 1px solid var(--border);
        }
        
        .feature-list li:last-child {
            border-bottom: none;
        }
        
        .feature-list li::before {
            content: '✓ ';
            color: var(--success);
            font-weight: 700;
            margin-right: 8px;
        }
    </style>
</head>
<body>
    """ + NAVBAR + """
    
    <div class="pricing-hero">
        <h1>Simple, Transparent Pricing</h1>
        <p>Choose the plan that fits your trading style</p>
    </div>
    
    <div class="pricing-grid">
        <div class="pricing-card">
            <div class="plan-name">Free</div>
            <div class="plan-price">$0<span>/month</span></div>
            <div class="plan-description">Perfect for getting started</div>
            <ul class="feature-list">
                <li>2 active alerts</li>
                <li>Email notifications</li>
                <li>Hourly price checks</li>
                <li>Basic indicators</li>
            </ul>
            <a href="/app" class="btn-primary" style="width: 100%; text-align: center;">Get Started</a>
        </div>
        
        <div class="pricing-card featured">
            <div class="badge">MOST POPULAR</div>
            <div class="plan-name">Pro</div>
            <div class="plan-price">$10<span>/month</span></div>
            <div class="plan-description">For serious traders</div>
            <ul class="feature-list">
                <li>Unlimited alerts</li>
                <li>Email + SMS notifications</li>
                <li>Real-time monitoring</li>
                <li>All indicators (RSI, MACD, etc)</li>
                <li>Priority support</li>
            </ul>
            <a href="/app" class="btn-primary" style="width: 100%; text-align: center;">Start Free Trial</a>
        </div>
        
        <div class="pricing-card">
            <div class="plan-name">Enterprise</div>
            <div class="plan-price">Custom</div>
            <div class="plan-description">For teams and institutions</div>
            <ul class="feature-list">
                <li>Everything in Pro</li>
                <li>API access</li>
                <li>Dedicated support</li>
                <li>Custom integrations</li>
                <li>SLA guarantee</li>
            </ul>
            <a href="#" class="btn-primary" style="width: 100%; text-align: center;">Contact Sales</a>
        </div>
    </div>
</body>
</html>
    """)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/add-strategy', methods=['POST'])
def add_strategy():
    """API endpoint to add strategy"""
    try:
        data = request.json
        email = data.get('email')
        strategy_text = data.get('strategy')
        
        if not email or not strategy_text:
            return jsonify({'success': False, 'error': 'Missing data'})
        
        strategy_id = system.add_user_strategy(email, strategy_text)
        parsed = system.parser.parse(strategy_text)
        
        return jsonify({
            'success': True,
            'strategy_id': strategy_id,
            'parsed': parsed
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🌐 STRATALERTS WEB APP STARTING")
    print("="*70)
    print("\nYour professional website is now running:")
    print("👉 http://localhost:5000 (Landing Page)")
    print("👉 http://localhost:5000/app (Create Alerts)")
    print("👉 http://localhost:5000/pricing (Pricing)")
    print("\nPress Ctrl+C to stop")
    print("="*70 + "\n")
    
    app.run(debug=True, port=5000)
