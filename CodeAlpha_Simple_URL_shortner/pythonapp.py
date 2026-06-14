import string
import random
import sqlite3
from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)

# --- DATABASE SETUP ---
def init_db():
    """Creates a local database file to store the URL mappings."""
    conn = sqlite3.connect("urls.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS url_map (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            long_url TEXT NOT NULL,
            short_code TEXT NOT NULL UNIQUE
        )
    """)
    conn.commit()
    conn.close()

def generate_short_code():
    """Generates a random 6-character short code (e.g., aBcd12)."""
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(6))

# --- HTML FRONTEND LAYOUT ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CodeAlpha URL Shortener</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; text-align: center; padding: 50px; }
        .container { max-width: 500px; background: white; padding: 30px; margin: auto; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        input[type="text"] { width: 80%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; }
        input[type="submit"] { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
        .result { margin-top: 20px; padding: 15px; background: #d4edda; color: #155724; border-radius: 4px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🔗 CodeAlpha URL Shortener</h2>
        <form method="POST">
            <input type="text" name="long_url" placeholder="Paste your long URL here..." required>
            <br>
            <input type="submit" value="Shorten URL">
        </form>
        {% if short_url %}
            <div class="result">
                Short URL: <a href="{{ short_url }}" target="_blank">{{ short_url }}</a>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

# --- ROUTES / API ENDPOINTS ---
@app.route("/", methods=["GET", "POST"])
def home():
    short_url = None
    if request.method == "POST":
        long_url = request.form["long_url"]
        short_code = generate_short_code()

        # Save connection to local SQLite DB
        conn = sqlite3.connect("urls.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO url_map (long_url, short_code) VALUES (?, ?)", (long_url, short_code))
        conn.commit()
        conn.close()

        # Generate the clickable short URL address
        short_url = request.host_url + short_code

    return render_template_string(HTML_TEMPLATE, short_url=short_url)

@app.route("/<short_code>")
def redirect_to_long(short_code):
    """Looks up the short code in the database and redirects the browser."""
    conn = sqlite3.connect("urls.db")
    cursor = conn.cursor()
    cursor.execute("SELECT long_url FROM url_map WHERE short_code = ?", (short_code,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return redirect(row[0]) # Redirect to the original URL
    return "<h3>Error: Short URL not found!</h3>", 404

if __name__ == "__main__":
    init_db() # Run database verification setup on start
    app.run(debug=True)