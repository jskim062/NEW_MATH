import os
import streamlit as st
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import io
from dotenv import load_dotenv
from google import genai

# Setup Directories
SOLUTIONS_DIR = Path("solutions")
PROBLEMS_DIR = Path("problems")

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    client = genai.Client(api_key=api_key)
else:
    client = None

st.set_page_config(layout="wide", page_title="Math Problem Solver Viewer", page_icon="📝")

st.title("Elite Mathematical Problem Solver 📝")
st.markdown("수능/모의고사 수학 문제 AI 풀이 뷰어입니다. 좌측에서 문제 원본을, 우측에서 단계별 해설을 확인하세요.")

tab1, tab2 = st.tabs(["📚 원본 문제 해설 뷰어", "✨ AI 융합 출제 문항 (Generated)"])

@st.cache_data(show_spinner=False)
def reformat_markdown_with_gemini(content: str) -> str:
    """Uses Gemini to properly format the markdown content for readability."""
    if not client:
        return content  # Fallback if no API key
    try:
        reformat_prompt = """
        다음 마크다운 내용에서 가독성을 높이기 위해 양식을 교정해줘.
        
        [교정 규칙]
        1. (가), (나), (다) 등의 조건문은 블록인용구(blockquote, `> (가) ...`)로 변경해줘.
        2. 객관식 보기(①, ②, ③, ④, ⑤)는 기존 텍스트에 한 줄로 붙어있더라도, **반드시 각각의 보기마다 강제로 줄바꿈(엔터)을 두 번 넣어서** 리스트 형태로 세로로 길게 정렬해줘.
        3. 풀이 과정의 1., 2., 3. 같은 번호 매기기는 무조건 새 줄에서 시작하고 시각적으로 구분되게 단락을 나눠줘.
        4. 수식(\\(...\\), $$...$$)이나 그 안의 내용(예: LaTeX 문법 백슬래시 \\sqrt 등)은 절대로 건드리지 마.
        5. 그 외의 마크다운 구조(## Heading 부분 등)나 텍스트의 본래 문장은 변경하지 마.
        
        [원본 내용]
        """
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=[reformat_prompt + content]
        )
        if response.text:
            return response.text
        return content
    except Exception as e:
        return content

def load_markdown_content(filepath: Path) -> str:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
            # The JSON payload from Gemini escapes backslashes (\\\\) and newlines (\\n).
            content = content.replace('\\\\', '\\')
            content = content.replace('\\n', '\n')
            
            # To ensure \lim subscripts appear directly underneath the operator in inline mode: # Optional fix
            content = content.replace(r'\lim_{', r'\lim\limits_{')
            
            # To ensure \sum (sigma) limits appear directly underneath/above the operator in inline mode: 
            content = content.replace(r'\sum_{', r'\sum\limits_{')
            
            # Reformat visual structure dynamically via LLM
            content = reformat_markdown_with_gemini(content)
            
            # Fallback regex for multiple-choice options in case the LLM fails to add double newlines
            import re
            content = re.sub(r'(?<!\n\n) *([①②③④⑤])', r'\n\n\1', content)
            
            return content
    except Exception as e:
        return f"Error loading file: {e}"

def render_pdf_page(pdf_path: Path, page_num: int):
    """Renders a specific page of a PDF as an image for Streamlit."""
    try:
        doc = fitz.open(pdf_path)
        if page_num < 0 or page_num >= len(doc):
            return None
        page = doc.load_page(page_num)
        # Increase resolution
        zoom = 2.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img_data = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_data))
        return image
    except Exception as e:
        st.error(f"Error rendering PDF: {e}")
        return None

    # Sidebar logic for selecting solutions
    st.sidebar.header("📁 Saved Solutions")
    
    if not SOLUTIONS_DIR.exists():
        st.sidebar.warning("솔루션 폴더가 없습니다. 스크립트를 먼저 실행해주세요.")
        st.stop()
    
    md_files = sorted(list(SOLUTIONS_DIR.glob("*.md")))
    
    if not md_files:
        st.sidebar.info("아직 저장된 문제 풀이가 없습니다.")
        st.stop()

    # Let user pick a solution file
    selected_solution = st.sidebar.selectbox(
        "풀이를 확인할 문제를 선택하세요:", 
        options=md_files, 
        format_func=lambda x: x.name
    )

    # Render main split view
    if selected_solution:
        col1, col2 = st.columns([1, 1], gap="large")
        
        with col1:
            st.subheader("📄 원본 문제 (PDF)")
            
            # Logic to find the matching PDF
            pdf_files = sorted(list(PROBLEMS_DIR.glob("*.pdf")))
            
            if pdf_files:
                selected_pdf = st.selectbox("문제지 (PDF) 선택:", options=pdf_files, format_func=lambda x: x.name)
                
                try:
                    doc = fitz.open(selected_pdf)
                    total_pages = len(doc)
                    doc.close()
                    
                    selected_page = st.number_input("페이지 번호 선택", min_value=1, max_value=total_pages, value=1) - 1
                    
                    pdf_image = render_pdf_page(selected_pdf, selected_page)
                    if pdf_image:
                        st.image(pdf_image, use_container_width=True, caption=f"Page {selected_page + 1} of {selected_pdf.name}")
                except Exception as e:
                    st.error("Error reading PDF.")
            else:
                st.info("problems 폴더에 PDF 파일이 없습니다.")
                
        with col2:
            st.subheader("💡 AI 풀이 (LaTeX)")
            # Display a loading spinner while LLM is formatting
            with st.spinner("AI가 풀이 화면을 예쁘게 정돈하고 있습니다..."):
                content = load_markdown_content(selected_solution)
            # Streamlit nativelly renders Markdown including LaTeX math formulas
            st.markdown(content)

with tab2:
    st.subheader("🌟 AI Generated K-SAT Problems")
    st.markdown("원본 해설지의 로직을 추출하여 완전히 새롭게 융합 출제한 난이도별 3문항 세트입니다.")
    
    generated_file = Path("generated") / "generated_problems.md"
    if generated_file.exists():
        with open(generated_file, "r", encoding="utf-8") as f:
            generated_content = f.read()
            
        generated_content = generated_content.replace('\\\\', '\\')
        generated_content = generated_content.replace('\\n', '\n')
        generated_content = generated_content.replace(r'\lim_{', r'\lim\limits_{')
        generated_content = generated_content.replace(r'\sum_{', r'\sum\limits_{')
        
        with st.container():
            st.markdown(generated_content)
    else:
        st.info("아직 생성된 문제 세트가 없습니다. `generator.py` 스크립트를 먼저 실행해주세요.")
