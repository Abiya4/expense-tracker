from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ---------------- DATABASE CONNECTION ----------------
mysql_conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Abiya@2005!",
    database="mini_project_db"
)

# ---------------- GLOBAL LOGIN STATE ----------------
logged_in_user = {
    "id": None,
    "role": None
}

def is_empty(value):
    return value is None or str(value).strip() == ""

# ---------------- AUTH MODULE ----------------

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username, password, phone, balance = data.get('username'), data.get('password'), data.get('phone'), data.get('balance')
    if is_empty(username) or is_empty(password) or is_empty(phone) or balance is None:
        return jsonify({"success": False, "message": "All fields required"}), 400
    cur = mysql_conn.cursor(buffered=True)
    cur.execute("SELECT id FROM users WHERE username=%s", (username,))
    if cur.fetchone():
        cur.close()
        return jsonify({"success": False, "message": "Username exists"}), 409
    cur.execute("INSERT INTO users(username, password, phone, balance, role) VALUES (%s, %s, %s, %s, 'user')",
                (username, password, phone, balance))
    mysql_conn.commit()
    cur.close()
    return jsonify({"success": True}), 201

@app.route('/login', methods=['POST'])
def login():
    global logged_in_user
    data = request.json
    username, password = data.get('username'), data.get('password')
    cur = mysql_conn.cursor(buffered=True)
    cur.execute("SELECT id, balance, role, is_active FROM users WHERE username=%s AND password=%s", (username, password))
    user = cur.fetchone()
    cur.close()
    if not user:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401
    if not user[3]:
        return jsonify({"success": False, "message": "Account deactivated"}), 403
    logged_in_user["id"], logged_in_user["role"] = user[0], user[2]
    return jsonify({"success": True, "role": user[2], "balance": float(user[1]) if user[2] == 'user' else None})

@app.route('/logout', methods=['POST'])
def logout():
    logged_in_user["id"], logged_in_user["role"] = None, None
    return jsonify({"success": True})

@app.route('/balance', methods=['GET'])
def get_balance():
    if logged_in_user["id"] is None or logged_in_user["role"] != 'user':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    cur = mysql_conn.cursor(buffered=True)
    cur.execute("SELECT balance FROM users WHERE id=%s", (logged_in_user["id"],))
    result = cur.fetchone()
    cur.close()
    if result:
        return jsonify({"balance": float(result[0])})
    return jsonify({"success": False, "message": "User not found"}), 404

# ================= USER MODULE (VIEW, ADD, EDIT, DELETE) =================

@app.route('/expenses', methods=['GET'])
def get_expenses():
    if logged_in_user["role"] != 'user': 
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    cur = mysql_conn.cursor(buffered=True)
    cur.execute("SELECT id, amount, date, time, category, type FROM expenses WHERE user_id=%s ORDER BY date DESC, time DESC", 
                (logged_in_user["id"],))
    rows = cur.fetchall()
    cur.close()
    return jsonify([{
        "id": r[0],
        "amount": float(r[1]),
        "date": str(r[2]),
        "time": str(r[3]),
        "category": r[4],
        "type": r[5]
    } for r in rows])

@app.route('/expenses', methods=['POST'])
def add_expense():
    if logged_in_user["role"] != 'user': 
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    data = request.json
    amount = data.get('amount')
    category = data.get('category')
    t_type = data.get('type', 'expense')
    
    if amount is None or amount <= 0: 
        return jsonify({"success": False, "message": "Invalid amount"}), 400
    
    now = datetime.now()
    cur = mysql_conn.cursor(buffered=True)
    
    cur.execute(
        "INSERT INTO expenses(amount, date, time, category, user_id, type) VALUES (%s, %s, %s, %s, %s, %s)",
        (amount, now.date(), now.time(), category, logged_in_user["id"], t_type)
    )
    
    # Adjust balance: income adds, expense subtracts
    adj = amount if t_type == 'income' else -amount
    cur.execute("UPDATE users SET balance = balance + %s WHERE id=%s", (adj, logged_in_user["id"]))
    
    mysql_conn.commit()
    cur.close()
    return jsonify({"success": True}), 201

@app.route('/expenses/<int:expense_id>', methods=['PUT'])
def edit_expense(expense_id):
    if logged_in_user["role"] != 'user': 
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    data = request.json
    cur = mysql_conn.cursor(buffered=True)
    
    cur.execute("SELECT amount, type, category FROM expenses WHERE id=%s AND user_id=%s", 
                (expense_id, logged_in_user["id"]))
    row = cur.fetchone()
    
    if not row: 
        cur.close()
        return jsonify({"success": False, "message": "Not found"}), 404
    
    old_amt, old_type, old_category = float(row[0]), row[1], row[2]
    new_amt = float(data.get('amount', old_amt))
    new_type = data.get('type', old_type)
    new_category = data.get('category', old_category)

    # Reverse old transaction effect
    undo = -old_amt if old_type == 'income' else old_amt
    # Apply new transaction effect
    apply = new_amt if new_type == 'income' else -new_amt
    
    cur.execute("UPDATE users SET balance = balance + %s + %s WHERE id=%s", 
                (undo, apply, logged_in_user["id"]))
    cur.execute("UPDATE expenses SET amount=%s, category=%s, type=%s WHERE id=%s", 
                (new_amt, new_category, new_type, expense_id))
    
    mysql_conn.commit()
    cur.close()
    return jsonify({"success": True})

@app.route('/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    if logged_in_user["role"] != 'user': 
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    cur = mysql_conn.cursor(buffered=True)
    cur.execute("SELECT amount, type FROM expenses WHERE id=%s AND user_id=%s", 
                (expense_id, logged_in_user["id"]))
    row = cur.fetchone()
    
    if not row: 
        cur.close()
        return jsonify({"success": False, "message": "Not found"}), 404
    
    # Reverse the transaction: income gets subtracted, expense gets added back
    reversal = -row[0] if row[1] == 'income' else row[0]
    
    cur.execute("DELETE FROM expenses WHERE id=%s", (expense_id,))
    cur.execute("UPDATE users SET balance = balance + %s WHERE id=%s", 
                (reversal, logged_in_user["id"]))
    
    mysql_conn.commit()
    cur.close()
    return jsonify({"success": True})

# ================= ADMIN MODULE (SEARCH, ANALYTICS, REMOVE) =================

@app.route('/admin/users', methods=['GET'])
def admin_users():
    if logged_in_user["role"] != 'admin': 
        return jsonify({"success": False, "message": "Admin only"}), 403
    
    # Get search query parameter
    q = request.args.get('q', '').strip()
    
    cur = mysql_conn.cursor(buffered=True)
    
    if q:
        # Search by username or phone
        cur.execute(
            "SELECT id, username, phone, balance, is_active FROM users WHERE role='user' AND (username LIKE %s OR phone LIKE %s)",
            (f"%{q}%", f"%{q}%")
        )
    else:
        # Get all users
        cur.execute("SELECT id, username, phone, balance, is_active FROM users WHERE role='user'")
    
    rows = cur.fetchall()
    cur.close()
    
    return jsonify([{
        "id": r[0],
        "username": r[1],
        "phone": r[2],
        "balance": float(r[3]),
        "active": bool(r[4])
    } for r in rows])

@app.route('/admin/users/<int:user_id>', methods=['DELETE'])
def admin_delete_user(user_id):
    if logged_in_user["role"] != 'admin': 
        return jsonify({"success": False, "message": "Admin only"}), 403
    
    cur = mysql_conn.cursor(buffered=True)
    
    # Check if user exists and is not an admin
    cur.execute("SELECT role FROM users WHERE id=%s", (user_id,))
    user = cur.fetchone()
    
    if not user:
        cur.close()
        return jsonify({"success": False, "message": "User not found"}), 404
    
    if user[0] == 'admin':
        cur.close()
        return jsonify({"success": False, "message": "Cannot delete admin"}), 403
    
    # Delete user (CASCADE will delete all expenses)
    cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
    mysql_conn.commit()
    cur.close()
    
    return jsonify({"success": True, "message": "User removed successfully"})

@app.route('/admin/expenses', methods=['GET'])
def admin_expenses():
    if logged_in_user["role"] != 'admin': 
        return jsonify({"success": False, "message": "Admin only"}), 403
    
    cur = mysql_conn.cursor(buffered=True)
    cur.execute("""
        SELECT u.username, e.amount, e.category, e.date, e.type
        FROM expenses e
        JOIN users u ON e.user_id = u.id
        ORDER BY e.date DESC, e.time DESC
    """)
    rows = cur.fetchall()
    cur.close()
    
    return jsonify([{
        "username": r[0],
        "amount": float(r[1]),
        "category": r[2],
        "date": str(r[3]),
        "type": r[4]
    } for r in rows])

@app.route('/admin/analytics', methods=['GET'])
def admin_analytics():
    if logged_in_user["role"] != 'admin': 
        return jsonify({"success": False, "message": "Admin only"}), 403
    
    cur = mysql_conn.cursor(buffered=True)
    
    # Total users
    cur.execute("SELECT COUNT(*) FROM users WHERE role='user'")
    u_count = cur.fetchone()[0]
    
    # Total expenses (only expense type)
    cur.execute("SELECT IFNULL(SUM(amount), 0) FROM expenses WHERE type='expense'")
    e_sum = cur.fetchone()[0]
    
    cur.close()
    
    return jsonify({
        "total_users": u_count,
        "total_expenses": float(e_sum)
    })

# ---------------- RUN SERVER ----------------
if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5000,debug=True)