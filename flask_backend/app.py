from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ---------------- DATABASE CONNECTION ----------------
# ---------------- DATABASE CONNECTION ----------------
mysql_conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Abiya@2005!",
    database="mini_project_db"
)

# ---------------- MIGRATION ----------------
def run_migrations():
    print("Checking for database migrations...")
    cur = mysql_conn.cursor(buffered=True)
    try:
        # Check if 'status' column exists in 'expenses'
        cur.execute("SHOW COLUMNS FROM expenses LIKE 'status'")
        result = cur.fetchone()
        if not result:
            print("Adding 'status' column to expenses table...")
            cur.execute("ALTER TABLE expenses ADD COLUMN status VARCHAR(20) DEFAULT 'confirmed'")
            mysql_conn.commit()
            print("Migration successful: 'status' column added.")
        else:
            print("Migration check: 'status' column already exists.")
            
        # Check if 'entry_method' column exists
        cur.execute("SHOW COLUMNS FROM expenses LIKE 'entry_method'")
        result = cur.fetchone()
        if not result:
            print("Adding 'entry_method' column to expenses table...")
            cur.execute("ALTER TABLE expenses ADD COLUMN entry_method VARCHAR(20) DEFAULT 'manual'")
            mysql_conn.commit()
            print("Migration successful: 'entry_method' column added.")
        
        # Check if 'merchant' column exists (from friend's schema) - REMOVE IF NOT NEEDED
        # cur.execute("SHOW COLUMNS FROM expenses LIKE 'merchant'")
        # result = cur.fetchone()
        # if not result:
        #     print("Adding 'merchant' column to expenses table...")
        #     cur.execute("ALTER TABLE expenses ADD COLUMN merchant VARCHAR(100) DEFAULT 'Unknown'")
        #     mysql_conn.commit()
        #     print("Migration successful: 'merchant' column added.")
        # else:
        #     print("Migration check: 'merchant' column already exists.")
        
        # Create budgets table if it doesn't exist (from friend's schema)
        cur.execute("SHOW TABLES LIKE 'budgets'")
        result = cur.fetchone()
        if not result:
            print("Creating 'budgets' table...")
            cur.execute("""
                CREATE TABLE budgets (
                    user_id INT PRIMARY KEY,
                    monthly_limit DECIMAL(10,2) NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            mysql_conn.commit()
            print("Migration successful: 'budgets' table created.")
        else:
            print("Migration check: 'budgets' table already exists.")
            
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        cur.close()

# Run migrations on startup
run_migrations()

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
    return jsonify({"success": True, "id": user[0], "role": user[2], "balance": float(user[1]) if user[2] == 'user' else None})

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
    
    # Optional filtering by status
    status_filter = request.args.get('status') # 'pending' or 'confirmed'
    
    cur = mysql_conn.cursor(buffered=True)
    
    if status_filter:
        query = "SELECT id, amount, date, time, category, type, status, entry_method FROM expenses WHERE user_id=%s AND status=%s ORDER BY date DESC, time DESC"
        params = (logged_in_user["id"], status_filter)
    else:
        # Default behavior: Show all (or client can filter) - let's return all and let client decide, 
        # but traditionally 'status' might be useful context.
        query = "SELECT id, amount, date, time, category, type, status, entry_method FROM expenses WHERE user_id=%s ORDER BY date DESC, time DESC"
        params = (logged_in_user["id"],)
        
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    return jsonify([{
        "id": r[0],
        "amount": float(r[1]),
        "date": str(r[2]),
        "time": str(r[3]),
        "category": r[4],
        "type": r[5],
        "status": r[6],
        "entry_method": r[7]
    } for r in rows])

@app.route('/expenses', methods=['POST'])
def add_expense():
    if logged_in_user["role"] != 'user': 
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    data = request.json
    amount = data.get('amount')
    category = data.get('category')
    t_type = data.get('type', 'expense')
    status = data.get('status', 'confirmed') # Default to confirmed
    entry_method = data.get('entry_method', 'manual')
    # merchant = data.get('merchant', 'Unknown')  # REMOVED
    
    # Optional fields for manual/synced entry
    date_val = data.get('date') # Expecting YYYY-MM-DD
    time_val = data.get('time') # Expecting HH:MM:SS
    
    if amount is None or amount <= 0: 
        return jsonify({"success": False, "message": "Invalid amount"}), 400
    
    now = datetime.now()
    final_date = date_val if date_val else now.date()
    final_time = time_val if time_val else now.time()
    
    cur = mysql_conn.cursor(buffered=True)
    
    cur.execute(
        "INSERT INTO expenses(amount, date, time, category, user_id, type, status, entry_method) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (amount, final_date, final_time, category, logged_in_user["id"], t_type, status, entry_method)
    )
    
    # Adjust balance ONLY if status is 'confirmed'
    if status == 'confirmed':
        adj = amount if t_type == 'income' else -amount
        cur.execute("UPDATE users SET balance = balance + %s WHERE id=%s", (adj, logged_in_user["id"]))
    
    mysql_conn.commit()
    cur.close()
    return jsonify({"success": True}), 201

@app.route('/expenses/server_sync', methods=['POST'])
def sync_pending_expenses():
    """
    Endpoint to receive a batch of pending expenses from the client (e.g., from SMS Sync).
    Avoids duplicates based on amount, date, and time? Or just inserts them as pending.
    """
    if logged_in_user["role"] != 'user':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
        
    data = request.json
    expenses_list = data.get('expenses', [])
    
    if not expenses_list:
        return jsonify({"success": True, "message": "No expenses to sync"}), 200
        
    cur = mysql_conn.cursor(buffered=True)
    count = 0
    
    for item in expenses_list:
        try:
            amount = item.get('amount')
            date_str = item.get('date')
            time_str = item.get('time', '00:00:00')
            category = item.get('category', 'Uncategorized') # Usually 'Uncategorized' for SMS
            t_type = item.get('type', 'expense')
            # merchant = item.get('merchant', 'Unknown')  # REMOVED
            
            # Simple duplicate check: if an identical pending expense exists for this user on this date/amount
            # This is heuristic, but prevents spamming refresh from adding duplicates
            cur.execute("""
                SELECT id FROM expenses 
                WHERE user_id=%s AND amount=%s AND date=%s AND type=%s AND status='pending'
            """, (logged_in_user["id"], amount, date_str, t_type))
            
            if cur.fetchone():
                print(f"Skipping duplicate pending expense: {amount} on {date_str}")
                continue

            cur.execute(
                "INSERT INTO expenses(amount, date, time, category, user_id, type, status, entry_method) VALUES (%s, %s, %s, %s, %s, %s, 'pending', 'sms')",
                (amount, date_str, time_str, category, logged_in_user["id"], t_type)
            )
            count += 1
        except Exception as e:
            print(f"Error syncing item {item}: {e}")
            
    mysql_conn.commit()
    cur.close()
    return jsonify({"success": True, "synced_count": count}), 201

@app.route('/expenses/confirm_sms', methods=['POST'])
def confirm_sms_expense():
    # ... Keeping for backward compatibility or direct calls if needed ...
    # But now using add_expense or sync_pending_expenses is preferred.
    # Let's redirect logic to add_expense for consistency if called directly.
    return add_expense()

@app.route('/expenses/<int:expense_id>', methods=['PUT'])
def edit_expense(expense_id):
    if logged_in_user["role"] != 'user': 
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    data = request.json
    cur = mysql_conn.cursor(buffered=True)
    
    cur.execute("SELECT amount, type, category, status FROM expenses WHERE id=%s AND user_id=%s", 
                (expense_id, logged_in_user["id"]))
    row = cur.fetchone()
    
    if not row: 
        cur.close()
        return jsonify({"success": False, "message": "Not found"}), 404
    
    old_amt, old_type, old_category, old_status = float(row[0]), row[1], row[2], row[3]
    new_amt = float(data.get('amount', old_amt))
    new_type = data.get('type', old_type)
    new_category = data.get('category', old_category)
    new_status = data.get('status', old_status)

    # Balance Adjustment Logic:
    # 1. If old was confirmed, reverting it:
    if old_status == 'confirmed':
        undo = -old_amt if old_type == 'income' else old_amt
        cur.execute("UPDATE users SET balance = balance + %s WHERE id=%s", (undo, logged_in_user["id"]))
        
    # 2. If new is confirmed, applying it:
    if new_status == 'confirmed':
        apply = new_amt if new_type == 'income' else -new_amt
        cur.execute("UPDATE users SET balance = balance + %s WHERE id=%s", (apply, logged_in_user["id"]))
    
    # Update the record
    cur.execute("UPDATE expenses SET amount=%s, category=%s, type=%s, status=%s WHERE id=%s", 
                (new_amt, new_category, new_type, new_status, expense_id))
    
    mysql_conn.commit()
    cur.close()
    return jsonify({"success": True})

@app.route('/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    if logged_in_user["role"] != 'user': 
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    cur = mysql_conn.cursor(buffered=True)
    cur.execute("SELECT amount, type, status FROM expenses WHERE id=%s AND user_id=%s", 
                (expense_id, logged_in_user["id"]))
    row = cur.fetchone()
    
    if not row: 
        cur.close()
        return jsonify({"success": False, "message": "Not found"}), 404
    
    amount, t_type, status = row[0], row[1], row[2]
    
    # Only reverse balance if it was confirmed
    if status == 'confirmed':
        reversal = -amount if t_type == 'income' else amount
        cur.execute("UPDATE users SET balance = balance + %s WHERE id=%s", 
                    (reversal, logged_in_user["id"]))
    
    cur.execute("DELETE FROM expenses WHERE id=%s", (expense_id,))
    
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
