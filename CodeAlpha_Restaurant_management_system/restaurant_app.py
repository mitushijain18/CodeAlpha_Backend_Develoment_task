import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

# --- DATABASE SETUP & AUTO-SEEDING ---
def init_db():
    """Sets up a database tracking menu items, table inventory, and customer orders."""
    conn = sqlite3.connect("restaurant.db")
    cursor = conn.cursor()
    
    # 1. Inventory & Menu Table (Keeps track of food item portions left)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            price REAL NOT NULL,
            stock_left INTEGER NOT NULL
        )
    """)
    
    # 2. Table Placement Status Tracker
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tables (
            table_num INTEGER PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'Available'
        )
    """)
    
    # 3. Live Customer Orders Queue
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_num INTEGER,
            item_name TEXT,
            quantity INTEGER,
            FOREIGN KEY(table_num) REFERENCES tables(table_num)
        )
    """)
    
    # Seed default restaurant inventory if empty
    cursor.execute("SELECT COUNT(*) FROM menu")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO menu (item_name, price, stock_left) VALUES ('Classic Cheeseburger', 12.99, 50)")
        cursor.execute("INSERT INTO menu (item_name, price, stock_left) VALUES ('Crispy Truffle Fries', 5.50, 30)")
        cursor.execute("INSERT INTO menu (item_name, price, stock_left) VALUES ('Iced Caramel Latte', 4.99, 10)")
        
        # Seed 4 dining tables
        for i in range(1, 5):
            cursor.execute("INSERT INTO tables (table_num, status) VALUES (?, 'Available')", (i,))
            
    conn.commit()
    conn.close()

# --- HTML PLATFORM FRONTEND (Fixed Template Syntax) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Restaurant Operations Portal</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #f1f5f9; color: #0f172a; margin: 0; padding: 30px; }
        .container { max-width: 900px; margin: auto; }
        h1, h2 { color: #0f172a; margin-top: 0; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .full-width { grid-column: span 2; }
        .badge { padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
        .badge-low { background: #fee2e2; color: #991b1b; }
        .badge-ok { background: #dcfce7; color: #166534; }
        input, select { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #cbd5e1; border-radius: 4px; box-sizing: border-box; }
        input[type="submit"] { background: #dc2626; color: white; border: none; cursor: pointer; font-weight: bold; }
        input[type="submit"]:hover { background: #b91c1c; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #e2e8f0; }
        th { background: #f8fafc; }
    </style>
</head>
<body>
    <div class="container">
        <h1 style="color: #b91c1c;">🍽️ CodeAlpha Restaurant Management System</h1>
        
        <div class="grid">
            <div class="card">
                <h2>📋 Menu & Live Inventory Stock</h2>
                <table>
                    <tr>
                        <th>Dish / Drink</th>
                        <th>Price</th>
                        <th>Stock Status</th>
                    </tr>
                    {% for item in menu %}
                    <tr>
                        <td><strong>{{ item[1] }}</strong></td>
                        <td>${{ "%.2f"|format(item[2]) }}</td>
                        <td>
                            {{ item[3] }} left 
                            {% if item[3] <= 10 %}
                                <span class="badge badge-low">⚠️ LOW ALERT</span>
                            {% else %}
                                <span class="badge badge-ok">✓ OK</span>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </table>
            </div>

            <div class="card">
                <h2>📥 Place New Table Order</h2>
                <form action="/place_order" method="POST">
                    <label>Select Dining Table:</label>
                    <select name="table_num">
                        {% for table in tables %}
                            <option value="{{ table[0] }}">Table {{ table[0] }} ({{ table[1] }})</option>
                        {% endfor %}
                    </select>
                    
                    <label>Select Item to Order:</label>
                    <select name="item_id">
                        {% for item in menu %}
                            <option value="{{ item[0] }}">{{ item[1] }} - (${{ item[2] }})</option>
                        {% endfor %}
                    </select>
                    
                    <label>Serving Quantity:</label>
                    <input type="number" name="quantity" min="1" value="1" required>
                    <input type="submit" value="Send Order to Kitchen">
                </form>
                {% if error_msg %}
                    <p style="color: #dc2626; font-weight: bold; margin-top: 10px;">❌ {{ error_msg }}</p>
                {% endif %}
            </div>

            <div class="card full-width">
                <h2>🔥 Live Active Orders Queue</h2>
                <table>
                    <tr>
                        <th>Order ID</th>
                        <th>Table Location</th>
                        <th>Ordered Item</th>
                        <th>Quantity Ordered</th>
                    </tr>
                    {% if orders %}
                        {% for order in orders %}
                        <tr>
                            <td>#{{ order[0] }}</td>
                            <td><span style="background: #e0f2fe; padding: 3px 8px; border-radius: 4px;">Table {{ order[1] }}</span></td>
                            <td>{{ order[2] }}</td>
                            <td><strong>x{{ order[3] }}</strong></td>
                        </tr>
                        {% endfor %}
                    {% else %}
                        <tr>
                            <td colspan="4" style="text-align: center; color: #64748b;">No active pending kitchen orders.</td>
                        </tr>
                    {% endif %}
                </table>
            </div>
        </div>
    </div>
</body>
</html>
"""

# --- BACKEND LOGIC ROUTING & INVENTORY SAFETY CHECKS ---

@app.route("/")
def dashboard():
    conn = sqlite3.connect("restaurant.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, item_name, price, stock_left FROM menu")
    menu = cursor.fetchall()
    
    cursor.execute("SELECT table_num, status FROM tables")
    tables = cursor.fetchall()
    
    cursor.execute("SELECT id, table_num, item_name, quantity FROM orders")
    orders = cursor.fetchall()
    
    # Catching inventory rejection errors passed via redirect arguments
    error_msg = request.args.get("error")
    
    conn.close()
    return render_template_string(HTML_TEMPLATE, menu=menu, tables=tables, orders=orders, error_msg=error_msg)

@app.route("/place_order", methods=["POST"])
def place_order():
    table_num = int(request.form["table_num"])
    item_id = int(request.form["item_id"])
    quantity = int(request.form["quantity"])
    
    conn = sqlite3.connect("restaurant.db")
    cursor = conn.cursor()
    
    # Step 1: Check Current Availability/Stock Level
    cursor.execute("SELECT item_name, stock_left FROM menu WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    item_name, current_stock = item[0], item[1]
    
    if current_stock < quantity:
        conn.close()
        return redirect(url_for("dashboard", error=f"Insufficient inventory! Only {current_stock} units of {item_name} remain."))
        
    # Step 2: Deduct quantities from Stock (Auto-Update Inventory Logic)
    new_stock = current_stock - quantity
    cursor.execute("UPDATE menu SET stock_left = ? WHERE id = ?", (new_stock, item_id))
    
    # Step 3: Change Table Status to Occupied
    cursor.execute("UPDATE tables SET status = 'Occupied' WHERE table_num = ?", (table_num,))
    
    # Step 4: Queue order record to Kitchen list
    cursor.execute("INSERT INTO orders (table_num, item_name, quantity) VALUES (?, ?, ?)", 
                   (table_num, item_name, quantity))
    
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5002)