# NEW_MATH: AI-Powered K-SAT Math Problem Generator

An intelligent pipeline designed to analyze Korean Scholastic Aptitude Test (K-SAT) mathematics problems, extract their underlying logical layers, and generate entirely new problems through advanced logic fusion.

## Features

1.  **PDF Math Solver (`solver.py`)**: Uses Google's Gemini Vision models to perform OCR on K-SAT math PDFs and solves them step-by-step, generating structured markdown solutions.
2.  **Logic Database Builder (`db_builder.py`)**: Analyzes the generated solutions to extract multi-layer mathematical logics (Layer A: Structure, Layer B: Tool, Layer C: Inference) and common traps, saving them into an SQLite database.
3.  **AI Problem Generator (`generator.py`)**: Acts as a "K-SAT Problem Architect." It synthesizes the logic database to generate brand new problems across different difficulty levels (Level 1, Level 2, Level 3) using strict rules like Semantic Masking and Format Destruction.
4.  **Interactive Viewer (`app.py`)**: A Streamlit web application to view the original PDFs, their extracted step-by-step solutions, and the newly generated AI problems side-by-side.

## Setup

1.  Clone the repository.
2.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Create a `.env` file in the root directory and add your Gemini API key:
    ```env
    GEMINI_API_KEY=your_api_key_here
    ```

## Usage

*   Place K-SAT PDF files into the `problems/` directory.
*   Run the solver to generate solutions: `python solver.py`
*   Build the logic database: `python db_builder.py`
*   Generate new problems: `python generator.py`
*   Launch the viewer: `streamlit run app.py`

## Architecture

*   **Models Used**: `gemini-3.1-flash-image-preview` (OCR), `gemini-3.1-pro-preview` / `gemini-3-pro-preview` (Solving & Generating)
*   **Database**: SQLite (`problems.db`)
*   **UI**: Streamlit
