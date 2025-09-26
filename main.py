import os
import shutil
import tempfile
import json
import stat
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from runner import run_command, detect_project_type, check_for_test_files
# Updated import to fix the deprecation warning
from langchain_ollama import OllamaLLM as Ollama
from git import Repo, GitCommandError

app = FastAPI(title="EngiVerse AI Analyzer API")

# Increased timeout for the more complex prompt
llm = Ollama(model="codellama", timeout=180)

# --- Helper Functions ---
def remove_readonly(func, path, _):
    """Clear the readonly bit and reattempt the removal on Windows."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def read_project_files(path: str, max_chars: int = 15000) -> str:
    """
    Reads the content of all relevant source code files in a project directory
    and concatenates them into a single string.
    """
    all_code_content = ""
    file_extensions = ('.js', '.py', '.html', '.css', '.jsx', '.ts', '.tsx', '.java', '.go', '.rs')
    ignore_dirs = ('.git', 'node_modules', 'venv', '__pycache__')

    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            if file.endswith(file_extensions):
                try:
                    with open(os.path.join(root, file), "r", encoding="utf-8", errors="ignore") as f:
                        all_code_content += f"--- File: {file} ---\n{f.read()}\n\n"
                        if len(all_code_content) > max_chars:
                            return all_code_content[:max_chars]
                except Exception:
                    continue
    return all_code_content

# --- API Models and Endpoints ---
class AnalyzeRequest(BaseModel):
    repo_url: str

@app.get("/")
def read_root():
    return {"message": "Welcome to the EngiVerse AI Analyzer API!"}

@app.post("/analyze-repository")
def analyze_repository(request: AnalyzeRequest):
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 1. Clone Repo
        clean_url = request.repo_url.split('?')[0]
        Repo.clone_from(clean_url, temp_dir)
        
        # --- 2. Health Report Generation ---
        health_report = {}
        project_type = detect_project_type(temp_dir)
        
        readme_path = os.path.join(temp_dir, "README.md")
        readme_content = ""
        if os.path.exists(readme_path):
            health_report["readme_is_present"] = True
            with open(readme_path, "r", encoding="utf-8", errors='ignore') as f:
                readme_content = f.read()
        else:
            health_report["readme_is_present"] = False

        build_command = "npm install" if project_type == "nodejs" else "pip install -r requirements.txt"
        health_report["build_successful"] = run_command(build_command, temp_dir)["success"]
        
        test_command = "npm test" if project_type == "nodejs" else "pytest"
        health_report["tests_found_and_passed"] = check_for_test_files(temp_dir) and run_command(test_command, temp_dir)["success"]
        
        # --- 3. Detailed AI Analysis ---
        code_content = read_project_files(temp_dir)
        
        detailed_prompt = f"""
        You are 'Code-Compass', an AI expert at analyzing open-source projects for the EngiVerse platform. 
        Your purpose is to provide a rich, detailed, and structured analysis in a single JSON object to guide new contributors.

        <CONTEXT>
        <README>
        {readme_content if readme_content else "No README provided."}
        </README>
        <SOURCE_CODE>
        {code_content}
        </SOURCE_CODE>
        </CONTEXT>

        <INSTRUCTIONS>
        Generate a single JSON object with two top-level keys: "project_overview" and "contribution_guide".
        1.  The "project_overview" object should contain:
            - "elevator_pitch": A single, compelling sentence.
            - "detailed_description": A paragraph explaining the project's purpose and the problem it solves.
            - "target_audience": A brief description of who would use this project.
            - "tech_stack": An array of strings listing the key technologies.
        2.  The "contribution_guide" object should contain:
            - "current_status": A description of how complete the project is.
            - "contribution_friendliness": A score from 1-10 and a brief justification.
            - "first_good_issue": A specific, actionable task a new developer could tackle first.
            - "suggested_roadmap": An array of 3-4 major features or next steps for the project's future.

        Do not include any text or markdown formatting outside of the main JSON object.
        </INSTRUCTIONS>
        """
        
        ai_response_text = llm.invoke(detailed_prompt)

        # 4. Parse the AI's response as JSON (Robust version)
        try:
            start_index = ai_response_text.find('{')
            end_index = ai_response_text.rfind('}') + 1
            
            if start_index != -1 and end_index != 0:
                json_string = ai_response_text[start_index:end_index]
                ai_json_response = json.loads(json_string)
            else:
                raise json.JSONDecodeError("No JSON object found in the response.", ai_response_text, 0)

        except json.JSONDecodeError:
            ai_json_response = {"error": "Failed to parse AI summary.", "raw_response": ai_response_text}

        # 5. Combine and Return Results
        final_response = {
            "health_report": health_report
        }
        final_response.update(ai_json_response)
        
        return final_response

    except GitCommandError as e:
        raise HTTPException(status_code=400, detail=f"Failed to clone repository. Is the URL correct and public? Error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
    finally:
        # 6. Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, onerror=remove_readonly)

