import os
import sqlite3
import re
import json
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Setup Directories
SOLUTIONS_DIR = Path("solutions")
DB_FILE = "problems.db"

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in environment variables.")
    exit(1)

client = genai.Client(api_key=api_key)
# Using flash or pro for analysis. Pro is better for complex reasoning.
MODEL_ID = "gemini-3-pro-preview" 

SYSTEM_PROMPT = """[System Role]
너는 대한민국 수능(K-SAT) 수학 영역 출제 본부의 '수석 문항 설계 위원'이자 평가 공학자이다.
제공된 단일 문항의 해설 데이터를 분석하여 수학적 로직을 층위별로 추출하라.

[Phase 1: 층위별 로직 데이터베이스화 (Multi-Layer Logic Extraction)]
제공된 해설지를 전수 분석하여 다음 3개의 레이어(Layer)와 메타 데이터로 분해하라.

* Layer_A (함수/상황의 구조): 문항의 뼈대가 되는 함수 개형이나 조건 기법 (예: 정적분으로 정의된 함수, 원에 내접하는 사각형).
* Layer_B (핵심 도구 및 테크닉): 문제 해결에 쓰인 결정적 수학 도구 (예: 부분적분, 절대부등식의 압착, 역 곱의 미분법).
* Layer_C (추론의 전개 방식): 정답으로 향하는 논리적 연결 고리와 'The Click(번뜩이는 통찰)' 포인트 (예: 케이스 분류, 대칭성 발견).
* Trap_Data: 해설지의 'Post-Solution Reflection'을 분석하여 수험생이 빠지기 쉬운 논리적 함정 패턴.

출력은 반드시 유효한 JSON 형식이어야 하며, 다음과 같은 키를 포함해야 한다:
{
  "Layer_A": "...",
  "Layer_B": "...",
  "Layer_C": "...",
  "Trap_Data": "..."
}
"""

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ProblemAnalysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_file TEXT,
            problem_number TEXT,
            original_content TEXT,
            layer_a TEXT,
            layer_b TEXT,
            layer_c TEXT,
            trap_data TEXT,
            UNIQUE(source_file, problem_number)
        )
    ''')
    conn.commit()
    return conn

def extract_problems_from_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by "## Problem "
    problems = []
    parts = re.split(r'^## Problem\s+', content, flags=re.MULTILINE)[1:] # Skip the first part before any problem
    
    seen_numbers = {}
    
    for part in parts:
        lines = part.split('\n', 1)
        if len(lines) >= 2:
            base_problem_number = lines[0].strip()
            problem_content = lines[1].strip()
            
            if base_problem_number in seen_numbers:
                seen_numbers[base_problem_number] += 1
                problem_number = f"{base_problem_number}_{seen_numbers[base_problem_number]}"
            else:
                seen_numbers[base_problem_number] = 0
                problem_number = base_problem_number
                
            problems.append((problem_number, problem_content))
            
    return problems

def analyze_problem(content):
    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[
                SYSTEM_PROMPT,
                "다음은 분석할 기출 문항의 해설 데이터입니다:\n\n" + content
            ],
            config=types.GenerateContentConfig(
                temperature=0.2, # Lower temperature for stable JSON output
                response_mime_type="application/json",
            )
        )
        result_text = response.text
        return json.loads(result_text)
    except Exception as e:
        print(f"Error during API call or JSON parsing: {e}")
        return None

def main():
    print("Initializing Database...")
    conn = init_db()
    cursor = conn.cursor()

    solution_files = list(SOLUTIONS_DIR.glob("*.md"))
    if not solution_files:
        print("No solution files found.")
        return

    for file in solution_files:
        filename = file.name
        print(f"Processing file: {filename}")
        problems = extract_problems_from_file(file)
        
        for p_num, p_content in problems:
            # Check if already processed
            cursor.execute("SELECT id FROM ProblemAnalysis WHERE source_file = ? AND problem_number = ?", (filename, p_num))
            if cursor.fetchone():
                print(f"  Problem {p_num} already in DB. Skipping.")
                continue
                
            print(f"  Analyzing Problem {p_num}...")
            analysis_result = analyze_problem(p_content)
            
            if analysis_result:
                if isinstance(analysis_result, list) and len(analysis_result) > 0:
                    analysis_result = analysis_result[0]
                if isinstance(analysis_result, dict):
                    try:
                        cursor.execute('''
                            INSERT INTO ProblemAnalysis 
                            (source_file, problem_number, original_content, layer_a, layer_b, layer_c, trap_data)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            filename,
                            p_num,
                            p_content,
                            analysis_result.get('Layer_A', ''),
                            analysis_result.get('Layer_B', ''),
                            analysis_result.get('Layer_C', ''),
                            analysis_result.get('Trap_Data', '')
                        ))
                        conn.commit()
                        print(f"  -> Saved Problem {p_num} to DB.")
                    except sqlite3.IntegrityError:
                        print(f"  -> Problem {p_num} already exists (concurrent run?).")
                else:
                    print(f"  -> Problem {p_num} returned invalid JSON structure.")
            else:
                print(f"  -> Failed to analyze Problem {p_num}.")

    conn.close()
    print("Database build complete.")

if __name__ == "__main__":
    main()
