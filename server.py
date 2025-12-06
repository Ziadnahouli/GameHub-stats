from flask import Flask, request, jsonify, render_template_string
import sqlite3
import time
from datetime import datetime

app = Flask(__name__)
DB_FILE = 'analytics.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Table to store unique users
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id TEXT PRIMARY KEY, first_seen REAL, last_seen REAL, version TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/ping', methods=['POST'])
def ping():
    """Desktop App calls this every 5 minutes"""
    data = request.json
    user_id = data.get('id')
    version = data.get('version')
    now = time.time()
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Try to update existing user
    c.execute("UPDATE users SET last_seen = ?, version = ? WHERE user_id = ?", (now, version, user_id))
    
    # If no row updated, it's a NEW USER
    if c.rowcount == 0:
        c.execute("INSERT INTO users (user_id, first_seen, last_seen, version) VALUES (?, ?, ?, ?)", 
                  (user_id, now, now, version))
    
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route('/')
def dashboard():
    """The Dashboard YOU look at"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    now = time.time()
    five_mins_ago = now - 300  # 5 minutes buffer
    
    # 1. Total Users (All time)
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    
    # 2. Online Users (Pinged in last 5 mins)
    c.execute("SELECT COUNT(*) FROM users WHERE last_seen > ?", (five_mins_ago,))
    online_users = c.fetchone()[0]
    
    # 3. New Users (Joined in last 24 hours)
    one_day_ago = now - 86400
    c.execute("SELECT COUNT(*) FROM users WHERE first_seen > ?", (one_day_ago,))
    new_users_24h = c.fetchone()[0]
    
    conn.close()
    
    # Simple HTML Dashboard
    html = f"""
    <html>
    <head>
        <title>Game Hub Live</title>
        <meta http-equiv="refresh" content="30"> <!-- Auto refresh every 30s -->
        <style>
            body {{ font-family: sans-serif; background: #121212; color: white; text-align: center; padding: 50px; }}
            .grid {{ display: flex; justify-content: center; gap: 20px; }}
            .card {{ background: #222; padding: 20px; border-radius: 10px; width: 200px; }}
            h1 {{ color: #5865F2; }}
            .number {{ font-size: 3rem; font-weight: bold; margin: 10px 0; }}
            .green {{ color: #2ecc71; }}
        </style>
    </head>
    <body>
        <h1>Game Hub Live Analytics</h1>
        <div class="grid">
            <div class="card">
                <h3>Online Now</h3>
                <div class="number green">{online_users}</div>
                <p>Active Users</p>
            </div>
            <div class="card">
                <h3>Total Installs</h3>
                <div class="number">{total_users}</div>
                <p>Offline: {total_users - online_users}</p>
            </div>
            <div class="card">
                <h3>New (24h)</h3>
                <div class="number">{new_users_24h}</div>
            </div>
        </div>
    </body>
    </html>
    """
    return html

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)