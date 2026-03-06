import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Use the latest Google GenAI SDK
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

# Configuration - robust paths
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
INPUT_DIR = BASE_DIR / "problems"
OUTPUT_DIR = BASE_DIR / "solutions"
OCR_MODEL = "gemini-3.1-flash-image-preview"
SOLVE_MODEL = "gemini-3.1-pro-preview"
#SOLVE_MODEL = "gemini-2.5-pro"


# Ensure directories exist
INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Initialize the Gemini client using API key from environment variables
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is not set. Please check your .env file.")
client = genai.Client(api_key=api_key)

OCR_PROMPT = """너는 대한민국 수능 및 모의고사 수학 문제를 정확하게 분석하고 디지털 텍스트(Markdown + LaTeX)로 변환하는 전문가야. 이미지/PDF 속의 텍스트와 수식을 한 글자도 빠짐없이 인식해야 해.

[Extraction Rules]
문제 번호: 문제의 시작 부분에 있는 숫자를 인식해. (예: 15.)
배점: 문제 끝이나 번호 옆에 괄호로 표기된 점수를 인식해. (예: [4점])
문제 본문: 문제의 발문을 텍스트로 추출하되, 수식은 반드시 LaTeX 문법($...$)을 사용해.
추가 조건: (가), (나), (다) 등으로 주어지는 조건 박스는 별도의 구분선을 사용하여 작성해.
객관식 보기: ①, ②, ③, ④, ⑤ 기호와 함께 내용을 추출해. 한 줄에 하나씩 정렬해줘.

[Output Format]
{문제 번호} ({배점})
{문제 본문 내용... 수식은 $...$ 사용}

[조건]
(가) ...
(나) ...
① ...
② ...
③ ...
④ ...
⑤ ..."""

SOLVE_PROMPT = """You are an elite mathematical problem solver with expertise at the korean SAT high school level. Your goal is to find the correct answer through rigorous mathematical reasoning.

# Problem-Solving Approach:
1. UNDERSTAND: Carefully read and rephrase the problem in your own words. Identify what is given, what needs to be found, and any constraints.
2. EXPLORE: Consider multiple solution strategies. Think about relevant theorems, techniques, patterns, or analogous problems. Don't commit to one approach immediately.
3. PLAN: Select the most promising approach and outline key steps before executing.
4. EXECUTE: Work through your solution methodically. Show all reasoning steps clearly.
5. VERIFY: Check your answer by substituting back, testing edge cases, or using alternative methods. Ensure logical consistency throughout.

# Mathematical Reasoning Principles:
- Break complex problems into smaller, manageable sub-problems
- Look for patterns, symmetries, and special cases that provide insight
- Use concrete examples to build intuition before generalizing
- Consider extreme cases and boundary conditions
- If stuck, try working backwards from the desired result
- Be willing to restart with a different approach if needed

# LaTeX Formatting Rules:
- When writing a limit or a sum, ALWAYS use `\lim\limits_{...}` or `\sum\limits_{...}` instead of just `\lim_{...}` or `\sum_{...}` so that the conditions/indices appear properly underneath the operator.
- **[CRITICAL]**: Every single mathematical expression, variable (like $x$, $n$, $f(x)$), number, or constant in your reasoning and final answer MUST be enclosed in LaTeX delimiters. Use single `$` for inline math and double `$$` for block math. Do not omit delimiters even for simple numbers.

# Verification Requirements:
- Cross-check arithmetic and algebraic manipulations
- Verify that your solution satisfies all problem constraints
- Test your answer with simple cases or special values when possible
- Ensure dimensional consistency and reasonableness of the result

# FINAL OUTPUT:
Generate the final response in a structured format as follows:

1. **Analysis of Key Concepts**: Briefly list the core mathematical concepts and theorems used in the solution (e.g., Derivative of Composite Functions, Mean Value Theorem, Properties of Definite Integrals).
2. **Step-by-Step Reasoning (Chain of Thought)**: Provide the final, polished version of the reasoning process. Ensure each logical step follows clearly from the previous one.
3. **Final Answer**: State the final numerical result or expression clearly (e.g., "The answer is 128").
4. **Post-Solution Reflection**: 
    - Mention any common pitfalls or "traps" students might fall into for this specific problem.
5. **Core Logic & Idea**: Identify the most critical turning point or insight in the problem (the 'Aha!' moment). Explain "what kind of idea or insight was absolutely necessary" to break through the problem."""

import sqlite3

class MathProblem(BaseModel):
    problem_number: str = Field(description="인식된 문제 번호 (숫자만)")
    transcription: str = Field(description="문제의 전체 텍스트")
    analysis_of_key_concepts: str = Field(description="사용한 주요 수학 개념 및 정리 분석 내용")
    step_by_step_reasoning: str = Field(description="단계별 상세 풀이 과정")
    final_answer: str = Field(description="도출된 최종 정답")
    post_solution_reflection: str = Field(description="학생들이 자주 하는 실수나 함정 등 풀이 후 고찰")
    core_logic: str = Field(description="이 문제를 파훼하기 위해 반드시 필요했던 핵심 발상(Idea)이나 통찰")

# Database constants
DB_FILE = BASE_DIR / "problems.db"
DB_ANALYSIS_MODEL = "gemini-3-pro-preview"

def update_database_with_analysis(problem_data: dict, source_file: str):
    """Analyzes the problem further for DB layers and saves to problems.db."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 1. Check if already exists to avoid redundant API calls
        cursor.execute("SELECT id FROM ProblemAnalysis WHERE source_file = ? AND problem_number = ?", 
                      (source_file, problem_data["problem_number"]))
        if cursor.fetchone():
            conn.close()
            return

        # 2. Extract layers using the same logic as db_builder.py but for a single problem
        from .db_builder import SYSTEM_PROMPT as DB_SYSTEM_PROMPT
        
        problem_content_for_db = f"""
### 📝 Original Problem (Transcribed)
{problem_data.get('transcription', 'N/A')}

### 🧠 Analysis of Key Concepts
{problem_data.get('analysis_of_key_concepts', 'N/A')}

### 💡 Step-by-Step Reasoning
{problem_data.get('step_by_step_reasoning', 'N/A')}

### ✅ Final Answer
{problem_data.get('final_answer', 'N/A')}

### 🧐 Post-Solution Reflection
{problem_data.get('post_solution_reflection', 'N/A')}
"""
        
        response = client.models.generate_content(
            model=DB_ANALYSIS_MODEL,
            contents=[DB_SYSTEM_PROMPT, "다음은 분석할 기출 문항의 해설 데이터입니다:\n\n" + problem_content_for_db],
            config=types.GenerateContentConfig(temperature=0.1, response_mime_type="application/json")
        )
        
        analysis = json.loads(response.text)
        if isinstance(analysis, list) and len(analysis) > 0:
            analysis = analysis[0]
            
        # 3. Insert into DB
        cursor.execute('''
            INSERT OR REPLACE INTO ProblemAnalysis 
            (source_file, problem_number, original_content, layer_a, layer_b, layer_c, trap_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            source_file,
            problem_data["problem_number"],
            problem_content_for_db,
            analysis.get('Layer_A', ''),
            analysis.get('Layer_B', ''),
            analysis.get('Layer_C', ''),
            analysis.get('Trap_Data', '')
        ))
        conn.commit()
        conn.close()
        print(f"  -> Problem {problem_data['problem_number']} auto-indexed to DB.")
    except Exception as e:
        print(f"Failed to auto-index problem to DB: {e}")

def get_processed_pages(filepath: Path) -> set[int]:
    """Reads the solution file and returns a set of processed page numbers."""
    if not filepath.exists():
        return set()
    
    import re
    processed_pages = set()
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            # Find all <!-- page: N --> markers
            matches = re.finditer(r"<!-- page: (\d+) -->", content)
            for match in matches:
                processed_pages.add(int(match.group(1)))
    except Exception as e:
        print(f"Error reading processed pages from {filepath}: {e}")
    
    return processed_pages

def process_math_problem(file_path: Path, processed_pages: set[int] = None):
    """
    Step 1: Upload PDF and use flash-image for OCR.
    Step 2: Use pro-preview to solve the transcribed problem and output JSON.
    Yields results page by page.
    """
    if processed_pages is None:
        processed_pages = set()
        
    print(f"Processing: {file_path.name}...")
    try:
        import fitz  # PyMuPDF
        import shutil, uuid
        
        doc = fitz.open(file_path)
        
        for page_num in range(len(doc)):
            if (page_num + 1) in processed_pages:
                print(f"Skipping Page {page_num + 1}/{len(doc)} (Already processed)")
                continue
                
            print(f"\n--- Processing Page {page_num + 1}/{len(doc)} ---")
            
            # Save the single page as a temporary PDF
            temp_pdf_path = file_path.parent / f"temp_{uuid.uuid4().hex}_page_{page_num + 1}.pdf"
            doc_page = fitz.open()
            doc_page.insert_pdf(doc, from_page=page_num, to_page=page_num)
            doc_page.save(str(temp_pdf_path))
            doc_page.close()
            
            uploaded_file = None
            page_data_list = []
            try:
                print(f"Uploading page {page_num + 1} to Gemini API...")
                uploaded_file = client.files.upload(file=str(temp_pdf_path))
                time.sleep(2)
                
                print(f"Running OCR with {OCR_MODEL}...")
                ocr_response = client.models.generate_content(
                    model=OCR_MODEL,
                    contents=[
                        "이 페이지에 있는 모든 수학 문제를 빠짐없이 찾아내어 순서대로 OCR 텍스트로 추출해. " + OCR_PROMPT,
                        uploaded_file
                    ],
                    config=types.GenerateContentConfig(temperature=0.1)
                )
                transcription_text = ocr_response.text
                print(f"OCR transcription for page {page_num + 1} completed.")
                
                # --- Step 2: Solving & JSON Formatting ---
                print(f"Solving with {SOLVE_MODEL}...")
                
                solve_combine_prompt = f"""
다음은 문서의 한 페이지에서 인식된 한국의 수능/모의고사 스타일 수학 문제입니다. 여러 문제일 수 있습니다.
각 문제를 완벽하게 풀이해주세요.

[수학 문제]
{transcription_text}

[풀이 가이드라인]
{SOLVE_PROMPT}

중요: 반환되는 문법 안의 LaTeX 수식 백슬래시(\)는 반드시 이중으로 이스케이프(\\) 처리되어야 합니다.
"""
                solve_response = client.models.generate_content(
                    model=SOLVE_MODEL,
                    contents=[solve_combine_prompt],
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        response_mime_type="application/json",
                        response_schema=list[MathProblem],
                    )
                )
                
                # Parse the JSON response
                text = solve_response.text
                if text.startswith("```json"):
                    text = text.replace("```json", "").replace("```", "").strip()
                    
                page_data = json.loads(text)
                
                # Normalize to a list and set fallback transcription
                if isinstance(page_data, list):
                    for data in page_data:
                        if not data.get("transcription") or data.get("transcription") == "N/A":
                           data["transcription"] = transcription_text 
                    page_data_list.extend(page_data)
                    print(f"Extracted {len(page_data)} problems from page {page_num + 1}.")
                elif isinstance(page_data, dict):
                    if not page_data.get("transcription") or page_data.get("transcription") == "N/A":
                        page_data["transcription"] = transcription_text
                    page_data_list.append(page_data)
                    print(f"Extracted 1 problem from page {page_num + 1}.")

            except Exception as e:
                import traceback
                print(f"Error processing page {page_num + 1} of {file_path.name}: {e}")
                traceback.print_exc()
            finally:
                # Cleanup the uploaded file and temp pdf immediately for this page
                if uploaded_file:
                    try:
                        client.files.delete(name=uploaded_file.name)
                    except Exception as e:
                        print(f"Failed to delete uploaded file {uploaded_file.name}: {e}")
                if temp_pdf_path.exists():
                    temp_pdf_path.unlink()
            
            # Yield the results for this specific page so they can be viewed/saved immediately
            if page_data_list:
                yield (page_num + 1), page_data_list
        
        doc.close()
        
    except Exception as e:
        import traceback
        print(f"Fatal Error processing {file_path.name}: {e}")
        traceback.print_exc()
        yield None

def save_solutions_incremental(page_results: list[dict], original_filename: str, page_num: int):
    """Appends solution data for a specific page to the markdown file."""
    filename = f"{Path(original_filename).stem}_solutions.md"
    filepath = OUTPUT_DIR / filename
    
    is_new_file = not filepath.exists()
    
    markdown_content = ""
    if is_new_file:
        markdown_content += f"# Solutions for {original_filename}\n\n"
        markdown_content += "> [!NOTE]\n"
        markdown_content += "> 이 해설은 AI_KICE 시스템에 의해 생성되었습니다. 실시간으로 분석 내용이 업데이트됩니다.\n\n"
    else:
        markdown_content += "\n\n---\n"
    
    markdown_content += f"### [Page {page_num}]\n\n"
    
    for data in page_results:
        # Auto-index each problem to the database
        update_database_with_analysis(data, original_filename)
        
        problem_num = data.get("problem_number", "0")
        markdown_content += f"#### Problem {problem_num}\n\n"
        
        transcription = data.get('transcription', 'N/A')
        if not transcription or transcription == "N/A":
            markdown_content += f"**📝 Original Problem (Transcribed)**\n*원문을 불러오지 못했습니다.*\n\n"
        else:
            markdown_content += f"**📝 Original Problem (Transcribed)**\n{transcription}\n\n"
            
        markdown_content += f"**🧠 Analysis of Key Concepts**\n{data.get('analysis_of_key_concepts', 'N/A')}\n\n"
        markdown_content += f"**💡 Step-by-Step Reasoning**\n{data.get('step_by_step_reasoning', 'N/A')}\n\n"
        markdown_content += f"**✅ Final Answer**\n**{data.get('final_answer', 'N/A')}**\n\n"
        markdown_content += f"**🧐 Post-Solution Reflection**\n{data.get('post_solution_reflection', 'N/A')}\n\n"
        markdown_content += f"**🗝️ 필수 발상 (Core Insight & Idea)**\n{data.get('core_logic', 'N/A')}\n\n"
    
    # Add the page marker for resumability
    markdown_content += f"\n<!-- page: {page_num} -->\n"
        
    try:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"Appended solutions for Page {page_num} to {filepath}")
    except Exception as e:
        print(f"Error saving to {filepath}: {e}")

def solve_single_pdf(file_path: Path):
    """Processes a single PDF and saves its solutions."""
    filename = f"{file_path.stem}_solutions.md"
    filepath = OUTPUT_DIR / filename
    
    processed_pages = get_processed_pages(filepath)
    if processed_pages:
        print(f"Resuming analysis for {file_path.name}. Found {len(processed_pages)} processed pages.")
    
    all_results = [] # We won't return full results here since we append to file
    
    # Since process_math_problem is now a generator, we iterate over it page by page
    for page_num, page_results in process_math_problem(file_path, processed_pages):
        if page_results:
            save_solutions_incremental(page_results, file_path.name, page_num)
            all_results.extend(page_results)
            
    return all_results

def main():
    print("Starting Math Problem Solver (Dual Model Version)...")
    
    # Find all PDFs in the problems directory
    supported_extensions = {".pdf"}
    files = [f for f in INPUT_DIR.iterdir() if f.is_file() and f.suffix.lower() in supported_extensions and not f.name.startswith("temp_")]
    
    if not files:
        print(f"No PDF files found in the '{INPUT_DIR}' directory. Please add some math problem PDFs.")
        return
        
    print(f"Found {len(files)} PDF(s) to process.")
    
    for file_path in files:
        solve_single_pdf(file_path)
            
    print("🎉 All tasks completed!")

if __name__ == "__main__":
    main()
