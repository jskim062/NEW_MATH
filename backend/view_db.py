import sqlite3
import json
import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DB_FILE = BASE_DIR / "problems.db"

def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode(sys.stdout.encoding or 'cp949', errors='replace').decode(sys.stdout.encoding or 'cp949'))

def view_problem(problem_number=None):
    if not DB_FILE.exists():
        print(f"Error: {DB_FILE} not found.")
        return
        
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    if problem_number:
        cursor.execute("SELECT problem_number, layer_a, layer_b, layer_c, trap_data FROM ProblemAnalysis WHERE problem_number = ?", (str(problem_number),))
        row = cursor.fetchone()
        if not row:
            print(f"Problem {problem_number} not found in database.")
            return
        rows = [row]
    else:
        cursor.execute("SELECT problem_number, layer_a, layer_b, layer_c, trap_data FROM ProblemAnalysis ORDER BY CAST(problem_number AS INTEGER)")
        rows = cursor.fetchall()

    for row in rows:
        p_num, a, b, c, trap = row
        safe_print(f"--- Problem {p_num} ---")
        safe_print(f"[Layer A]: {a}")
        safe_print(f"[Layer B]: {b}")
        safe_print(f"[Layer C]: {c}")
        safe_print(f"[Trap Data]: {trap}\n")
        
    conn.close()

def view_generated_problems():
    import os
    from pathlib import Path
    BASE_DIR = Path(__file__).parent.parent
    GEN_DB_FILE = BASE_DIR / "generated_problems.db"
    
    if not GEN_DB_FILE.exists():
        print(f"Error: {GEN_DB_FILE.name} not found.")
        return

    conn = sqlite3.connect(str(GEN_DB_FILE))
    cursor = conn.cursor()
    cursor.execute("SELECT id, difficulty, content, answer, created_at FROM GeneratedProblems ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("No generated problems found in database.")
        return

    for row in rows:
        pid, diff, content, answer, created_at = row
        print(f"--- Generated Problem ID: {pid} ({diff}) ---")
        print(f"[Created At]: {created_at}")
        print(f"[Problem]:\n{content}\n")
        print(f"[Answer]: {answer}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="View Problem Analysis DB")
    parser.add_argument("-p", "--problem", help="Specific problem number to view", type=str)
    parser.add_argument("-g", "--generated", help="View generated problems from generated_problems.db", action="store_true")
    args = parser.parse_args()
    
    if args.generated:
        view_generated_problems()
    else:
        view_problem(args.problem)
