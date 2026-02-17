import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Abiya@2005!",
        database="mini_project_db"
    )
    cursor = conn.cursor()

    # Check columns in expenses table
    cursor.execute("DESCRIBE expenses")
    columns = [row[0] for row in cursor.fetchall()]
    print("Existing columns:", columns)

    if "entry_method" not in columns:
        print("Adding entry_method column...")
        cursor.execute("ALTER TABLE expenses ADD COLUMN entry_method VARCHAR(20) DEFAULT 'manual'")
        conn.commit()
        print("Column added successfully.")
    else:
        print("Column entry_method already exists.")

    cursor.close()
    conn.close()

except mysql.connector.Error as err:
    print(f"Error: {err}")
