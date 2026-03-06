import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.generator import parse_and_save_problems

def test_actual_file_parsing():
    content_file = Path("backend/generated/generated_problems.md")
    if not content_file.exists():
        content_file = Path("generated/generated_problems.md")
    
    if not content_file.exists():
        print("Error: generated_problems.md not found.")
        return
        
    with open(content_file, "r", encoding="utf-8") as f:
        text = f.read()
        
    print(f"Testing parsing of {content_file}...")
    parse_and_save_problems(text)
    print("Done. Please check the DB using view_db.py --generated")

if __name__ == "__main__":
    test_actual_file_parsing()
