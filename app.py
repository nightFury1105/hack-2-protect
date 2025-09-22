from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3, random, pickle, numpy as np
from twilio.rest import Client

app = Flask(__name__)
app.secret_key = "mysecretkey"

# --- Twilio Setup ---
TWILIO_SID = "ACc252ecb77018022123486c8ad1ae1faf"
TWILIO_AUTH = "89ba8265bab86260ec5e4fa488936f13"
TWILIO_PHONE = "+15392659530"
client = Client(TWILIO_SID, TWILIO_AUTH)

# --- Load ML Model ---
with open("fraud_model.pkl", "rb") as f:
    fraud_model = pickle.load(f)

# --- Initialize DB ---
def init_db():
    conn = sqlite3.connect("bank.db")
    c = conn.cursor()

    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            mobile TEXT UNIQUE NOT NULL,
            balance REAL DEFAULT 10000
        )
    """)

    # Transactions table
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL,
            timestamp TEXT
        )
    """)

    # Fill timestamp for any NULL
    c.execute("UPDATE transactions SET timestamp = datetime('now') WHERE timestamp IS NULL")

    conn.commit()
    conn.close()

init_db()

# --- Register ---
@app.route("/register", methods=["GET", "POST"])
def register():
    msg = ""
    if request.method == "POST":
        name = request.form["name"]
        mobile = request.form["mobile"]

        conn = sqlite3.connect("bank.db")
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (name, mobile, balance) VALUES (?, ?, ?)", (name, mobile, 10000))
            conn.commit()
            msg = "✅ Registered successfully! Please login."
        except:
            msg = "❌ Mobile number already registered!"
        conn.close()
    return render_template("register.html", msg=msg)

# --- Login with OTP ---
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        mobile = request.form["mobile"]
        conn = sqlite3.connect("bank.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE mobile=?", (mobile,))
        user = c.fetchone()
        conn.close()

        if not user:
            error = "❌ Number not registered!"
            return render_template("login.html", error=error)

        otp = str(random.randint(1000, 9999))
        session["otp"] = otp
        session["mobile"] = mobile

        try:
            client.messages.create(body=f"Your OTP is {otp}", from_=TWILIO_PHONE, to=mobile)
        except Exception as e:
            error = f"Error sending SMS: {str(e)}"
            return render_template("login.html", error=error)

        return render_template("login.html", otp_sent=True, mobile=mobile)
    return render_template("login.html", error=error)

@app.route("/verify", methods=["POST"])
def verify():
    entered_otp = request.form["otp"]
    if entered_otp == session.get("otp"):
        session["user"] = session["mobile"]
        return redirect(url_for("home"))
    return render_template("login.html", error="❌ Invalid OTP!", otp_sent=True, mobile=session.get("mobile"))

# --- Home ---
@app.route("/home")
def home():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("bank.db")
    c = conn.cursor()
    c.execute("SELECT name, mobile, balance FROM users WHERE mobile=?", (session["user"],))
    user = c.fetchone()
    conn.close()

    return render_template("home.html", user=user)

# --- Profile ---
@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("bank.db")
    c = conn.cursor()
    c.execute("SELECT name, mobile, balance FROM users WHERE mobile=?", (session["user"],))
    user = c.fetchone()
    conn.close()

    return render_template("profile.html", user=user)

# --- Transfer ---
@app.route("/transfer", methods=["GET", "POST"])
def transfer():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("bank.db")
    c = conn.cursor()
    c.execute("SELECT name, balance FROM users WHERE mobile=?", (session["user"],))
    user = c.fetchone()
    conn.close()

    msg = error = ""
    if request.method == "POST":
        receiver = request.form["receiver"]
        amount = float(request.form["amount"])
        sender = session["user"]

        conn = sqlite3.connect("bank.db")
        c = conn.cursor()
        c.execute("SELECT name, balance FROM users WHERE mobile=?", (receiver,))
        rec_user = c.fetchone()

        if not rec_user:
            conn.close()
            error = "❌ Receiver not found!"
            return render_template("transfer.html", user=user, msg=msg, error=error)

        if amount > user[1]:
            conn.close()
            error = "❌ Insufficient balance!"
            return render_template("transfer.html", user=user, msg=msg, error=error)

        # Fraud prediction
        features = np.array([[amount]])
        prediction = fraud_model.predict(features)[0]
        status = "fraud" if prediction == 1 else "success"

        if status == "success":
            new_sender_balance = user[1] - amount
            new_receiver_balance = rec_user[1] + amount
            c.execute("UPDATE users SET balance=? WHERE mobile=?", (new_sender_balance, sender))
            c.execute("UPDATE users SET balance=? WHERE mobile=?", (new_receiver_balance, receiver))

        # Insert transaction with timestamp
        c.execute("INSERT INTO transactions (sender, receiver, amount, status, timestamp) VALUES (?, ?, ?, ?, datetime('now'))",
                  (sender, receiver, amount, status))
        conn.commit()
        conn.close()

        msg = f"✅ ₹{amount} transferred to {receiver} ({status.upper()})"
        user = (user[0], user[1] - amount)

    return render_template("transfer.html", user=user, msg=msg, error=error)

# --- Deposit ---
@app.route("/deposit", methods=["GET", "POST"])
def deposit():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("bank.db")
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE mobile=?", (session["user"],))
    row = c.fetchone()
    balance = row[0] if row else 0

    msg = ""
    if request.method == "POST":
        amount = float(request.form["amount"])
        new_balance = balance + amount
        c.execute("UPDATE users SET balance=? WHERE mobile=?", (new_balance, session["user"]))
        c.execute("INSERT INTO transactions (sender, receiver, amount, status, timestamp) VALUES (?, ?, ?, ?, datetime('now'))",
                  (session["user"], session["user"], amount, "deposit"))
        conn.commit()
        balance = new_balance
        msg = f"✅ ₹{amount} deposited successfully!"
    conn.close()

    return render_template("deposit.html", balance=balance, msg=msg)

# --- Transactions ---
@app.route("/transactions")
def transactions():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("bank.db")
    c = conn.cursor()
    c.execute("""SELECT sender, receiver, amount, status, timestamp 
                 FROM transactions WHERE sender=? OR receiver=? ORDER BY id DESC""",
              (session["user"], session["user"]))
    txns = c.fetchall()
    conn.close()

    return render_template("transactions.html", txns=txns)

# --- Logout ---
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# --- AJAX: Get receiver name ---
@app.route("/get_receiver_name")
def get_receiver_name():
    mobile = request.args.get("mobile")
    conn = sqlite3.connect("bank.db")
    c = conn.cursor()
    c.execute("SELECT name FROM users WHERE mobile=?", (mobile,))
    row = c.fetchone()
    conn.close()
    return jsonify({"name": row[0] if row else ""})

# --- AJAX: Get sender balance ---
@app.route("/get_balance")
def get_balance():
    mobile = session.get("user")
    conn = sqlite3.connect("bank.db")
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE mobile=?", (mobile,))
    row = c.fetchone()
    conn.close()
    return jsonify({"balance": row[0] if row else 0})

if __name__ == "__main__":
    app.run(debug=True)