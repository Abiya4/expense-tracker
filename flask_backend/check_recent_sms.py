import mysql.connector
from datetime import datetime, timedelta

# Database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="expense_tracker"
)

cursor = db.cursor(dictionary=True)

# Check recent expenses (last 24 hours)
print("=" * 60)
print("RECENT EXPENSES (Last 24 hours)")
print("=" * 60)

yesterday = datetime.now() - timedelta(days=1)
query = """
    SELECT id, user_id, amount, category, type, merchant, date, time, created_at 
    FROM expenses 
    WHERE created_at >= %s 
    ORDER BY created_at DESC 
    LIMIT 10
"""
cursor.execute(query, (yesterday,))
expenses = cursor.fetchall()

if expenses:
    for exp in expenses:
        print(f"\nID: {exp['id']}")
        print(f"User: {exp['user_id']}")
        print(f"Amount: Rs.{exp['amount']}")
        print(f"Type: {exp['type']}")
        print(f"Category: {exp['category']}")
        print(f"Merchant: {exp['merchant']}")
        print(f"Date: {exp['date']} {exp['time']}")
        print(f"Created: {exp['created_at']}")
        print("-" * 60)
else:
    print("\n❌ NO RECENT EXPENSES FOUND!")
    print("This means the SMS was NOT saved to the database.")

# Check total count
cursor.execute("SELECT COUNT(*) as total FROM expenses")
total = cursor.fetchone()
print(f"\n📊 Total expenses in database: {total['total']}")

cursor.close()
db.close()
