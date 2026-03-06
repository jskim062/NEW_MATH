import sqlite3
import sys

def check_db(path):
    print(f"Checking {path}")
    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cur.fetchall()
        print("Tables:", tables)
        conn.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    check_db("problems.db")
    check_db("backend/problems.db")
