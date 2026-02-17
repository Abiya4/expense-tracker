import mysql.connector

db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Abiya@2005!",
    "database": "mini_project_db"
}

try:
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor()
    
    print("=" * 60)
    print("DATABASE SCHEMA VERIFICATION")
    print("=" * 60)
    
    print("\n--- EXPENSES TABLE COLUMNS ---")
    cur.execute("SHOW COLUMNS FROM expenses")
    for row in cur.fetchall():
        print(f"  ✓ {row[0]:15} | {row[1]:20} | Default: {row[4]}")
    
    print("\n--- USERS TABLE COLUMNS ---")
    cur.execute("SHOW COLUMNS FROM users")
    for row in cur.fetchall():
        print(f"  ✓ {row[0]:15} | {row[1]:20} | Default: {row[4]}")
    
    print("\n--- BUDGETS TABLE COLUMNS ---")
    try:
        cur.execute("SHOW COLUMNS FROM budgets")
        for row in cur.fetchall():
            print(f"  ✓ {row[0]:15} | {row[1]:20} | Default: {row[4]}")
    except Exception as e:
        print(f"  ✗ Budgets table not found: {e}")
    
    print("\n--- ALL TABLES IN DATABASE ---")
    cur.execute("SHOW TABLES")
    tables = [row[0] for row in cur.fetchall()]
    for table in tables:
        print(f"  ✓ {table}")
    
    print("\n--- SAMPLE DATA FROM EXPENSES ---")
    cur.execute("SELECT id, amount, category, merchant, entry_method, status FROM expenses ORDER BY id DESC LIMIT 3")
    rows = cur.fetchall()
    if rows:
        for row in rows:
            print(f"  ID: {row[0]} | Amount: {row[1]} | Category: {row[2]} | Merchant: {row[3]} | Method: {row[4]} | Status: {row[5]}")
    else:
        print("  (No expenses found)")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✓ VERIFICATION COMPLETE")
    print("=" * 60)

except Exception as e:
    print(f"Database Error: {e}")
