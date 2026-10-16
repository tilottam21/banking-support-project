
import os
from dotenv import load_dotenv
from flask import Flask, jsonify
import mysql.connector

load_dotenv()

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_NAME", "banking_support")
    )

@app.route("/")
def home():
    return "Banking Support System is Running!"

@app.route("/health")
def health():
    try:
        print("HEALTH ROUTE HIT")
        conn = get_db_connection()
        conn.close()
        return jsonify({
            "application": "UP",
            "database": "CONNECTED"
        })
    except Exception as e:
        print("HEALTH ERROR:", repr(e))
        return jsonify({
            "application": "UP",
            "database": "ERROR",
            "message": str(e)
        }), 500

@app.route("/customers")
def customers():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT customer_id, full_name, email, phone
        FROM customers
    """)

    result = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(result)


@app.route("/failed-transactions")
def failed_transactions():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            t.reference_no,
            c.full_name,
            a.account_number,
            t.amount,
            t.status,
            t.txn_time
        FROM transactions t
        JOIN accounts a
            ON t.account_id = a.account_id
        JOIN customers c
            ON a.customer_id = c.customer_id
        WHERE t.status = 'FAILED'
        ORDER BY t.txn_time DESC
    """)

    result = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(result)

@app.route("/open-tickets")
def open_tickets():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            st.ticket_id,
            c.full_name,
            st.issue_type,
            st.description,
            st.status,
            st.created_at
        FROM support_tickets st
        JOIN customers c
            ON st.customer_id = c.customer_id
        WHERE st.status IN ('OPEN', 'IN_PROGRESS')
        ORDER BY st.created_at DESC
    """)

    result = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(result)


@app.route("/dashboard")
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM customers")
    total_customers = cursor.fetchone()["total"]

    cursor.execute(
        "SELECT COUNT(*) AS total FROM transactions WHERE status = 'FAILED'"
    )
    failed_transactions = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM support_tickets
        WHERE status IN ('OPEN', 'IN_PROGRESS')
    """)
    open_tickets = cursor.fetchone()["total"]

    cursor.close()
    conn.close()

    return f"""
    <html>
    <head>
        <title>Banking Support Dashboard</title>
        <style>
            body {{
                font-family: Arial;
                background: #f2f5f9;
                padding: 40px;
            }}
            h1 {{ color: #17365d; }}
            .card {{
                background: white;
                padding: 24px;
                margin: 15px 0;
                border-radius: 10px;
                box-shadow: 0 2px 8px #ddd;
            }}
            .number {{ font-size: 32px; font-weight: bold; }}
            a {{ margin-right: 20px; }}
        </style>
    </head>
    <body>
        <h1>Banking Support Dashboard</h1>

        <div class="card">
            Total Customers
            <div class="number">{total_customers}</div>
        </div>

        <div class="card">
            Failed Transactions
            <div class="number">{failed_transactions}</div>
        </div>

        <div class="card">
            Unresolved Tickets
            <div class="number">{open_tickets}</div>
        </div>

        <p>
            <a href="/customers">Customers</a>
            <a href="/failed-transactions">Failed Transactions</a>
            <a href="/open-tickets">Support Tickets</a>
        </p>
    </body>
    </html>
    """
@app.route("/resolve-ticket/<int:ticket_id>", methods=["POST"])
def resolve_ticket(ticket_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE support_tickets
        SET status = 'RESOLVED'
        WHERE ticket_id = %s
          AND status != 'RESOLVED'
        """,
        (ticket_id,)
    )

    updated = cursor.rowcount
    conn.commit()

    cursor.close()
    conn.close()

    if updated == 0:
        return jsonify({
            "message": "Ticket not found or already resolved"
        }), 404

    return jsonify({
        "ticket_id": ticket_id,
        "status": "RESOLVED",
        "message": "Ticket resolved successfully"
    })

if __name__ == "__main__":
    app.run(debug=True)