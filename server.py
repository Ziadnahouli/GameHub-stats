# server.py
from flask import Flask, request, jsonify
import sqlite3
import time

app = Flask(__name__)
DB_FILE = 'analytics.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, first_seen REAL, last_seen REAL, version TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/ping', methods=['POST'])
def ping():
    data = request.json
    user_id = data.get('id')
    version = data.get('version')
    now = time.time()
    
    # DEBUG PRINT
    print(f"✅ Received PING from User: {user_id} (v{version})")
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET last_seen = ?, version = ? WHERE user_id = ?", (now, version, user_id))
    if c.rowcount == 0:
        c.execute("INSERT INTO users (user_id, first_seen, last_seen, version) VALUES (?, ?, ?, ?)", (user_id, now, now, version))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route('/')
def dashboard():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now = time.time()
    online_users = c.execute("SELECT COUNT(*) FROM users WHERE last_seen > ?", (now - 300,)).fetchone()[0]
    total_users = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    
    return f"""
    <html><body style='background:#222;color:white;text-align:center;font-family:sans-serif;padding:50px;'>
        <h1>Game Hub Stats</h1>
        <h2>Online Now: <span style='color:#0f0;'>{online_users}</span></h2>
        <h3>Total Installs: {total_users}</h3>
    </body></html>
    """

if __name__ == '__main__':
    # LISTEN ON ALL INTERFACES
    print("Server running on http://127.0.0.1:10000")
    app.run(host='0.0.0.0', port=10000)
