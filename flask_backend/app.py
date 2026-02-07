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

# ---------------- GLOBAL LOGIN STATE (MINI PROJECT) ----------------
logged_in_user = {
    "id": None,
    "role": None
}

# ---------------- HELPER FUNCTION ----------------
def is_empty(value):
    return value is None or str(value).strip() == ""

# ---------------- SIGNUP (USER ONLY) ----------------
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json

    username = data.get('username')
    password = data.get('password')
    phone = data.get('phone')
    balance = data.get('balance')

    if is_empty(username) or is_empty(password) or is_empty(phone) or balance is None:
        return jsonify({"success": False, "message": "All fields are required"}), 400

    if balance < 0:
        return jsonify({"success": False, "message": "Balance cannot be negative"}), 400

    cur = mysql_conn.cursor(buffered=True)

    cur.execute("SELECT id FROM users WHERE username=%s", (username,))
    if cur.fetchone():
        cur.close()
        return jsonify({"success": False, "message": "Username already exists"}), 409

    cur.execute(
        "INSERT INTO users(username, password, phone, balance, role) VALUES (%s, %s, %s, %s, 'user')",
        (username, password, phone, balance)
    )

    mysql_conn.commit()
    cur.close()

    return jsonify({"success": True}), 201

# ---------------- LOGIN (USER + ADMIN) ----------------
@app.route('/login', methods=['POST'])
def login():
    global logged_in_user

    data = request.json
    username = data.get('username')
    password = data.get('password')

    if is_empty(username) or is_empty(password):
        return jsonify({"success": False, "message": "Username and password required"}), 400

    cur = mysql_conn.cursor(buffered=True)
    cur.execute(
        "SELECT id, balance, role, is_active FROM users WHERE username=%s AND password=%s",
        (username, password)
    )
    user = cur.fetchone()
    cur.close()

    if not user:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401

    if not user[3]:
        return jsonify({"success": False, "message": "Account deactivated"}), 403

    logged_in_user["id"] = user[0]
    logged_in_user["role"] = user[2]

    return jsonify({
        "success": True,
        "role": user[2],
        "balance": float(user[1]) if user[2] == 'user' else None
    })

# ---------------- LOGOUT ----------------
@app.route('/logout', methods=['POST'])
def logout():
    logged_in_user["id"] = None
    logged_in_user["role"] = None
    return jsonify({"success": True})

# ---------------- GET BALANCE ----------------
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

# ================= USER MODULE =================

# ---------------- GET USER EXPENSES ----------------
@app.route('/expenses', methods=['GET'])
def get_expenses():
    if logged_in_user["id"] is None or logged_in_user["role"] != 'user':
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    cur = mysql_conn.cursor(buffered=True)
    cur.execute(
        "SELECT id, amount, date, time, category FROM expenses WHERE user_id=%s",
        (logged_in_user["id"],)
    )

    rows = cur.fetchall()
    cur.close()

    expenses = []
    for r in rows:
        expenses.append({
            "id": r[0],
            "amount": float(r[1]),
            "date": str(r[2]),
            "time": str(r[3]),
            "category": r[4]
        })

    return jsonify(expenses)

# ---------------- ADD EXPENSE ----------------
@app.route('/expenses', methods=['POST'])
def add_expense():
    if logged_in_user["id"] is None or logged_in_user["role"] != 'user':
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.json
    amount = data.get('amount')
    category = data.get('category')

    if amount is None or is_empty(category):
        return jsonify({"success": False, "message": "Amount and category required"}), 400

    if amount <= 0:
        return jsonify({"success": False, "message": "Amount must be positive"}), 400

    now = datetime.now()

    cur = mysql_conn.cursor(buffered=True)

    cur.execute(
        "INSERT INTO expenses(amount, date, time, category, user_id) VALUES (%s, %s, %s, %s, %s)",
        (amount, now.date(), now.time(), category, logged_in_user["id"])
    )

    cur.execute(
        "UPDATE users SET balance = balance - %s WHERE id=%s",
        (amount, logged_in_user["id"])
    )

    mysql_conn.commit()
    cur.close()

    return jsonify({"success": True}), 201

# ---------------- EDIT EXPENSE ----------------
@app.route('/expenses/<int:expense_id>', methods=['PUT'])
def edit_expense(expense_id):
    print(f"Edit expense called for ID: {expense_id}")
    print(f"Logged in user: {logged_in_user}")
    
    if logged_in_user["id"] is None or logged_in_user["role"] != 'user':
        print("Unauthorized access attempt")
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.json
    print(f"Received data: {data}")

    cur = mysql_conn.cursor(buffered=True)
    
    try:
        cur.execute(
            "SELECT amount, category FROM expenses WHERE id=%s AND user_id=%s",
            (expense_id, logged_in_user["id"])
        )
        row = cur.fetchone()

        if not row:
            cur.close()
            print(f"Expense {expense_id} not found for user {logged_in_user['id']}")
            return jsonify({"success": False, "message": "Expense not found"}), 404

        old_amount = float(row[0])
        old_category = row[1]
        print(f"Old values - Amount: {old_amount}, Category: {old_category}")
        
        new_amount = float(data.get('amount', old_amount))
        new_category = data.get('category', old_category)
        print(f"New values - Amount: {new_amount}, Category: {new_category}")

        if new_amount <= 0:
            cur.close()
            print("Invalid amount (must be positive)")
            return jsonify({"success": False, "message": "Amount must be positive"}), 400

        diff = new_amount - old_amount
        print(f"Balance difference: {diff}")

        cur.execute(
            "UPDATE expenses SET amount=%s, category=%s WHERE id=%s",
            (new_amount, new_category, expense_id)
        )
        print(f"Updated expense record")
        
        cur.execute(
            "UPDATE users SET balance = balance - %s WHERE id=%s",
            (diff, logged_in_user["id"])
        )
        print(f"Updated user balance")

        mysql_conn.commit()
        cur.close()
        
        print("Update successful")
        return jsonify({"success": True})
        
    except Exception as e:
        mysql_conn.rollback()
        cur.close()
        print(f"Error updating expense: {str(e)}")
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

# ---------------- DELETE EXPENSE ----------------
@app.route('/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    if logged_in_user["id"] is None or logged_in_user["role"] != 'user':
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    cur = mysql_conn.cursor(buffered=True)
    cur.execute(
        "SELECT amount FROM expenses WHERE id=%s AND user_id=%s",
        (expense_id, logged_in_user["id"])
    )
    row = cur.fetchone()

    if not row:
        cur.close()
        return jsonify({"success": False, "message": "Expense not found"}), 404

    amount = row[0]

    cur.execute("DELETE FROM expenses WHERE id=%s", (expense_id,))
    cur.execute(
        "UPDATE users SET balance = balance + %s WHERE id=%s",
        (amount, logged_in_user["id"])
    )

    mysql_conn.commit()
    cur.close()

    return jsonify({"success": True})

# ================= ADMIN MODULE (MINIMUM & PERFECT) =================

# ---------------- VIEW ALL USERS ----------------
@app.route('/admin/users', methods=['GET'])
def admin_users():
    if logged_in_user["role"] != 'admin':
        return jsonify({"success": False, "message": "Admin only"}), 403

    cur = mysql_conn.cursor(buffered=True)
    cur.execute(
        "SELECT id, username, phone, is_active FROM users WHERE role='user'"
    )
    rows = cur.fetchall()
    cur.close()

    users = []
    for r in rows:
        users.append({
            "id": r[0],
            "username": r[1],
            "phone": r[2],
            "active": bool(r[3])
        })

    return jsonify(users)

# ---------------- VIEW ALL TRANSACTIONS ----------------
@app.route('/admin/expenses', methods=['GET'])
def admin_expenses():
    if logged_in_user["role"] != 'admin':
        return jsonify({"success": False, "message": "Admin only"}), 403

    cur = mysql_conn.cursor(buffered=True)
    cur.execute("""
        SELECT u.username, e.amount, e.category, e.date
        FROM expenses e
        JOIN users u ON e.user_id = u.id
    """)
    rows = cur.fetchall()
    cur.close()

    expenses = []
    for r in rows:
        expenses.append({
            "username": r[0],
            "amount": float(r[1]),
            "category": r[2],
            "date": str(r[3])
        })

    return jsonify(expenses)

# ---------------- BASIC ANALYTICS ----------------
@app.route('/admin/analytics', methods=['GET'])
def admin_analytics():
    if logged_in_user["role"] != 'admin':
        return jsonify({"success": False, "message": "Admin only"}), 403

    cur = mysql_conn.cursor(buffered=True)

    cur.execute("SELECT COUNT(*) FROM users WHERE role='user'")
    total_users = cur.fetchone()[0]

    cur.execute("SELECT IFNULL(SUM(amount),0) FROM expenses")
    total_expenses = cur.fetchone()[0]

    cur.close()

    return jsonify({
        "total_users": total_users,
        "total_expenses": float(total_expenses)
    })

# ---------------- RUN SERVER ----------------
if __name__ == '__main__':
    app.run(debug=True)