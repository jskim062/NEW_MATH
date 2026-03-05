import sqlite3
import json
import argparse

def view_problem(problem_number=None):
    conn = sqlite3.connect('problems.db')
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
        print(f"--- Problem {p_num} ---")
        print(f"[Layer A]: {a}")
        print(f"[Layer B]: {b}")
        print(f"[Layer C]: {c}")
        print(f"[Trap Data]: {trap}\n")
        
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="View Problem Analysis DB")
    parser.add_argument("-p", "--problem", help="Specific problem number to view", type=str)
    args = parser.parse_args()
    
    view_problem(args.problem)
