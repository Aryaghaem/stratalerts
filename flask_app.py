"""
STRATALERTS - Premium Redesign
================================
Bloomberg terminal-inspired dark professional aesthetic
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


def get_strategies_by_email(email):
    conn = sqlite3.connect('alerts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM strategies WHERE email = ? ORDER BY created_at DESC', (email,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def update_strategy_in_db(strategy_id, email, strategy):
    conn = sqlite3.connect('alerts.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE strategies SET ticker=?, strategy_type=?, condition=?, threshold=?, raw_description=?
        WHERE id=? AND email=?
    ''', (
        strategy.get('ticker', 'UNKNOWN'),
        strategy.get('type', 'PRICE'),
        strategy.get('condition', 'above'),
        strategy.get('threshold', 0),
        strategy.get('raw_description', ''),
        strategy_id,
        email
    ))
    conn.commit()
    conn.close()


# ============================================================================
# STRATEGY PARSER
# ============================================================================

def parse_strategy(text):
    text_lower = text.lower()
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
        "spy": "SPY", "qqq": "QQQ",
        "s&p": "SPY", "nasdaq": "QQQ",
    }
    ticker = "UNKNOWN"
    for name, symbol in tickers.items():
        if name in text_lower:
            ticker = symbol
            break
    if any(word in text_lower for word in ["above", "over", "exceed", "break", "hit", "reaches"]):
        condition = "above"
    elif any(word in text_lower for word in ["below", "under", "drop", "fall", "dips"]):
        condition = "below"
    else:
        condition = "above"
    numbers = re.findall(r'\$?\d+[\d,]*\.?\d*', text)
    threshold = 0
    if numbers:
        num_str = numbers[0].replace('$', '').replace(',', '')
        try:
            threshold = float(num_str)
        except:
            threshold = 0
    if "rsi" in text_lower:
        strategy_type = "RSI"
    elif "macd" in text_lower:
        strategy_type = "MACD"
    elif "volume" in text_lower:
        strategy_type = "VOLUME"
    elif "moving average" in text_lower or " ma " in text_lower:
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
    <title>StratAlerts — Institutional-Grade Trading Alerts</title>
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #080c10;
            --bg2: #0d1117;
            --bg3: #111820;
            --border: #1e2d3d;
            --border2: #243447;
            --accent: #00d4ff;
            --accent2: #00ff88;
            --accent3: #ff6b35;
            --text: #c9d1d9;
            --text2: #8b949e;
            --text3: #58677a;
            --red: #ff4757;
            --green: #00ff88;
            --yellow: #ffd43b;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html { scroll-behavior: smooth; }
        body {
            font-family: 'IBM Plex Sans', sans-serif;
            background: var(--bg);
            color: var(--text);
            overflow-x: hidden;
        }

        /* SCAN LINE EFFECT */
        body::before {
            content: '';
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: repeating-linear-gradient(
                0deg,
                transparent,
                transparent 2px,
                rgba(0,212,255,0.015) 2px,
                rgba(0,212,255,0.015) 4px
            );
            pointer-events: none;
            z-index: 9999;
        }

        /* TICKER BAR */
        .ticker-wrap {
            background: var(--bg2);
            border-bottom: 1px solid var(--border);
            padding: 8px 0;
            overflow: hidden;
            white-space: nowrap;
        }
        .ticker-track {
            display: inline-block;
            animation: ticker 40s linear infinite;
        }
        .ticker-track:hover { animation-play-state: paused; }
        @keyframes ticker {
            0% { transform: translateX(0); }
            100% { transform: translateX(-50%); }
        }
        .ticker-item {
            display: inline-block;
            margin: 0 32px;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 12px;
            color: var(--text2);
        }
        .ticker-item .sym { color: var(--accent); font-weight: 600; margin-right: 8px; }
        .ticker-item .up { color: var(--green); }
        .ticker-item .down { color: var(--red); }
        .ticker-sep { color: var(--border2); margin: 0 8px; }

        /* NAVBAR */
        .navbar {
            position: fixed; top: 33px; width: 100%;
            background: rgba(8, 12, 16, 0.92);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
            padding: 14px 0; z-index: 100;
        }
        .nav-inner {
            max-width: 1200px; margin: 0 auto; padding: 0 32px;
            display: flex; justify-content: space-between; align-items: center;
        }
        .logo {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 18px; font-weight: 600;
            color: var(--accent);
            letter-spacing: 2px;
            text-decoration: none;
        }
        .logo span { color: var(--text2); }
        .nav-links { display: flex; gap: 32px; align-items: center; }
        .nav-links a {
            color: var(--text2); text-decoration: none;
            font-size: 13px; font-weight: 500;
            letter-spacing: 0.5px;
            transition: color 0.2s;
        }
        .nav-links a:hover { color: var(--accent); }
        .nav-cta {
            background: transparent;
            border: 1px solid var(--accent);
            color: var(--accent) !important;
            padding: 7px 20px;
            border-radius: 2px;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 12px !important;
            letter-spacing: 1px;
            transition: all 0.2s !important;
        }
        .nav-cta:hover {
            background: var(--accent) !important;
            color: var(--bg) !important;
        }

        /* HERO */
        .hero {
            padding: 180px 32px 120px;
            max-width: 1200px; margin: 0 auto;
            position: relative;
        }
        .hero-tag {
            display: inline-flex; align-items: center; gap: 8px;
            background: rgba(0,212,255,0.08);
            border: 1px solid rgba(0,212,255,0.2);
            padding: 6px 14px; border-radius: 2px;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 11px; color: var(--accent);
            letter-spacing: 2px; text-transform: uppercase;
            margin-bottom: 32px;
        }
        .hero-tag::before {
            content: '';
            width: 6px; height: 6px;
            background: var(--green);
            border-radius: 50%;
            animation: blink 1.5s ease-in-out infinite;
        }
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        .hero h1 {
            font-size: clamp(42px, 6vw, 80px);
            font-weight: 700;
            line-height: 1.05;
            letter-spacing: -1px;
            margin-bottom: 24px;
            color: #e6edf3;
        }
        .hero h1 .hl {
            color: var(--accent);
            position: relative;
        }
        .hero-sub {
            font-size: 18px;
            color: var(--text2);
            max-width: 580px;
            line-height: 1.7;
            margin-bottom: 48px;
            font-weight: 300;
        }
        .hero-actions { display: flex; gap: 16px; align-items: center; flex-wrap: wrap; }
        .btn-primary {
            background: var(--accent);
            color: var(--bg);
            padding: 14px 32px;
            border-radius: 2px;
            text-decoration: none;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 1px;
            transition: all 0.2s;
            border: none; cursor: pointer;
            display: inline-block;
        }
        .btn-primary:hover {
            background: #33dcff;
            transform: translateY(-1px);
            box-shadow: 0 8px 32px rgba(0,212,255,0.3);
        }
        .btn-ghost {
            color: var(--text2);
            padding: 14px 32px;
            border-radius: 2px;
            text-decoration: none;
            font-size: 13px;
            font-weight: 500;
            border: 1px solid var(--border2);
            transition: all 0.2s;
            display: inline-block;
        }
        .btn-ghost:hover { color: var(--text); border-color: var(--text3); }

        /* STATS BAR */
        .stats-bar {
            max-width: 1200px; margin: 0 auto 80px;
            padding: 0 32px;
            display: grid; grid-template-columns: repeat(4, 1fr);
            gap: 1px;
            background: var(--border);
            border: 1px solid var(--border);
            border-radius: 4px;
            overflow: hidden;
        }
        .stat-item {
            background: var(--bg2);
            padding: 28px 32px;
        }
        .stat-label {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 10px;
            color: var(--text3);
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        .stat-value {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 32px;
            font-weight: 600;
            color: var(--accent);
        }
        .stat-sub { font-size: 12px; color: var(--text3); margin-top: 4px; }

        /* SECTION */
        .section {
            max-width: 1200px; margin: 0 auto;
            padding: 80px 32px;
        }
        .section-label {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 10px;
            color: var(--accent);
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-bottom: 16px;
        }
        .section-title {
            font-size: clamp(28px, 3vw, 42px);
            font-weight: 700;
            color: #e6edf3;
            margin-bottom: 16px;
            letter-spacing: -0.5px;
        }
        .section-sub {
            color: var(--text2);
            font-size: 16px;
            max-width: 560px;
            line-height: 1.7;
            margin-bottom: 56px;
            font-weight: 300;
        }

        /* HOW IT WORKS */
        .steps {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1px;
            background: var(--border);
            border: 1px solid var(--border);
            border-radius: 4px;
            overflow: hidden;
        }
        .step {
            background: var(--bg2);
            padding: 40px 36px;
            position: relative;
        }
        .step-num {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 48px;
            font-weight: 600;
            color: var(--border2);
            line-height: 1;
            margin-bottom: 24px;
        }
        .step-title {
            font-size: 18px;
            font-weight: 600;
            color: #e6edf3;
            margin-bottom: 12px;
        }
        .step-desc { color: var(--text2); font-size: 14px; line-height: 1.7; }
        .step-icon {
            position: absolute; top: 36px; right: 36px;
            font-size: 28px; opacity: 0.6;
        }
        .step:hover { background: var(--bg3); }
        .step:hover .step-num { color: var(--accent); opacity: 0.3; }

        /* FEATURES */
        .features {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-top: 8px;
        }
        .feature-card {
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 32px;
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
        }
        .feature-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 2px;
            background: linear-gradient(90deg, var(--accent), transparent);
            opacity: 0;
            transition: opacity 0.3s;
        }
        .feature-card:hover { border-color: var(--border2); transform: translateY(-2px); }
        .feature-card:hover::before { opacity: 1; }
        .feature-icon { font-size: 24px; margin-bottom: 16px; }
        .feature-title { font-size: 16px; font-weight: 600; color: #e6edf3; margin-bottom: 8px; }
        .feature-desc { color: var(--text2); font-size: 13px; line-height: 1.7; }

        /* PRICING */
        .pricing {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
        }
        .price-card {
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 40px 36px;
            position: relative;
            transition: all 0.3s;
        }
        .price-card.featured {
            border-color: var(--accent);
            background: rgba(0,212,255,0.04);
        }
        .price-card.featured::before {
            content: 'MOST POPULAR';
            position: absolute; top: -1px; left: 50%; transform: translateX(-50%);
            background: var(--accent);
            color: var(--bg);
            font-family: 'IBM Plex Mono', monospace;
            font-size: 9px;
            font-weight: 600;
            letter-spacing: 2px;
            padding: 4px 16px;
            border-radius: 0 0 4px 4px;
        }
        .price-tier {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 11px;
            color: var(--text3);
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 20px;
        }
        .price-amount {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 48px;
            font-weight: 600;
            color: #e6edf3;
            line-height: 1;
            margin-bottom: 6px;
        }
        .price-amount sup { font-size: 24px; vertical-align: top; margin-top: 8px; color: var(--text2); }
        .price-period { font-size: 13px; color: var(--text3); margin-bottom: 32px; }
        .price-features { list-style: none; margin-bottom: 36px; }
        .price-features li {
            padding: 10px 0;
            border-bottom: 1px solid var(--border);
            font-size: 13px;
            color: var(--text2);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .price-features li::before { content: '—'; color: var(--text3); font-size: 12px; }
        .price-features li.highlight { color: var(--text); }
        .price-features li.highlight::before { content: '✓'; color: var(--green); }
        .price-btn {
            display: block;
            text-align: center;
            padding: 13px;
            border-radius: 2px;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 1px;
            text-decoration: none;
            transition: all 0.2s;
            cursor: pointer;
            border: none;
            width: 100%;
        }
        .price-btn-outline {
            border: 1px solid var(--border2);
            color: var(--text2);
            background: transparent;
        }
        .price-btn-outline:hover { border-color: var(--accent); color: var(--accent); }
        .price-btn-solid {
            background: var(--accent);
            color: var(--bg);
        }
        .price-btn-solid:hover { background: #33dcff; box-shadow: 0 4px 24px rgba(0,212,255,0.3); }

        /* TESTIMONIALS */
        .testimonials {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
        }
        .testi-card {
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 32px;
        }
        .testi-quote {
            font-size: 14px;
            color: var(--text);
            line-height: 1.8;
            margin-bottom: 24px;
            font-style: italic;
        }
        .testi-quote::before { content: '"'; color: var(--accent); font-size: 24px; font-style: normal; }
        .testi-author { display: flex; align-items: center; gap: 12px; }
        .testi-avatar {
            width: 36px; height: 36px;
            background: var(--border2);
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 12px;
            color: var(--accent);
            font-weight: 600;
        }
        .testi-name { font-size: 13px; font-weight: 600; color: #e6edf3; }
        .testi-role { font-size: 11px; color: var(--text3); font-family: 'IBM Plex Mono', monospace; }
        .testi-stars { color: var(--yellow); font-size: 12px; margin-bottom: 16px; }

        /* DIVIDER */
        .divider {
            border: none;
            border-top: 1px solid var(--border);
            max-width: 1200px; margin: 0 auto;
        }

        /* FOOTER */
        .footer {
            border-top: 1px solid var(--border);
            padding: 40px 32px;
            max-width: 1200px; margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .footer-logo {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 14px; color: var(--accent);
            letter-spacing: 2px;
        }
        .footer-text { font-size: 12px; color: var(--text3); }

        /* RESPONSIVE */
        @media (max-width: 900px) {
            .stats-bar { grid-template-columns: repeat(2, 1fr); }
            .steps { grid-template-columns: 1fr; }
            .features { grid-template-columns: repeat(2, 1fr); }
            .pricing { grid-template-columns: 1fr; }
            .testimonials { grid-template-columns: 1fr; }
            .footer { flex-direction: column; gap: 16px; text-align: center; }
        }
        @media (max-width: 600px) {
            .stats-bar { grid-template-columns: 1fr; }
            .features { grid-template-columns: 1fr; }
            .nav-links { display: none; }
        }
    </style>
</head>
<body>

<!-- TICKER BAR -->
<div class="ticker-wrap">
    <div class="ticker-track" id="ticker">
        <span class="ticker-item"><span class="sym">AAPL</span>182.63 <span class="up">+1.24%</span></span>
        <span class="ticker-item"><span class="sym">TSLA</span>248.50 <span class="down">-0.87%</span></span>
        <span class="ticker-item"><span class="sym">NVDA</span>824.18 <span class="up">+2.31%</span></span>
        <span class="ticker-item"><span class="sym">MSFT</span>415.32 <span class="up">+0.62%</span></span>
        <span class="ticker-item"><span class="sym">BTC-USD</span>68,420 <span class="up">+3.14%</span></span>
        <span class="ticker-item"><span class="sym">ETH-USD</span>3,812 <span class="up">+1.88%</span></span>
        <span class="ticker-item"><span class="sym">AMZN</span>192.40 <span class="down">-0.33%</span></span>
        <span class="ticker-item"><span class="sym">GOOGL</span>164.72 <span class="up">+0.44%</span></span>
        <span class="ticker-item"><span class="sym">META</span>512.80 <span class="up">+1.09%</span></span>
        <span class="ticker-item"><span class="sym">SPY</span>523.16 <span class="up">+0.28%</span></span>
        <span class="ticker-item"><span class="sym">QQQ</span>448.91 <span class="up">+0.51%</span></span>
        <!-- Duplicate for seamless loop -->
        <span class="ticker-item"><span class="sym">AAPL</span>182.63 <span class="up">+1.24%</span></span>
        <span class="ticker-item"><span class="sym">TSLA</span>248.50 <span class="down">-0.87%</span></span>
        <span class="ticker-item"><span class="sym">NVDA</span>824.18 <span class="up">+2.31%</span></span>
        <span class="ticker-item"><span class="sym">MSFT</span>415.32 <span class="up">+0.62%</span></span>
        <span class="ticker-item"><span class="sym">BTC-USD</span>68,420 <span class="up">+3.14%</span></span>
        <span class="ticker-item"><span class="sym">ETH-USD</span>3,812 <span class="up">+1.88%</span></span>
        <span class="ticker-item"><span class="sym">AMZN</span>192.40 <span class="down">-0.33%</span></span>
        <span class="ticker-item"><span class="sym">GOOGL</span>164.72 <span class="up">+0.44%</span></span>
        <span class="ticker-item"><span class="sym">META</span>512.80 <span class="up">+1.09%</span></span>
        <span class="ticker-item"><span class="sym">SPY</span>523.16 <span class="up">+0.28%</span></span>
        <span class="ticker-item"><span class="sym">QQQ</span>448.91 <span class="up">+0.51%</span></span>
    </div>
</div>

<!-- NAVBAR -->
<nav class="navbar">
    <div class="nav-inner">
        <a href="/" class="logo">STRAT<span>ALERTS</span></a>
        <div class="nav-links">
            <a href="#how-it-works">How It Works</a>
            <a href="#features">Features</a>
            <a href="#pricing">Pricing</a>
            <a href="/app" class="nav-cta">LAUNCH APP →</a>
        </div>
    </div>
</nav>

<!-- HERO -->
<div class="hero">
    <div class="hero-tag">Market Intelligence Platform · Live</div>
    <h1>Never Miss a<br>Critical <span class="hl">Trade Signal.</span></h1>
    <p class="hero-sub">Institutional-grade trading alerts powered by AI. Describe your strategy in plain English — we monitor markets 24/7 and alert you the moment conditions are met.</p>
    <div class="hero-actions">
        <a href="/app" class="btn-primary">START FREE TRIAL →</a>
        <a href="#how-it-works" class="btn-ghost">See How It Works</a>
    </div>
</div>

<!-- STATS BAR -->
<div class="stats-bar">
    <div class="stat-item">
        <div class="stat-label">Alerts Triggered</div>
        <div class="stat-value">2.4M+</div>
        <div class="stat-sub">Across all users</div>
    </div>
    <div class="stat-item">
        <div class="stat-label">Avg Response Time</div>
        <div class="stat-value">&lt; 2s</div>
        <div class="stat-sub">Market to notification</div>
    </div>
    <div class="stat-item">
        <div class="stat-label">Assets Monitored</div>
        <div class="stat-value">10,000+</div>
        <div class="stat-sub">Stocks, crypto & ETFs</div>
    </div>
    <div class="stat-item">
        <div class="stat-label">Uptime</div>
        <div class="stat-value">99.97%</div>
        <div class="stat-sub">24/7 monitoring</div>
    </div>
</div>

<!-- HOW IT WORKS -->
<div class="section" id="how-it-works">
    <div class="section-label">// Process</div>
    <div class="section-title">Up and Running in 60 Seconds</div>
    <p class="section-sub">No complex setups. No coding. Just describe what you want — our AI handles the rest.</p>
    <div class="steps">
        <div class="step">
            <div class="step-num">01</div>
            <div class="step-icon">✍️</div>
            <div class="step-title">Describe Your Strategy</div>
            <p class="step-desc">Type your trading condition in plain English. "Alert me when NVDA breaks above $900" or "Notify me if BTC drops below $60k." Our AI understands context and intent.</p>
        </div>
        <div class="step">
            <div class="step-num">02</div>
            <div class="step-icon">🤖</div>
            <div class="step-title">AI Parses & Activates</div>
            <p class="step-desc">Our system instantly interprets your strategy, identifies the ticker, condition, and threshold. Premium users can refine with AI conversation until it's exactly right.</p>
        </div>
        <div class="step">
            <div class="step-num">03</div>
            <div class="step-icon">⚡</div>
            <div class="step-title">Get Alerted Instantly</div>
            <p class="step-desc">The moment market conditions match your strategy, you receive an email alert within seconds. Manage, edit, or pause any alert from your dashboard at any time.</p>
        </div>
    </div>
</div>

<hr class="divider">

<!-- FEATURES -->
<div class="section" id="features">
    <div class="section-label">// Capabilities</div>
    <div class="section-title">Everything a Serious Trader Needs</div>
    <p class="section-sub">Built for precision. Designed for speed. Engineered for traders who can't afford to miss a move.</p>
    <div class="features">
        <div class="feature-card">
            <div class="feature-icon">🧠</div>
            <div class="feature-title">Natural Language AI</div>
            <p class="feature-desc">Describe complex strategies in plain English. Our AI handles PRICE, RSI, MACD, Volume, and Moving Average conditions.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">💬</div>
            <div class="feature-title">AI Strategy Conversation</div>
            <p class="feature-desc">Premium users can refine strategies through dialogue. Ask follow-up questions, adjust parameters, get AI recommendations.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">✏️</div>
            <div class="feature-title">Edit & Update Alerts</div>
            <p class="feature-desc">Markets change. Your strategy can too. Return to any previous alert and update it on the fly without losing history.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-title">Strategy History</div>
            <p class="feature-desc">Full audit trail of every alert you've created. See what triggered, when, and at what price. Your complete trading log.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">⚡</div>
            <div class="feature-title">Sub-2 Second Alerts</div>
            <p class="feature-desc">Market events happen fast. Our monitoring engine checks conditions continuously and delivers notifications in real-time.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🌐</div>
            <div class="feature-title">10,000+ Assets</div>
            <p class="feature-desc">Monitor US stocks, crypto, ETFs, and indices. From AAPL to obscure small-caps, we've got coverage across all major markets.</p>
        </div>
    </div>
</div>

<hr class="divider">

<!-- PRICING -->
<div class="section" id="pricing">
    <div class="section-label">// Pricing</div>
    <div class="section-title">Simple, Transparent Pricing</div>
    <p class="section-sub">Start free. Upgrade when you need more power. No hidden fees, no long-term contracts.</p>
    <div class="pricing">
        <!-- FREE -->
        <div class="price-card">
            <div class="price-tier">Free</div>
            <div class="price-amount"><sup>$</sup>0</div>
            <div class="price-period">forever</div>
            <ul class="price-features">
                <li class="highlight">3 active alerts</li>
                <li class="highlight">Email notifications</li>
                <li class="highlight">Price alerts</li>
                <li>AI strategy parsing</li>
                <li>Basic asset coverage</li>
            </ul>
            <a href="/app" class="price-btn price-btn-outline">GET STARTED FREE</a>
        </div>
        <!-- PREMIUM -->
        <div class="price-card featured">
            <div class="price-tier">Premium</div>
            <div class="price-amount"><sup>$</sup>9<span style="font-size:28px">.99</span></div>
            <div class="price-period">per month</div>
            <ul class="price-features">
                <li class="highlight">Unlimited active alerts</li>
                <li class="highlight">AI strategy conversation</li>
                <li class="highlight">Edit & update alerts</li>
                <li class="highlight">Full strategy history</li>
                <li class="highlight">RSI, MACD, Volume alerts</li>
                <li class="highlight">Priority email delivery</li>
                <li class="highlight">10,000+ assets</li>
            </ul>
            <a href="/app" class="price-btn price-btn-solid">START PREMIUM →</a>
        </div>
        <!-- PRO -->
        <div class="price-card">
            <div class="price-tier">Pro / Teams</div>
            <div class="price-amount"><sup>$</sup>49</div>
            <div class="price-period">per month · coming soon</div>
            <ul class="price-features">
                <li class="highlight">Everything in Premium</li>
                <li class="highlight">API access</li>
                <li class="highlight">Webhook integrations</li>
                <li class="highlight">SMS & push notifications</li>
                <li class="highlight">Team seats (up to 10)</li>
                <li class="highlight">Dedicated support</li>
                <li>Custom alert logic</li>
            </ul>
            <a href="#" class="price-btn price-btn-outline">JOIN WAITLIST</a>
        </div>
    </div>
</div>

<hr class="divider">

<!-- TESTIMONIALS -->
<div class="section">
    <div class="section-label">// Social Proof</div>
    <div class="section-title">Trusted by Active Traders</div>
    <p class="section-sub">From day traders to long-term investors — StratAlerts fits every style.</p>
    <div class="testimonials">
        <div class="testi-card">
            <div class="testi-stars">★★★★★</div>
            <p class="testi-quote">Finally an alert system that understands plain English. I just type what I want and it works. Caught a NVDA breakout I would have 100% missed.</p>
            <div class="testi-author">
                <div class="testi-avatar">MK</div>
                <div>
                    <div class="testi-name">Marcus K.</div>
                    <div class="testi-role">Day Trader · Chicago</div>
                </div>
            </div>
        </div>
        <div class="testi-card">
            <div class="testi-stars">★★★★★</div>
            <p class="testi-quote">The AI conversation feature on Premium is a game changer. I refined my MACD strategy through chat until it was exactly what I needed.</p>
            <div class="testi-author">
                <div class="testi-avatar">SR</div>
                <div>
                    <div class="testi-name">Sophia R.</div>
                    <div class="testi-role">Swing Trader · NYC</div>
                </div>
            </div>
        </div>
        <div class="testi-card">
            <div class="testi-stars">★★★★★</div>
            <p class="testi-quote">$9.99/month for unlimited alerts with AI? That's less than one bad trade. The strategy history alone is worth it — I use it to review my setups.</p>
            <div class="testi-author">
                <div class="testi-avatar">JT</div>
                <div>
                    <div class="testi-name">James T.</div>
                    <div class="testi-role">Options Trader · Austin</div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- FOOTER -->
<div style="border-top: 1px solid var(--border); margin-top: 40px;">
    <div class="footer">
        <div class="footer-logo">STRATALERTS</div>
        <div class="footer-text">© 2025 StratAlerts. Built for traders, by traders.</div>
        <a href="/app" class="btn-primary" style="font-size: 12px; padding: 10px 24px;">LAUNCH APP →</a>
    </div>
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
    <title>Dashboard — StratAlerts</title>
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #080c10;
            --bg2: #0d1117;
            --bg3: #111820;
            --border: #1e2d3d;
            --border2: #243447;
            --accent: #00d4ff;
            --accent2: #00ff88;
            --text: #c9d1d9;
            --text2: #8b949e;
            --text3: #58677a;
            --red: #ff4757;
            --green: #00ff88;
            --yellow: #ffd43b;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'IBM Plex Sans', sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
        }
        body::before {
            content: '';
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: repeating-linear-gradient(
                0deg, transparent, transparent 2px,
                rgba(0,212,255,0.012) 2px, rgba(0,212,255,0.012) 4px
            );
            pointer-events: none; z-index: 9999;
        }

        /* LAYOUT */
        .layout { display: flex; min-height: 100vh; }

        /* SIDEBAR */
        .sidebar {
            width: 240px; flex-shrink: 0;
            background: var(--bg2);
            border-right: 1px solid var(--border);
            display: flex; flex-direction: column;
            padding: 24px 0;
            position: fixed; top: 0; bottom: 0; left: 0;
        }
        .sidebar-logo {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 14px; font-weight: 600;
            color: var(--accent);
            letter-spacing: 2px;
            padding: 0 24px 24px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 16px;
            text-decoration: none;
            display: block;
        }
        .sidebar-logo span { color: var(--text3); }
        .sidebar-nav a {
            display: flex; align-items: center; gap: 10px;
            padding: 10px 24px;
            color: var(--text2);
            text-decoration: none;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.2s;
            border-left: 2px solid transparent;
        }
        .sidebar-nav a:hover, .sidebar-nav a.active {
            color: var(--accent);
            background: rgba(0,212,255,0.05);
            border-left-color: var(--accent);
        }
        .sidebar-nav a .icon { font-size: 15px; width: 20px; }
        .sidebar-section {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 9px; color: var(--text3);
            letter-spacing: 2px; text-transform: uppercase;
            padding: 16px 24px 8px;
        }
        .sidebar-bottom {
            margin-top: auto;
            padding: 16px 24px;
            border-top: 1px solid var(--border);
        }
        .plan-badge {
            display: inline-block;
            background: rgba(0,212,255,0.1);
            border: 1px solid rgba(0,212,255,0.2);
            color: var(--accent);
            font-family: 'IBM Plex Mono', monospace;
            font-size: 9px;
            letter-spacing: 1px;
            padding: 3px 8px;
            border-radius: 2px;
            margin-bottom: 8px;
        }
        .upgrade-link {
            font-size: 11px; color: var(--text3);
            text-decoration: none; display: block;
        }
        .upgrade-link:hover { color: var(--accent); }

        /* MAIN */
        .main {
            margin-left: 240px;
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        .topbar {
            background: var(--bg2);
            border-bottom: 1px solid var(--border);
            padding: 16px 32px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .topbar-title {
            font-size: 14px; font-weight: 600;
            color: #e6edf3;
        }
        .topbar-sub {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 11px; color: var(--text3);
        }
        .status-dot {
            display: flex; align-items: center; gap: 8px;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 11px; color: var(--green);
        }
        .status-dot::before {
            content: '';
            width: 6px; height: 6px;
            background: var(--green);
            border-radius: 50%;
            animation: blink 1.5s ease-in-out infinite;
        }
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }

        .content { padding: 32px; }

        /* TABS */
        .tabs {
            display: flex; gap: 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 32px;
        }
        .tab {
            padding: 12px 24px;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 12px;
            color: var(--text3);
            cursor: pointer;
            border-bottom: 2px solid transparent;
            margin-bottom: -1px;
            transition: all 0.2s;
            letter-spacing: 0.5px;
        }
        .tab:hover { color: var(--text2); }
        .tab.active { color: var(--accent); border-bottom-color: var(--accent); }

        /* FORM */
        .form-card {
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 32px;
            max-width: 680px;
        }
        .form-title {
            font-size: 16px; font-weight: 600;
            color: #e6edf3; margin-bottom: 6px;
        }
        .form-sub { color: var(--text2); font-size: 13px; margin-bottom: 28px; }
        .field { margin-bottom: 20px; }
        .field label {
            display: block;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 10px; color: var(--text3);
            letter-spacing: 1.5px; text-transform: uppercase;
            margin-bottom: 8px;
        }
        .field input, .field textarea, .field select {
            width: 100%;
            background: var(--bg3);
            border: 1px solid var(--border);
            border-radius: 2px;
            color: var(--text);
            font-family: 'IBM Plex Sans', sans-serif;
            font-size: 14px;
            padding: 12px 16px;
            transition: border-color 0.2s;
            outline: none;
        }
        .field input:focus, .field textarea:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(0,212,255,0.08);
        }
        .field textarea { min-height: 100px; resize: vertical; }
        .submit-btn {
            background: var(--accent);
            color: var(--bg);
            border: none;
            padding: 13px 32px;
            border-radius: 2px;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 1px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .submit-btn:hover {
            background: #33dcff;
            box-shadow: 0 4px 20px rgba(0,212,255,0.3);
        }
        .submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }

        /* RESULT */
        .result-box {
            margin-top: 20px;
            padding: 20px;
            border-radius: 4px;
            display: none;
            font-size: 13px;
        }
        .result-box.success {
            background: rgba(0,255,136,0.07);
            border: 1px solid rgba(0,255,136,0.3);
            color: var(--green);
        }
        .result-box.error {
            background: rgba(255,71,87,0.07);
            border: 1px solid rgba(255,71,87,0.3);
            color: var(--red);
        }
        .result-box .result-title { font-weight: 600; margin-bottom: 8px; font-size: 14px; }
        .result-box .result-row {
            display: flex; gap: 8px;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 11px;
            color: var(--text2);
            margin-top: 6px;
        }
        .result-box .result-row .key { color: var(--text3); }

        /* EXAMPLES */
        .examples-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
            margin-top: 20px;
        }
        .example-chip {
            background: var(--bg3);
            border: 1px solid var(--border);
            border-radius: 2px;
            padding: 10px 14px;
            font-size: 12px;
            color: var(--text2);
            cursor: pointer;
            transition: all 0.2s;
        }
        .example-chip:hover {
            border-color: var(--accent);
            color: var(--accent);
            background: rgba(0,212,255,0.05);
        }
        .examples-label {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 10px; color: var(--text3);
            letter-spacing: 1.5px; text-transform: uppercase;
            margin-bottom: 10px; margin-top: 28px;
        }

        /* AI CHAT */
        .chat-container {
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 4px;
            max-width: 680px;
            display: flex;
            flex-direction: column;
            height: 480px;
        }
        .chat-header {
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
            display: flex; align-items: center; gap: 10px;
        }
        .chat-header-title {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 12px; color: var(--accent);
            letter-spacing: 1px;
        }
        .chat-messages {
            flex: 1; overflow-y: auto;
            padding: 20px;
            display: flex; flex-direction: column; gap: 12px;
        }
        .chat-messages::-webkit-scrollbar { width: 4px; }
        .chat-messages::-webkit-scrollbar-track { background: transparent; }
        .chat-messages::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 2px; }
        .msg {
            max-width: 85%;
            padding: 10px 14px;
            border-radius: 2px;
            font-size: 13px;
            line-height: 1.6;
        }
        .msg.ai {
            background: var(--bg3);
            border: 1px solid var(--border);
            color: var(--text);
            align-self: flex-start;
        }
        .msg.user {
            background: rgba(0,212,255,0.1);
            border: 1px solid rgba(0,212,255,0.2);
            color: var(--accent);
            align-self: flex-end;
        }
        .msg-label {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 9px; color: var(--text3);
            letter-spacing: 1px; text-transform: uppercase;
            margin-bottom: 4px;
        }
        .chat-input-row {
            padding: 16px 20px;
            border-top: 1px solid var(--border);
            display: flex; gap: 10px;
        }
        .chat-input {
            flex: 1;
            background: var(--bg3);
            border: 1px solid var(--border);
            border-radius: 2px;
            color: var(--text);
            font-family: 'IBM Plex Sans', sans-serif;
            font-size: 13px;
            padding: 10px 14px;
            outline: none;
        }
        .chat-input:focus { border-color: var(--accent); }
        .chat-send {
            background: var(--accent);
            color: var(--bg);
            border: none;
            padding: 10px 18px;
            border-radius: 2px;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 11px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .chat-send:hover { background: #33dcff; }
        .premium-lock {
            display: flex; flex-direction: column;
            align-items: center; justify-content: center;
            height: 100%;
            color: var(--text3);
            text-align: center;
            gap: 12px;
        }
        .premium-lock .lock-icon { font-size: 32px; opacity: 0.5; }
        .premium-lock p { font-size: 13px; max-width: 280px; line-height: 1.6; }
        .premium-lock a {
            background: var(--accent);
            color: var(--bg);
            padding: 10px 24px;
            border-radius: 2px;
            text-decoration: none;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 1px;
        }

        /* STRATEGIES LIST */
        .strategies-list { max-width: 680px; }
        .strategy-item {
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 20px 24px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 16px;
            transition: border-color 0.2s;
        }
        .strategy-item:hover { border-color: var(--border2); }
        .strategy-ticker {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 14px; font-weight: 600;
            color: var(--accent);
        }
        .strategy-type-badge {
            display: inline-block;
            background: rgba(0,212,255,0.08);
            border: 1px solid rgba(0,212,255,0.15);
            color: var(--text3);
            font-family: 'IBM Plex Mono', monospace;
            font-size: 9px; letter-spacing: 1px;
            padding: 2px 8px; border-radius: 2px;
            margin-left: 8px;
        }
        .strategy-desc {
            font-size: 13px; color: var(--text2);
            margin-top: 6px; line-height: 1.5;
        }
        .strategy-date {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 10px; color: var(--text3);
            margin-top: 8px;
        }
        .strategy-actions { display: flex; gap: 8px; flex-shrink: 0; }
        .action-btn {
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text3);
            padding: 6px 12px;
            border-radius: 2px;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 10px;
            cursor: pointer;
            transition: all 0.2s;
            letter-spacing: 0.5px;
        }
        .action-btn:hover { border-color: var(--accent); color: var(--accent); }
        .action-btn.danger:hover { border-color: var(--red); color: var(--red); }
        .empty-state {
            text-align: center; padding: 60px 32px;
            color: var(--text3);
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 4px;
            max-width: 680px;
        }
        .empty-state .icon { font-size: 36px; margin-bottom: 16px; opacity: 0.5; }
        .empty-state p { font-size: 14px; margin-bottom: 20px; }

        /* EDIT MODAL */
        .modal-overlay {
            position: fixed; inset: 0;
            background: rgba(8,12,16,0.85);
            backdrop-filter: blur(4px);
            z-index: 1000;
            display: none;
            align-items: center; justify-content: center;
        }
        .modal-overlay.open { display: flex; }
        .modal {
            background: var(--bg2);
            border: 1px solid var(--border2);
            border-radius: 4px;
            padding: 36px;
            width: 100%; max-width: 520px;
            position: relative;
        }
        .modal-title {
            font-size: 16px; font-weight: 600;
            color: #e6edf3; margin-bottom: 20px;
        }
        .modal-close {
            position: absolute; top: 16px; right: 16px;
            background: transparent; border: none;
            color: var(--text3); cursor: pointer;
            font-size: 20px; line-height: 1;
            transition: color 0.2s;
        }
        .modal-close:hover { color: var(--text); }
        .modal-actions { display: flex; gap: 12px; margin-top: 24px; }
        .modal-cancel {
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text2);
            padding: 11px 24px;
            border-radius: 2px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .modal-cancel:hover { border-color: var(--text3); }

        @media (max-width: 768px) {
            .sidebar { display: none; }
            .main { margin-left: 0; }
            .examples-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
<div class="layout">

    <!-- SIDEBAR -->
    <aside class="sidebar">
        <a href="/" class="sidebar-logo">STRAT<span>ALERTS</span></a>
        <nav class="sidebar-nav">
            <div class="sidebar-section">// Main</div>
            <a href="#" class="active" onclick="showTab('create')">
                <span class="icon">＋</span> New Alert
            </a>
            <a href="#" onclick="showTab('strategies')">
                <span class="icon">📋</span> My Strategies
            </a>
            <div class="sidebar-section">// Premium</div>
            <a href="#" onclick="showTab('ai-chat')">
                <span class="icon">🤖</span> AI Chat
            </a>
        </nav>
        <div class="sidebar-bottom">
            <div class="plan-badge">FREE PLAN</div>
            <a href="/#pricing" class="upgrade-link">→ Upgrade to Premium $9.99/mo</a>
        </div>
    </aside>

    <!-- MAIN CONTENT -->
    <div class="main">
        <div class="topbar">
            <div>
                <div class="topbar-title">Trading Alert Dashboard</div>
                <div class="topbar-sub">// ariaghaem.pythonanywhere.com</div>
            </div>
            <div class="status-dot">MARKETS MONITORED</div>
        </div>

        <div class="content">
            <!-- TABS -->
            <div class="tabs">
                <div class="tab active" id="tab-create" onclick="showTab('create')">NEW ALERT</div>
                <div class="tab" id="tab-strategies" onclick="showTab('strategies')">MY STRATEGIES</div>
                <div class="tab" id="tab-ai-chat" onclick="showTab('ai-chat')">AI CHAT <span style="font-size:9px;color:var(--accent);margin-left:6px">PREMIUM</span></div>
            </div>

            <!-- TAB: CREATE -->
            <div id="pane-create">
                <div class="form-card">
                    <div class="form-title">Create New Alert</div>
                    <p class="form-sub">Describe your trading strategy in plain English below.</p>
                    <form id="alertForm">
                        <div class="field">
                            <label>Email Address</label>
                            <input type="email" id="email" required placeholder="you@example.com">
                        </div>
                        <div class="field">
                            <label>Strategy Description</label>
                            <textarea id="strategy" required placeholder="e.g. Alert me when Apple goes above $220..."></textarea>
                        </div>
                        <button type="submit" class="submit-btn" id="submitBtn">⚡ CREATE ALERT</button>
                    </form>
                    <div class="result-box" id="result"></div>
                    <div class="examples-label">// Quick Examples</div>
                    <div class="examples-grid">
                        <div class="example-chip" onclick="fill('Alert me when Apple goes above $220')">AAPL above $220</div>
                        <div class="example-chip" onclick="fill('Notify me if Tesla drops below $200')">TSLA below $200</div>
                        <div class="example-chip" onclick="fill('Alert when Bitcoin hits $100,000')">BTC hits $100k</div>
                        <div class="example-chip" onclick="fill('Tell me when NVDA exceeds $900')">NVDA above $900</div>
                        <div class="example-chip" onclick="fill('Notify me if SPY falls below $500')">SPY below $500</div>
                        <div class="example-chip" onclick="fill('Alert me when Ethereum reaches $5,000')">ETH reaches $5k</div>
                    </div>
                </div>
            </div>

            <!-- TAB: STRATEGIES -->
            <div id="pane-strategies" style="display:none;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;max-width:680px;">
                    <div>
                        <div style="font-size:16px;font-weight:600;color:#e6edf3">My Strategies</div>
                        <div style="font-size:12px;color:var(--text3);margin-top:4px;font-family:'IBM Plex Mono',monospace;">Enter your email to load alerts</div>
                    </div>
                </div>
                <div style="max-width:680px;margin-bottom:20px;display:flex;gap:10px;">
                    <input type="email" id="loadEmail" placeholder="Enter your email to load strategies..."
                        style="flex:1;background:var(--bg2);border:1px solid var(--border);border-radius:2px;color:var(--text);font-family:'IBM Plex Sans',sans-serif;font-size:14px;padding:11px 16px;outline:none;">
                    <button onclick="loadStrategies()" class="submit-btn">LOAD →</button>
                </div>
                <div class="strategies-list" id="strategiesList">
                    <div class="empty-state">
                        <div class="icon">📭</div>
                        <p>Enter your email above to load your saved strategies.</p>
                    </div>
                </div>
            </div>

            <!-- TAB: AI CHAT -->
            <div id="pane-ai-chat" style="display:none;">
                <div class="chat-container">
                    <div class="chat-header">
                        <span style="font-size:16px;">🤖</span>
                        <div class="chat-header-title">AI STRATEGY ASSISTANT</div>
                        <span style="margin-left:auto;font-size:11px;color:var(--text3);font-family:'IBM Plex Mono',monospace">PREMIUM FEATURE</span>
                    </div>
                    <div class="chat-messages" id="chatMessages">
                        <div class="premium-lock">
                            <div class="lock-icon">🔒</div>
                            <p>AI strategy conversation is a <strong style="color:var(--text)">Premium</strong> feature. Upgrade to refine your strategies through dialogue, get AI recommendations, and more.</p>
                            <a href="/#pricing">UPGRADE · $9.99/MO →</a>
                        </div>
                    </div>
                    <div class="chat-input-row" style="opacity:0.4;pointer-events:none;">
                        <input class="chat-input" placeholder="Upgrade to Premium to use AI chat..." disabled>
                        <button class="chat-send" disabled>SEND</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- EDIT MODAL -->
<div class="modal-overlay" id="editModal">
    <div class="modal">
        <button class="modal-close" onclick="closeModal()">✕</button>
        <div class="modal-title">Edit Strategy</div>
        <input type="hidden" id="editId">
        <div class="field">
            <label>Email</label>
            <input type="email" id="editEmail" placeholder="your@email.com">
        </div>
        <div class="field">
            <label>Strategy Description</label>
            <textarea id="editStrategy" style="min-height:80px;"></textarea>
        </div>
        <div class="modal-actions">
            <button class="submit-btn" onclick="saveEdit()">SAVE CHANGES</button>
            <button class="modal-cancel" onclick="closeModal()">Cancel</button>
        </div>
    </div>
</div>

<script>
    function showTab(tab) {
        ['create','strategies','ai-chat'].forEach(t => {
            document.getElementById('pane-' + t).style.display = 'none';
            document.getElementById('tab-' + t).classList.remove('active');
        });
        document.getElementById('pane-' + tab).style.display = 'block';
        document.getElementById('tab-' + tab).classList.add('active');
    }

    function fill(text) {
        document.getElementById('strategy').value = text;
        document.getElementById('strategy').focus();
    }

    document.getElementById('alertForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('submitBtn');
        btn.disabled = true; btn.textContent = 'CREATING...';
        const email = document.getElementById('email').value;
        const strategy = document.getElementById('strategy').value;
        const result = document.getElementById('result');
        try {
            const resp = await fetch('/add-strategy', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email, strategy})
            });
            const data = await resp.json();
            result.style.display = 'block';
            if (data.success) {
                result.className = 'result-box success';
                result.innerHTML = `
                    <div class="result-title">✓ Alert Created Successfully</div>
                    <div class="result-row"><span class="key">TICKER</span> ${data.parsed.ticker}</div>
                    <div class="result-row"><span class="key">TYPE&nbsp;&nbsp;</span> ${data.parsed.type}</div>
                    <div class="result-row"><span class="key">COND&nbsp;&nbsp;</span> ${data.parsed.condition} $${data.parsed.threshold}</div>
                    <div class="result-row" style="margin-top:10px;color:var(--text3)">Market is now being monitored 24/7. You'll be emailed when conditions are met.</div>
                `;
                document.getElementById('strategy').value = '';
            } else {
                result.className = 'result-box error';
                result.innerHTML = '<div class="result-title">✕ Error</div><p>' + data.error + '</p>';
            }
        } catch(err) {
            result.style.display = 'block';
            result.className = 'result-box error';
            result.innerHTML = '<div class="result-title">✕ Connection Error</div><p>Please try again.</p>';
        }
        btn.disabled = false; btn.textContent = '⚡ CREATE ALERT';
    });

    async function loadStrategies() {
        const email = document.getElementById('loadEmail').value;
        if (!email) return;
        const list = document.getElementById('strategiesList');
        list.innerHTML = '<div style="color:var(--text3);font-family:\'IBM Plex Mono\',monospace;font-size:12px;padding:20px;">LOADING...</div>';
        try {
            const resp = await fetch('/get-strategies?email=' + encodeURIComponent(email));
            const data = await resp.json();
            if (!data.strategies || data.strategies.length === 0) {
                list.innerHTML = '<div class="empty-state"><div class="icon">📭</div><p>No strategies found for this email.</p></div>';
                return;
            }
            list.innerHTML = data.strategies.map(s => `
                <div class="strategy-item">
                    <div style="flex:1">
                        <div>
                            <span class="strategy-ticker">${s.ticker}</span>
                            <span class="strategy-type-badge">${s.strategy_type}</span>
                        </div>
                        <div class="strategy-desc">${s.raw_description}</div>
                        <div class="strategy-date">${s.condition.toUpperCase()} · $${s.threshold} · Created ${new Date(s.created_at).toLocaleDateString()}</div>
                    </div>
                    <div class="strategy-actions">
                        <button class="action-btn" onclick="openEdit(${s.id}, '${email}', \`${s.raw_description.replace(/`/g, "'")}\`)">EDIT</button>
                    </div>
                </div>
            `).join('');
        } catch(err) {
            list.innerHTML = '<div class="empty-state"><div class="icon">⚠️</div><p>Failed to load. Please try again.</p></div>';
        }
    }

    function openEdit(id, email, desc) {
        document.getElementById('editId').value = id;
        document.getElementById('editEmail').value = email;
        document.getElementById('editStrategy').value = desc;
        document.getElementById('editModal').classList.add('open');
    }
    function closeModal() {
        document.getElementById('editModal').classList.remove('open');
    }
    async function saveEdit() {
        const id = document.getElementById('editId').value;
        const email = document.getElementById('editEmail').value;
        const strategy = document.getElementById('editStrategy').value;
        try {
            const resp = await fetch('/update-strategy', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id, email, strategy})
            });
            const data = await resp.json();
            if (data.success) {
                closeModal();
                loadStrategies();
            }
        } catch(e) {}
    }

    // Close modal on overlay click
    document.getElementById('editModal').addEventListener('click', function(e) {
        if (e.target === this) closeModal();
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
        if not email or not strategy_text:
            return jsonify({'success': False, 'error': 'Email and strategy required'})
        parsed = parse_strategy(strategy_text)
        strategy_id = add_strategy_to_db(email, parsed)
        print(f"✓ Strategy #{strategy_id} created for {email}")
        return jsonify({'success': True, 'strategy_id': strategy_id, 'parsed': parsed})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get-strategies')
def get_strategies():
    try:
        email = request.args.get('email')
        if not email:
            return jsonify({'success': False, 'error': 'Email required'})
        rows = get_strategies_by_email(email)
        strategies = []
        for row in rows:
            strategies.append({
                'id': row[0], 'email': row[1], 'ticker': row[2],
                'strategy_type': row[3], 'condition': row[4],
                'threshold': row[5], 'raw_description': row[6],
                'created_at': row[7]
            })
        return jsonify({'success': True, 'strategies': strategies})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/update-strategy', methods=['POST'])
def update_strategy():
    try:
        data = request.json
        strategy_id = data.get('id')
        email = data.get('email')
        strategy_text = data.get('strategy')
        if not all([strategy_id, email, strategy_text]):
            return jsonify({'success': False, 'error': 'Missing fields'})
        parsed = parse_strategy(strategy_text)
        update_strategy_in_db(strategy_id, email, parsed)
        return jsonify({'success': True, 'parsed': parsed})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'message': 'StratAlerts is running!'})


# ============================================================================
# RUN
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
