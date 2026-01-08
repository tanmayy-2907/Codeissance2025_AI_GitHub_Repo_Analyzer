# Codeissance2025

A FastAPI-based service that accepts a GitHub repository link, sends the repository (or its contents/summary) to an Ollama model, and returns actionable suggestions on what could be improved (architecture, code quality, docs, testing, etc.).

## Features
- Accepts a **GitHub repository URL** as input
- Uses **FastAPI** to expose an HTTP API
- Calls an **Ollama** LLM to analyze the project
- Returns **improvement suggestions** (best practices, refactors, missing tests/docs, structure recommendations)

## Tech Stack
- **Python**
- **FastAPI**
- **Ollama** (local LLM inference)

## Getting Started

### Prerequisites
- Python 3.10+ (recommended)
- Ollama installed and running: https://ollama.com/
- An Ollama model pulled locally (example: `llama3`, `mistral`, etc.)

### Installation
```bash
git clone https://github.com/tanmayy-2907/Codeissance2025.git
cd Codeissance2025
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows (PowerShell)
# .\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### Run Ollama
Make sure Ollama is running locally. For example, to pull a model:
```bash
ollama pull llama3
```

### Run the API
```bash
uvicorn main:app --reload
```

Then open:
- API docs (Swagger): `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## API Usage

### Example Request
Send a GitHub repo URL and get improvement suggestions.

> Note: The exact endpoint/body may differ depending on your implementation—adjust the path/fields below to match your code.

```bash
curl -X POST "http://127.0.0.1:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/psf/requests"
  }'
```

### Example Response
```json
{
  "repo_url": "https://github.com/psf/requests",
  "summary": "High-level project overview from the model...",
  "improvements": [
    "Add contribution guidelines and a clearer development setup section.",
    "Increase unit test coverage for edge cases in ...",
    "Consider adding pre-commit hooks for formatting and linting."
  ]
}
```

## Configuration
Common things you may want to configure:
- Ollama host (default is usually `http://localhost:11434`)
- Model name (e.g., `llama3`, `mistral`)
- Timeouts / max tokens
- Repo ingestion strategy (clone vs. GitHub API vs. reading key files)

If your project uses environment variables, document them here (example):
```bash
export OLLAMA_HOST="http://localhost:11434"
export OLLAMA_MODEL="llama3"
```
