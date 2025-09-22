import sqlite3

conn = sqlite3.connect("bank.db")
c = conn.cursor()

# --- Create users table if not exists ---
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    mobile TEXT UNIQUE NOT NULL
)
""")

# --- Ensure balance column exists ---
try:
    c.execute("ALTER TABLE users ADD COLUMN balance REAL DEFAULT 10000")
    print("Added 'balance' column to users table.")
except sqlite3.OperationalError:
    print("'balance' column already exists.")

# --- Create transactions table if not exists ---
c.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT NOT NULL,
    receiver TEXT NOT NULL,
    amount REAL NOT NULL,
    status TEXT NOT NULL
)
""")

# --- Ensure timestamp column exists ---
try:
    c.execute("ALTER TABLE transactions ADD COLUMN timestamp TEXT DEFAULT CURRENT_TIMESTAMP")
    print("Added 'timestamp' column to transactions table.")
except sqlite3.OperationalError:
    print("'timestamp' column already exists.")

conn.commit()
conn.close()
print("Database initialized successfully!")