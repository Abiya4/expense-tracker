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
    
    print("--- ADDING MERCHANT COLUMN ---")
    try:
        cur.execute("ALTER TABLE expenses ADD COLUMN merchant VARCHAR(100) DEFAULT 'Unknown'")
        conn.commit()
        print("✓ Successfully added 'merchant' column to expenses table")
    except Exception as e:
        if "Duplicate column name" in str(e):
            print("✓ 'merchant' column already exists")
        else:
            print(f"✗ Error adding merchant column: {e}")
    
    print("\n--- CREATING BUDGETS TABLE ---")
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                user_id INT PRIMARY KEY,
                monthly_limit DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
        print("✓ Successfully created 'budgets' table")
    except Exception as e:
        print(f"✗ Error creating budgets table: {e}")
    
    print("\n--- VERIFYING COLUMNS ---")
    cur.execute("SHOW COLUMNS FROM expenses")
    columns = [row[0] for row in cur.fetchall()]
    print(f"Expenses columns: {columns}")
    
    print("\n--- VERIFYING TABLES ---")
    cur.execute("SHOW TABLES")
    tables = [row[0] for row in cur.fetchall()]
    print(f"Database tables: {tables}")
    
    cur.close()
    conn.close()
    print("\n✓ Database migration completed successfully!")

except Exception as e:
    print(f"Database Error: {e}")
