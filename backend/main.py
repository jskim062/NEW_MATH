from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import os
import shutil
from pathlib import Path
from typing import Optional

# Import our custom logic
from .solver import solve_single_pdf, process_math_problem, save_solutions_incremental
from .generator import generate_problems, generate_problems_stream, GEN_DB_FILE

app = FastAPI(title="AI_KICE API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup directories
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
SOLUTIONS_DIR = BASE_DIR / "solutions"
PROBLEMS_DIR = BASE_DIR / "problems"
GENERATED_DIR = BASE_DIR / "generated"

class GenerateRequest(BaseModel):
    constraints: Optional[str] = ""

class SolveRequest(BaseModel):
    filename: str

@app.get("/")
def read_root():
    return {"message": "Welcome to the Math Problem Solver API"}

@app.get("/api/solutions")
def list_solutions():
    if not SOLUTIONS_DIR.exists():
        return []
    md_files = sorted([f.name for f in SOLUTIONS_DIR.glob("*.md")])
    return [f for f in md_files if "_solutions" in f]

@app.get("/api/solution/{filename}")
def get_solution(filename: str):
    filepath = SOLUTIONS_DIR / filename
    if not filepath.exists() or filepath.suffix != ".md":
        raise HTTPException(status_code=404, detail="Solution file not found")
        
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            content = content.replace('\\\\', '\\').replace('\\n', '\n')
            
            import re
            content = re.sub(r'(?<!\n\n) *([①②③④⑤])', r'\n\n\1', content)
            return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pdfs")
def list_pdfs():
    if not PROBLEMS_DIR.exists():
        return []
    pdf_files = sorted([f.name for f in PROBLEMS_DIR.glob("*.pdf")])
    return pdf_files

@app.get("/api/pdf/{filename}")
def get_pdf(filename: str):
    filepath = PROBLEMS_DIR / filename
    if not filepath.exists() or filepath.suffix != ".pdf":
        raise HTTPException(status_code=404, detail="PDF file not found")
    return FileResponse(filepath, media_type="application/pdf")

@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    PROBLEMS_DIR.mkdir(parents=True, exist_ok=True)
    file_path = PROBLEMS_DIR / file.filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"filename": file.filename, "message": "Successfully uploaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/solve")
async def solve_pdf(request: SolveRequest):
    file_path = PROBLEMS_DIR / request.filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    try:
        # This might take a while, in a real app we'd use BackgroundTasks
        results = solve_single_pdf(file_path)
        return {"message": f"Successfully processed {len(results)} problems", "filename": request.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/generated")
def get_generated():
    filepath = GENERATED_DIR / "generated_problems.md"
    if not filepath.exists():
         return {"content": "아직 생성된 문제 세트가 없습니다. 생성하기 버튼을 눌러주세요."}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return {"content": f.read().replace('\\\\', '\\').replace('\\n', '\n')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate")
async def generate(request: GenerateRequest):
    try:
        content = generate_problems(constraints=request.constraints)
        return {"message": "Successfully generated new problems.", "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stream/generate")
async def stream_generate(request: GenerateRequest):
    def event_generator():
        for chunk in generate_problems_stream(request.constraints):
            yield chunk

    return StreamingResponse(event_generator(), media_type="text/plain")

@app.post("/api/stream/solve")
async def stream_solve(request: SolveRequest):
    file_path = PROBLEMS_DIR / request.filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    filename = f"{file_path.stem}_solutions.md"
    filepath = SOLUTIONS_DIR / filename
    
    # We want to yield the content as it's being generated
    def solve_generator():
        from .solver import get_processed_pages
        processed_pages = get_processed_pages(filepath)
        
        for page_num, page_results in process_math_problem(file_path, processed_pages):
            if page_results:
                save_solutions_incremental(page_results, file_path.name, page_num)
                # For streaming, we yield a marker or the new markdown content
                yield f"--- [Page {page_num}] ---\n"
                for data in page_results:
                    yield f"#### Problem {data.get('problem_number', '0')}\n\n"
                    transcription = data.get('transcription', 'N/A')
                    yield f"**📝 Original Problem**\n{transcription}\n\n"
                    yield f"**💡 Step-by-Step Reasoning**\n{data.get('step_by_step_reasoning', 'N/A')}\n\n"
                    
                    # Ensure the final answer is wrapped in LaTeX delimiters
                    answer = data.get('final_answer', 'N/A').strip()
                    if not answer.startswith('$'):
                        answer = f"$ {answer} $"
                    yield f"**✅ Final Answer**: {answer}\n\n"

    return StreamingResponse(solve_generator(), media_type="text/plain")

@app.get("/api/generated_problems")
async def get_generated_problems():
    import sqlite3
    if not GEN_DB_FILE.exists():
        return []
    
    conn = sqlite3.connect(str(GEN_DB_FILE))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, difficulty, created_at FROM GeneratedProblems ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

@app.get("/api/generated_problem/{problem_id}")
async def get_generated_problem(problem_id: int):
    import sqlite3
    if not GEN_DB_FILE.exists():
        return {"error": "Database not found"}
    
    conn = sqlite3.connect(str(GEN_DB_FILE))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM GeneratedProblems WHERE id = ?", (problem_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return {"error": "Problem not found"}
        
    return dict(row)

@app.post("/api/sync_generated")
async def sync_generated_problems():
    from .generator import parse_and_save_problems, OUTPUT_DIR
    import os
    
    file_path = OUTPUT_DIR / "generated_problems.md"
    if not file_path.exists():
        return {"success": False, "error": "generated_problems.md not found"}
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        parse_and_save_problems(content)
        return {"success": True, "message": "Successfully synchronized generated problems to DB"}
    except Exception as e:
        return {"success": False, "error": str(e)}
