import sqlite3

conn = sqlite3.connect("bank.db")
c = conn.cursor()

# Add balance column
try:
    c.execute("ALTER TABLE users ADD COLUMN balance REAL DEFAULT 0")
except sqlite3.OperationalError:
    pass

# Add timestamp column
try:
    c.execute("ALTER TABLE transactions ADD COLUMN timestamp TEXT DEFAULT CURRENT_TIMESTAMP")
except sqlite3.OperationalError:
    pass

conn.commit()
conn.close()
print("DB updated: balance and timestamp columns ensured.")