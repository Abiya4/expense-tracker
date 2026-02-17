import mysql.connector
import json

db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Abiya@2005!",
    "database": "mini_project_db"
}

try:
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor()
    
    print("--- CHECKING COLUMNS ---")
    cur.execute("SHOW COLUMNS FROM expenses")
    columns = [row[0] for row in cur.fetchall()]
    print(f"Columns: {columns}")
    
    if 'status' not in columns:
        print("ERROR: 'status' column MISSING!")
    else:
        print("SUCCESS: 'status' column exists.")

    print("\n--- CHECKING RECENT EXPENSES ---")
    cur.execute("SELECT id, amount, category, status FROM expenses ORDER BY id DESC LIMIT 5")
    for row in cur.fetchall():
        print(row)

    cur.close()
    conn.close()

except Exception as e:
    print(f"Database Error: {e}")
