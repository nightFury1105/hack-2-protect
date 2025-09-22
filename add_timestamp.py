import sqlite3

conn = sqlite3.connect("bank.db")
c = conn.cursor()

# --- Ensure balance column exists in users table ---
c.execute("PRAGMA table_info(users)")
user_cols = [col[1] for col in c.fetchall()]
if "balance" not in user_cols:
    c.execute("ALTER TABLE users ADD COLUMN balance REAL DEFAULT 10000")
    print("Added 'balance' column to users table")
else:
    print("'balance' column already exists")

# --- Ensure timestamp column exists in transactions table ---
c.execute("PRAGMA table_info(transactions)")
txn_cols = [col[1] for col in c.fetchall()]
if "timestamp" not in txn_cols:
    c.execute("ALTER TABLE transactions ADD COLUMN timestamp TEXT")
    # Fill existing rows with current datetime
    c.execute("UPDATE transactions SET timestamp = datetime('now') WHERE timestamp IS NULL")
    print("Added 'timestamp' column to transactions table")
else:
    print("'timestamp' column already exists")

conn.commit()
conn.close()
print("Database is ready!")