import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

# --- DATABASE SETUP ---
def init_db():
    """Sets up a local database with structured tables for Events and Registrations."""
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()
    
    # 1. Events Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            location TEXT NOT NULL
        )
    """)
    
    # 2. Registrations Table linked to the Events
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            user_name TEXT NOT NULL,
            user_email TEXT NOT NULL,
            FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
        )
    """)
    
    # Insert starter events if the table is brand new
    cursor.execute("SELECT COUNT(*) FROM events")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO events (title, date, location) VALUES ('CodeAlpha Tech Summit', '2026-08-15', 'Virtual Silicon Valley')")
        cursor.execute("INSERT INTO events (title, date, location) VALUES ('Web Dev Hackathon', '2026-11-22', 'Innovation Lab')")
        
    conn.commit()
    conn.close()

# --- HTML FRONTEND (Fixed Template Syntax) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Event Registration Dashboard</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #f8fafc; color: #0f172a; margin: 0; padding: 40px; }
        .container { max-width: 800px; margin: auto; }
        h1, h2 { color: #1e3a8a; }
        .card { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 25px; }
        input, select { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #cbd5e1; border-radius: 4px; box-sizing: border-box; }
        input[type="submit"] { background: #2563eb; color: white; border: none; cursor: pointer; font-weight: bold; }
        input[type="submit"]:hover { background: #1d4ed8; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #e2e8f0; }
        th { background: #f1f5f9; }
        .cancel-btn { color: #dc2626; text-decoration: none; font-size: 14px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📅 CodeAlpha Event Management Platform</h1>
        
        <div class="card">
            <h2>🎟️ Quick Registration Form</h2>
            <form action="/register" method="POST">
                <label>Select Active Event:</label>
                <select name="event_id" required>
                    {% for event in events %}
                        <option value="{{ event[0] }}">{{ event[1] }} ({{ event[2] }} - {{ event[3] }})</option>
                    {% endfor %}
                </select>
                <input type="text" name="user_name" placeholder="Your Full Name" required>
                <input type="email" name="user_email" placeholder="Your Email Address" required>
                <input type="submit" value="Confirm My Spot">
            </form>
        </div>

        <div class="card">
            <h2>📊 Current Attendee List</h2>
            <table>
                <tr>
                    <th>Event Title</th>
                    <th>Attendee</th>
                    <th>Email Contact</th>
                    <th>Management Action</th>
                </tr>
                {% if registrations %}
                    {% for reg in registrations %}
                    <tr>
                        <td><strong>{{ reg[1] }}</strong></td>
                        <td>{{ reg[2] }}</td>
                        <td>{{ reg[3] }}</td>
                        <td><a class="cancel-btn" href="/cancel/{{ reg[0] }}">❌ Cancel Seat</a></td>
                    </tr>
                    {% endfor %}
                {% else %}
                    <tr>
                        <td colspan="4" style="color: #64748b; text-align: center;">No active user bookings found.</td>
                    </tr>
                {% endif %}
            </table>
        </div>
    </div>
</body>
</html>
"""

# --- BACKEND LOGIC ROUTING ---

@app.route("/")
def dashboard():
    """Collects and lists available events and active user registrations."""
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title, date, location FROM events")
    events = cursor.fetchall()
    
    # Query linking registrations with corresponding event titles
    cursor.execute("""
        SELECT registrations.id, events.title, registrations.user_name, registrations.user_email 
        FROM registrations 
        JOIN events ON registrations.event_id = events.id
    """)
    registrations = cursor.fetchall()
    conn.close()
    
    return render_template_string(HTML_TEMPLATE, events=events, registrations=registrations)

@app.route("/register", methods=["POST"])
def handle_registration():
    """Saves new registrations to the database."""
    event_id = request.form["event_id"]
    user_name = request.form["user_name"]
    user_email = request.form["user_email"]
    
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO registrations (event_id, user_name, user_email) VALUES (?, ?, ?)", 
                   (event_id, user_name, user_email))
    conn.commit()
    conn.close()
    
    return redirect(url_for("dashboard"))

@app.route("/cancel/<int:reg_id>")
def cancel_registration(reg_id):
    """Deletes an active registration slot."""
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM registrations WHERE id = ?", (reg_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5001)