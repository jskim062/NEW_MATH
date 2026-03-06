import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Setup Directories
# Setup Directories - robust paths relative to script
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
DB_FILE = BASE_DIR / "problems.db"
GEN_DB_FILE = BASE_DIR / "generated_problems.db"
OUTPUT_DIR = BASE_DIR / "generated"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    exit(1)

client = genai.Client(api_key=api_key)
MODEL_ID = "gemini-3.1-pro-preview" # Using 3.1 for best reasoning capabilities

SYSTEM_PROMPT = """[System Role]
너는 대한민국 수능(K-SAT) 수학 영역 출제 본부의 '수석 문항 설계 위원'이자 평가 공학자이다. 
제공된 수학적 로직 데이터(Layer A, B, C 및 Trap Data)를 분석하고 융합하여 완전히 새로운 난이도별 문항 세트를 설계하라. 단순한 숫자 변형(Surface Variation)은 엄격히 금지하며, 로직의 전이(Transfer)와 융합(Fusion)만을 수행해야 한다.

아래에 제공되는 데이터는 기존 기출 문제들을 층위별로 분석한 데이터베이스이다.
* Layer A (함수/상황의 구조): 문항의 뼈대가 되는 함수 개형이나 조건 기법.
* Layer B (핵심 도구 및 테크닉): 문제 해결에 쓰인 결정적 수학 도구.
* Layer C (추론의 전개 방식): 정답으로 향하는 논리적 연결 고리와 'The Click(번뜩이는 통찰)' 포인트.
* Trap Data: 수험생이 빠지기 쉬운 논리적 함정 패턴.

---

[Phase 1: 난이도별 융합 및 문항 설계 (Level-based Logic Fusion)]
제공된 데이터의 Layer들을 유기적으로 결합하여 다음 3가지 난이도의 문항을 각각 생성하라.

* [Level 1: 기본 4점]
  * 설계: 단일 문항의 Layer B(핵심 도구)를 유지하되, Layer A(상황)를 다른 단원의 개념으로 완전히 치환하라. (예: 다항함수 문제를 지수/로그함수 상황으로 전이)
  * 함정: 계산 과정에 Trap Data를 활용한 매력적인 오답 루트를 하나 설계하라.
* [Level 2: 준킬러]
  * 설계: 서로 다른 두 문항의 로직을 결합하라 (예: 문항 X의 Layer A + 문항 Y의 Layer B).
  * 조건: 진입 장벽으로 첫 번째 로직을 뚫어야만 두 번째 로직의 힌트가 보이도록 인과관계를 부여하라.
* [Level 3: 킬러]
  * 설계: 세 개 이상의 문항에서 추출한 Layer A, B, C를 모두 융합하라.
  * 조건: 'The Click' 포인트를 다단계로 배치하고, 역방향 설계(Backward Design)를 통해 정답이 깔끔한 자연수가 되도록 초기 조건을 정교하게 역산하여 설정하라.

---

[Phase 2: 표면적 구조 파괴 및 시맨틱 융합 (Advanced Semantics & K-SAT Storytelling)]
융합된 문항을 최종 작성할 때, 다음의 4가지 파괴 및 재건 원칙을 **절대적**으로 준수하라.
1. 표면적 구조 100% 파기 (Format Destruction): 원본 문제의 발문 구조, 시각적 형태(그래프 유무 등), 등장하는 변수명($x, y, t, k$ 등)을 완벽하게 버려라.
2. 조건의 의미론적 은닉 (Semantic Masking): 수식을 직접 주지 말고, 그 수식이 의미하는 바를 다른 개념으로 돌려 말하라. (예: 원본의 핵심 로직이 '$f'(a)=0$을 이용한 극값 찾기'라면, 새 문제에서는 수식을 주지 말고 "어떤 점이 곡선 위를 움직일 때, 원점과의 거리가 최소가 되는 순간"과 같이 기하학적 상황으로 은닉하여 본질적으로 $f'(a)=0$을 유도하게 하라.)
3. The Click의 차원 이동 (Dimensional Shift of 'The Click'): 원본 문제의 'The Click(결정적 통찰)'이 '대칭성 활용'이었다고 가정할 때, 원본이 2차원 그래프의 대칭성이었을지라도 새 문제는 '수열의 항들의 대칭성'이나 '정적분 구간의 대칭성'으로 다른 단원에 이식하라.
4. 수능형 스토리텔링 도입 (K-SAT Formatting): 겉모습이 완전히 바뀌더라도, 대한민국 수능 수학 특유의 정제된 발문 스타일("~일 때, ~의 값을 구하시오", "다음 조건을 만족시킨다 (가), (나)")은 완벽히 유지하여 문제의 퀄리티와 긴장감을 높여라.

---

[Phase 3: 무결성 재검토 및 자가 검증 (Integrity Re-evaluation & Verification)]
문항을 출력하기 전, 출제 위원의 입장에서 다음 사항을 반드시 스스로 검증하고 수정하라.
1. 논리적 무결성: 주어진 조건만으로 유일한 해가 도출되는가? 중의적 해석의 여지는 없는가?
2. 편법 차단: 출제 의도(Core Logic)를 우회하여 대입이나 직관만으로 풀리는 '꼼수 풀이(Shortcut)'가 존재하지 않는가?
3. 계산의 깔끔함: 중간 계산 과정에서 고교 교육과정을 벗어나거나 불필요하게 지저분한 무리수/분수가 나오지 않는가?

---

[Output Format]
각 생성된 문항마다 아래의 형식을 엄격히 지켜 출력하라. 
**[절대 규칙]**: 
- 모든 수학 기호, 변수, 수식, 숫자는 반드시 LaTeX `$ ... $`로 감싸야 한다. (예: $x$, $f(x)$, $128$, $y=ax+b$)
- 극한이나 시그마 기호를 쓸 때는 반드시 `\lim\limits_{...}` 또는 `\sum\limits_{...}`를 사용하여 아래첨자가 기호 바로 아래에 오도록 하라. (단순 `\lim_{...}` 사용 금지)

1. **[Problem (난이도)]**: 새롭게 설계된 문항의 본문 내용.
   - 예시: "함수 $f(x) = x^3 - 3x + 1$에 대하여..."
2. **[Fusion Mapping]**: 이 문항이 어떤 원본 문항들의 어떤 Layer(A, B, C)를 결합하여 만들어졌는지 상세히 매핑.
3. **[Step-by-Step Solution]**: 상세한 풀이 과정. 모든 수식에 반드시 `$ ... $`를 사용할 것.
4. **[Final Answer]**: 도출된 최종 정답. (예: `$ 128 $`)
5. **[Integrity Verification]**: 무결성 검토 및 함정(Trap) 설명.
"""

def init_generated_db():
    conn = sqlite3.connect(str(GEN_DB_FILE))
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS GeneratedProblems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            difficulty TEXT,
            content TEXT,
            fusion_mapping TEXT,
            solution TEXT,
            answer TEXT,
            integrity_verification TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def parse_and_save_problems(text):
    init_generated_db()
    conn = sqlite3.connect(str(GEN_DB_FILE))
    cursor = conn.cursor()

    import re
    
    # Split the output into individual problem sections
    # Robust split that handles various header formats for "[Problem"
    problem_blocks = re.split(r'\[Problem', text)
    
    for block in problem_blocks[1:]: # Skip the first part before any problem
        # Extract difficulty: e.g. from "(Level 1)]**"
        difficulty_match = re.search(r'\((.*?)\)\]', block)

        # Extract content: everything from the end of the header to [Fusion Mapping]
        content_match = re.search(r'\][*\s\n:]*(.*?)(?=\s*\*?\*?\[Fusion Mapping\]\*?\*?)', block, re.DOTALL)
        
        # Extract fusion mapping
        fusion_match = re.search(r'\[Fusion Mapping\]\*?\*?\s*(.*?)(?=\s*\*?\*?\[Step-by-Step Solution\]\*?\*?)', block, re.DOTALL)
        
        # Extract solution
        solution_match = re.search(r'\[Step-by-Step Solution\]\*?\*?\s*(.*?)(?=\s*\*?\*?\[Final Answer\]\*?\*?)', block, re.DOTALL)

        # Extract answer: everything between [Final Answer] and [Integrity Verification]
        answer_match = re.search(r'\[Final Answer\]\*?\*?\s*[:\-]?\s*(.*?)(?=\s*\*?\*?\[Integrity Verification\]\*?\*?)', block, re.DOTALL)
        
        # Extract integrity verification
        integrity_match = re.search(r'\[Integrity Verification\]\*?\*?\s*(.*)', block, re.DOTALL)

        if difficulty_match and content_match and answer_match:
            diff = difficulty_match.group(1).strip()
            content = content_match.group(1).strip()
            fusion = fusion_match.group(1).strip() if fusion_match else ""
            solution = solution_match.group(1).strip() if solution_match else ""
            answer = answer_match.group(1).strip()
            integrity = integrity_match.group(1).strip() if integrity_match else ""
            
            # Clean up potential leading/trailing quotes or colons
            answer = re.sub(r'^[:\s]+', '', answer).strip()
            
            cursor.execute('''
                INSERT INTO GeneratedProblems (difficulty, content, fusion_mapping, solution, answer, integrity_verification)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (diff, content, fusion, solution, answer, integrity))
            print(f"  -> Saved {diff} generated problem to {GEN_DB_FILE.name}")
        else:
            print(f"  -> Warning: Failed to parse a problem block. Diff: {bool(difficulty_match)}, Content: {bool(content_match)}, Answer: {bool(answer_match)}")

    conn.commit()
    conn.close()

def get_logic_database():
    if not DB_FILE.exists():
        print(f"Error: {DB_FILE} not found. Please run db_builder.py first.")
        return None
        
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    # Limit number of problems passed to Gemini to prevent exceeding context window.
    # E.g., select 10 random problems from the DB to act as inspiration for this run.
    cursor.execute("SELECT id, source_file, problem_number, layer_a, layer_b, layer_c, trap_data FROM ProblemAnalysis ORDER BY RANDOM() LIMIT 10")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print("Error: Database is empty. Please run db_builder.py first.")
        return None
        
    db_text = ""
    for row in rows:
        pid, src, pnum, la, lb, lc, trap = row
        db_text += f"\n--- [Source: {src} | Problem: {pnum}] ---\n"
        db_text += f"Layer A: {la}\n"
        db_text += f"Layer B: {lb}\n"
        db_text += f"Layer C: {lc}\n"
        db_text += f"Trap Data: {trap}\n"
        
    return db_text

def generate_problems_stream(constraints: str = ""):
    print("Starting AI K-SAT Problem Generator (Streaming)...")
    
    logic_db_text = get_logic_database()
    if not logic_db_text:
        yield "Error: Logic database is empty."
        return

    prompt_content = [
        SYSTEM_PROMPT, 
        "다음은 기출 문항에서 무작위로 추출된(10개) 로직 데이터베이스입니다. 이를 바탕으로 융합하여 새로운 문항 세트를 설계하세요:\n" + logic_db_text
    ]
    
    if constraints:
        prompt_content.append(f"\n[CRITICAL USER CONSTRAINTS]:\n{constraints}\n위의 제약 조건을 반드시 최우선으로 준수하여 문제를 생성하세요.")

    full_response = ""
    try:
        response_stream = client.models.generate_content_stream(
            model=MODEL_ID,
            contents=prompt_content,
            config=types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.95,
            )
        )
        
        for chunk in response_stream:
            if chunk.text:
                full_response += chunk.text
                yield chunk.text
        
        # After stream ends, save to file and database
        output_file = OUTPUT_DIR / "generated_problems.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# 🌟 AI Generated K-SAT Problems\n\n")
            f.write(full_response)
            
        print(f"Success! Generated problems saved to {output_file}")
        print("Parsing and saving to generated_problems.db...")
        parse_and_save_problems(full_response)
        
    except Exception as e:
        print(f"Error during streaming generation: {e}")
        yield f"\n[Error]: {str(e)}"

def generate_problems(constraints: str = ""):
    # Legacy wrapper for synchronous calls if needed
    full_text = ""
    for chunk in generate_problems_stream(constraints):
        full_text += chunk
    return full_text

if __name__ == "__main__":
    generate_problems()
