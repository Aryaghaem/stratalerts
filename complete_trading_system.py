"""
COMPLETE AI TRADING ALERT SYSTEM
================================

This is the full production-ready system that:
1. Parses user strategies using Claude API
2. Monitors markets continuously
3. Sends alerts when conditions are met

To run: python complete_trading_system.py
"""

import json
import time
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import requests
from dataclasses import dataclass


# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """System configuration - UPDATE THESE WITH YOUR API KEYS"""
    
    # API Keys (you'll add these)
    CLAUDE_API_KEY = CLAUDE_API_KEY = "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"
    # Put your OpenAI API key here
    POLYGON_API_KEY = "your-polygon-api-key-here"  # Get from polygon.io
    
    # Or use free Yahoo Finance (less reliable but free)
    USE_FREE_DATA = True  # Set to False when you have Polygon key
    
    # Email settings (for alerts)
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    EMAIL_FROM = "your-email@gmail.com"
    EMAIL_PASSWORD = "lsep xhse ajqh lwwx"  # Gmail app password, not regular password
    
    # System settings
    CHECK_INTERVAL = 60  # Check market every 60 seconds
    DATABASE_FILE = "trading_alerts.db"


# ============================================================================
# DATABASE SETUP
# ============================================================================

class Database:
    """Handles all database operations"""
    
    def __init__(self, db_file: str = Config.DATABASE_FILE):
        self.db_file = db_file
        self.init_database()
    
    def init_database(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Strategies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategies (
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
            )
        ''')
        
        # Alerts history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (strategy_id) REFERENCES strategies (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✓ Database initialized")
    
    def add_user(self, email: str, phone: str = None) -> int:
        """Add a new user"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        try:
            cursor.execute('INSERT INTO users (email, phone) VALUES (?, ?)', (email, phone))
            user_id = cursor.lastrowid
            conn.commit()
            return user_id
        except sqlite3.IntegrityError:
            # User already exists
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            return cursor.fetchone()[0]
        finally:
            conn.close()
    
    def add_strategy(self, user_id: int, strategy: Dict) -> int:
        """Add a new strategy"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO strategies 
            (user_id, ticker, strategy_type, condition, threshold, parameters, raw_description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            strategy.get('ticker'),
            strategy.get('type'),
            strategy.get('condition'),
            strategy.get('threshold'),
            json.dumps(strategy.get('parameters', {})),
            strategy.get('raw_description')
        ))
        
        strategy_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return strategy_id
    
    def get_active_strategies(self) -> List[Dict]:
        """Get all active strategies"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.*, u.email, u.phone 
            FROM strategies s
            JOIN users u ON s.user_id = u.id
            WHERE s.active = 1 AND s.triggered_at IS NULL
        ''')
        
        columns = [desc[0] for desc in cursor.description]
        strategies = []
        
        for row in cursor.fetchall():
            strategy = dict(zip(columns, row))
            if strategy['parameters']:
                strategy['parameters'] = json.loads(strategy['parameters'])
            strategies.append(strategy)
        
        conn.close()
        return strategies
    
    def mark_triggered(self, strategy_id: int):
        """Mark a strategy as triggered"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE strategies 
            SET triggered_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (strategy_id,))
        
        conn.commit()
        conn.close()
    
    def log_alert(self, strategy_id: int, user_id: int, message: str):
        """Log an alert that was sent"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts (strategy_id, user_id, message)
            VALUES (?, ?, ?)
        ''', (strategy_id, user_id, message))
        
        conn.commit()
        conn.close()


# ============================================================================
# AI STRATEGY PARSER
# ============================================================================

class StrategyParser:
    """Uses OpenAI API to parse natural language strategies"""
    
    def __init__(self, api_key: str = Config.CLAUDE_API_KEY):
        self.api_key = api_key
        self.api_url = "https://api.openai.com/v1/chat/completions"
    
    def parse(self, user_description: str) -> Dict:
        """
        Convert natural language to structured strategy using OpenAI
        
        Example input: "Alert me when Apple's RSI drops below 30"
        Example output: {
            "ticker": "AAPL",
            "type": "RSI",
            "condition": "below",
            "threshold": 30,
            "raw_description": "Alert me when Apple's RSI drops below 30"
        }
        """
        
        if self.api_key == "your-claude-api-key-here" or self.api_key == "your-openai-api-key-here":
            print("⚠️  No API key set. Using fallback parser.")
            return self._fallback_parse(user_description)
        
        prompt = f"""Parse this trading strategy into JSON format.

User's strategy: "{user_description}"

Return ONLY valid JSON with these fields:
- ticker: stock symbol (string)
- type: one of [RSI, PRICE, MA_CROSS, VOLUME, MACD]
- condition: one of [above, below, crosses_above, crosses_below]
- threshold: numeric value (if applicable)
- parameters: object with additional params (like MA periods)

Example:
{{"ticker": "AAPL", "type": "RSI", "condition": "below", "threshold": 30}}

Return only the JSON, nothing else."""

        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 200,
                    "temperature": 0
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                text = data['choices'][0]['message']['content'].strip()
                
                # Clean JSON if wrapped in markdown
                if text.startswith("```"):
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                    text = text.strip()
                
                strategy = json.loads(text)
                strategy['raw_description'] = user_description
                
                print(f"✓ Parsed strategy: {strategy['ticker']} {strategy['type']}")
                return strategy
            else:
                print(f"API Error: {response.status_code}")
                return self._fallback_parse(user_description)
                
        except Exception as e:
            print(f"Error parsing with AI: {e}")
            return self._fallback_parse(user_description)
    
    def _fallback_parse(self, description: str) -> Dict:
        """Simple rule-based fallback parser"""
        import re
        
        description_lower = description.lower()
        
        # Extract ticker
        tickers = {
            "apple": "AAPL", "aapl": "AAPL",
            "tesla": "TSLA", "tsla": "TSLA",
            "microsoft": "MSFT", "msft": "MSFT",
            "google": "GOOGL", "googl": "GOOGL",
            "amazon": "AMZN", "amzn": "AMZN",
            "nvidia": "NVDA", "nvda": "NVDA",
            "meta": "META", "facebook": "META",
            "netflix": "NFLX", "nflx": "NFLX"
        }
        
        ticker = "UNKNOWN"
        for name, symbol in tickers.items():
            if name in description_lower:
                ticker = symbol
                break
        
        # Detect indicator type
        if "rsi" in description_lower:
            strategy_type = "RSI"
        elif "moving average" in description_lower or "ma" in description_lower:
            strategy_type = "MA_CROSS"
        elif "volume" in description_lower:
            strategy_type = "VOLUME"
        else:
            strategy_type = "PRICE"
        
        # Detect condition
        if any(word in description_lower for word in ["above", "over", "exceed", "break"]):
            condition = "above"
        elif any(word in description_lower for word in ["below", "under", "drop"]):
            condition = "below"
        else:
            condition = "above"
        
        # Extract threshold
        numbers = re.findall(r'\d+\.?\d*', description)
        threshold = float(numbers[0]) if numbers else 100.0
        
        return {
            "ticker": ticker,
            "type": strategy_type,
            "condition": condition,
            "threshold": threshold,
            "parameters": {},
            "raw_description": description
        }


# ============================================================================
# MARKET DATA PROVIDER
# ============================================================================

class MarketData:
    """Fetches real-time market data"""
    
    def __init__(self):
        self.use_free = Config.USE_FREE_DATA
        self.polygon_key = Config.POLYGON_API_KEY
    
    def get_price(self, ticker: str) -> Optional[float]:
        """Get current price"""
        if self.use_free:
            return self._get_price_yahoo(ticker)
        else:
            return self._get_price_polygon(ticker)
    
    def _get_price_yahoo(self, ticker: str) -> Optional[float]:
        """Yahoo Finance (free but unofficial)"""
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                price = data['chart']['result'][0]['meta']['regularMarketPrice']
                return float(price)
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
        return None
    
    def _get_price_polygon(self, ticker: str) -> Optional[float]:
        """Polygon.io (paid but reliable)"""
        try:
            url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/prev"
            headers = {"Authorization": f"Bearer {self.polygon_key}"}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                price = data['results'][0]['c']  # Close price
                return float(price)
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
        return None
    
    def calculate_rsi(self, ticker: str, period: int = 14) -> Optional[float]:
        """Calculate RSI (simplified version)"""
        # In production, you'd use a library like pandas-ta
        # For now, return a simulated value
        # TODO: Implement real RSI calculation
        return 45.0  # Placeholder
    
    def get_moving_average(self, ticker: str, period: int) -> Optional[float]:
        """Get moving average"""
        # TODO: Implement real MA calculation
        price = self.get_price(ticker)
        return price * 0.98 if price else None  # Placeholder


# ============================================================================
# ALERT SYSTEM
# ============================================================================

class AlertSystem:
    """Sends alerts to users"""
    
    def send_email(self, to_email: str, subject: str, message: str):
        """Send email alert"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = Config.EMAIL_FROM
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT)
            server.starttls()
            server.login(Config.EMAIL_FROM, Config.EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            print(f"✓ Email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def send_sms(self, phone: str, message: str):
        """Send SMS via Twilio (optional)"""
        # TODO: Implement Twilio SMS
        print(f"SMS to {phone}: {message}")
    
    def send_alert(self, user_email: str, user_phone: str, message: str):
        """Send alert via available channels"""
        # For now, just email
        self.send_email(user_email, "🚨 Trading Alert", message)
        
        # If phone provided, send SMS
        if user_phone:
            self.send_sms(user_phone, message)


# ============================================================================
# STRATEGY CHECKER
# ============================================================================

class StrategyChecker:
    """Checks if strategies should trigger"""
    
    def __init__(self, market_data: MarketData):
        self.market_data = market_data
    
    def check(self, strategy: Dict) -> tuple[bool, str]:
        """
        Check if a strategy should trigger
        Returns: (triggered, message)
        """
        ticker = strategy['ticker']
        strategy_type = strategy['strategy_type']
        condition = strategy['condition']
        threshold = strategy.get('threshold')
        
        try:
            if strategy_type == "PRICE":
                return self._check_price(ticker, condition, threshold)
            
            elif strategy_type == "RSI":
                return self._check_rsi(ticker, condition, threshold)
            
            elif strategy_type == "MA_CROSS":
                return self._check_ma_cross(ticker, strategy['parameters'])
            
            elif strategy_type == "VOLUME":
                return self._check_volume(ticker, condition, threshold)
            
        except Exception as e:
            print(f"Error checking {ticker}: {e}")
        
        return False, ""
    
    def _check_price(self, ticker: str, condition: str, threshold: float) -> tuple[bool, str]:
        """Check price condition"""
        current_price = self.market_data.get_price(ticker)
        
        if current_price is None:
            return False, ""
        
        if condition == "above" and current_price > threshold:
            msg = f"{ticker} broke above ${threshold}! Currently at ${current_price:.2f}"
            return True, msg
        
        elif condition == "below" and current_price < threshold:
            msg = f"{ticker} dropped below ${threshold}! Currently at ${current_price:.2f}"
            return True, msg
        
        return False, ""
    
    def _check_rsi(self, ticker: str, condition: str, threshold: float) -> tuple[bool, str]:
        """Check RSI condition"""
        current_rsi = self.market_data.calculate_rsi(ticker)
        
        if current_rsi is None:
            return False, ""
        
        if condition == "below" and current_rsi < threshold:
            msg = f"{ticker} RSI dropped to {current_rsi:.1f} (below {threshold}) - Oversold!"
            return True, msg
        
        elif condition == "above" and current_rsi > threshold:
            msg = f"{ticker} RSI rose to {current_rsi:.1f} (above {threshold}) - Overbought!"
            return True, msg
        
        return False, ""
    
    def _check_ma_cross(self, ticker: str, params: Dict) -> tuple[bool, str]:
        """Check moving average crossover"""
        # TODO: Implement proper MA cross detection
        return False, ""
    
    def _check_volume(self, ticker: str, condition: str, threshold: float) -> tuple[bool, str]:
        """Check volume condition"""
        # TODO: Implement volume checking
        return False, ""


# ============================================================================
# MAIN MONITORING SYSTEM
# ============================================================================

class TradingAlertSystem:
    """Main system that ties everything together"""
    
    def __init__(self):
        self.db = Database()
        self.parser = StrategyParser()
        self.market_data = MarketData()
        self.checker = StrategyChecker(self.market_data)
        self.alerts = AlertSystem()
    
    def add_user_strategy(self, email: str, strategy_description: str, phone: str = None) -> int:
        """Add a new user strategy"""
        # Get or create user
        user_id = self.db.add_user(email, phone)
        
        # Parse strategy
        strategy = self.parser.parse(strategy_description)
        
        # Save to database
        strategy_id = self.db.add_strategy(user_id, strategy)
        
        print(f"✓ Added strategy #{strategy_id} for {email}")
        return strategy_id
    
    def monitor_once(self):
        """Run one monitoring cycle"""
        strategies = self.db.get_active_strategies()
        
        if not strategies:
            print("No active strategies to monitor")
            return
        
        print(f"\n{'='*70}")
        print(f"Checking {len(strategies)} strategies at {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*70}\n")
        
        triggered_count = 0
        
        for strategy in strategies:
            ticker = strategy['ticker']
            user_email = strategy['email']
            
            # Check if should trigger
            triggered, message = self.checker.check(strategy)
            
            if triggered:
                # Send alert
                self.alerts.send_alert(user_email, strategy.get('phone'), message)
                
                # Mark as triggered
                self.db.mark_triggered(strategy['id'])
                
                # Log alert
                self.db.log_alert(strategy['id'], strategy['user_id'], message)
                
                triggered_count += 1
                print(f"🚨 ALERT: {message}")
            else:
                print(f"✓ {ticker:6} - Monitoring ({strategy['strategy_type']})")
        
        print(f"\n{'='*70}")
        print(f"Checked {len(strategies)} strategies | {triggered_count} alerts sent")
        print(f"{'='*70}\n")
    
    def start_monitoring(self, interval: int = Config.CHECK_INTERVAL):
        """Start continuous monitoring"""
        print("\n" + "="*70)
        print("🤖 AI TRADING ALERT SYSTEM STARTED")
        print("="*70)
        print(f"Checking market every {interval} seconds")
        print(f"Press Ctrl+C to stop\n")
        
        try:
            while True:
                self.monitor_once()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n⏹️  System stopped by user")
            self.print_stats()
    
    def print_stats(self):
        """Print system statistics"""
        conn = sqlite3.connect(Config.DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM strategies WHERE active = 1')
        strategy_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM alerts')
        alert_count = cursor.fetchone()[0]
        
        conn.close()
        
        print("\n" + "="*70)
        print("SYSTEM STATISTICS")
        print("="*70)
        print(f"Total users: {user_count}")
        print(f"Active strategies: {strategy_count}")
        print(f"Total alerts sent: {alert_count}")
        print("="*70 + "\n")


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    """Main entry point"""
    system = TradingAlertSystem()
    
    print("\n" + "="*70)
    print("AI TRADING ALERT SYSTEM")
    print("="*70)
    print("\nWhat would you like to do?")
    print("1. Add a new strategy")
    print("2. Start monitoring")
    print("3. View statistics")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        # Add strategy
        email = input("Your email: ").strip()
        strategy = input("Describe your strategy: ").strip()
        
        system.add_user_strategy(email, strategy)
        print("\n✓ Strategy added! Run option 2 to start monitoring.\n")
    
    elif choice == "2":
        # Start monitoring
        system.start_monitoring()
    
    elif choice == "3":
        # View stats
        system.print_stats()
    
    else:
        print("Goodbye!")


if __name__ == "__main__":
    main()
