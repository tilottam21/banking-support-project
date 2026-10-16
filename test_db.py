import os
import mysql.connector

try:
    connection = mysql.connector.connect(
    host=os.environ.get("DB_HOST", "localhost"),
    user=os.environ.get("DB_USER", "root"),
    password=os.environ.get("DB_PASSWORD"),
    database=os.environ.get("DB_NAME", "banking_support")
)

    if connection.is_connected():
        print("MySQL Connection: SUCCESS")
        print("Banking Support Database Server: CONNECTED")

    connection.close()

except mysql.connector.Error as error:
    print("MySQL Connection: FAILED")
    print("Error:", error)
