import os
import subprocess
import time
from dotenv import load_dotenv
from github import Github
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel

# Import our custom AST Profiler
from revision_3_profiler import CodeProfiler

load_dotenv()

# --- Configurations ---
GITHUB_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
TARGET_REPO_NAME = "Vinay1223/Automated_Testing_and_Code_Intelligence" # Your exact GitHub repo name

class TestGenerationResult(BaseModel):
    explanation: str = Field(description="Explanation of the test cases.")
    test_code: str = Field(description="Pure, valid, executable pytest code. No markdown backticks.")

model = GroqModel(
    model_name='llama-3.3-70b-versatile',
)

test_bot = Agent(
    model=model,
    output_type=TestGenerationResult,
    system_prompt=(
        "You are an expert QA Engineer specializing in writing unit tests using pytest.\n"
        "Your goal is to write raw, clean, executable Python code strings.\n"
        "CRITICAL: The `test_code` field must contain ONLY pure Python code. Never include triple backticks.\n"
        "Pay close attention to exceptions. If the code explicitly raises a specific error (like ValueError), your test must expect that exact exception type."
    )
)

def run_local_pytest(filename: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(["uv", "run", "pytest", filename], capture_output=True, text=True, timeout=10)
        return (True, result.stdout) if result.returncode == 0 else (False, f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    except Exception as e:
        return False, f"Failed to execute test runner: {str(e)}"

def create_github_pr(func_name: str, file_path: str, code_content: str, explanation: str):
    """The Git Agent: Authenticates, branches, commits, and opens a PR."""
    print("\n🌐 Connecting to GitHub...")
    g = Github(GITHUB_TOKEN)

    try:
        repo = g.get_repo(TARGET_REPO_NAME)
        
        # 1. Get the default branch dynamically (main or master)
        default_branch_name = repo.default_branch
        source_branch = repo.get_branch(default_branch_name)
        
        # 2. Create a new branch for this specific test
        branch_name = f"add-tests-{func_name}-{int(time.time())}"
        repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=source_branch.commit.sha)
        print(f"🌿 Created new branch: {branch_name}")
        
        # 3. Commit the new test file
        commit_message = f"test: Add automated pytest suite for {func_name}"
        repo.create_file(
            path=file_path, 
            message=commit_message, 
            content=code_content, 
            branch=branch_name
        )
        print(f"💾 Committed {file_path} to branch.")
        
        # 4. Open the Pull Request (pointing back to the dynamic default branch)
        pr_title = f"Add automated tests for `{func_name}`"
        pr_body = (
            f"### Automated Test Contribution\n\n"
            f"This PR introduces a validated test suite for the `{func_name}` function.\n\n"
            f"**AI Agent Explanation:**\n{explanation}\n\n"
            f"*Generated & validated autonomously via PydanticAI Testing Agent.*"
        )
        
        pr = repo.create_pull(title=pr_title, body=pr_body, head=branch_name, base=default_branch_name)
        print(f"🎉 SUCCESS! Pull Request Created: {pr.html_url}\n")
        
    except Exception as e:
        print(f"❌ GitHub API Error: {str(e)}")

def run_autonomous_pipeline():
    print("🚀 Starting HITL Multi-Agent PR Pipeline...")
    
    target_dir = "sample_repo"
    profiler = CodeProfiler(target_dir)
    discovered_functions = profiler.profile_repository()
    
    if not discovered_functions:
        print("⚠️ No functions found. Check your directory.")
        return
        
    for target in discovered_functions:
        func_name = target['name']
        file_path = target['file']
        source_code = target['source_code']
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        
        print(f"\n{'='*50}\n🎯 Target: '{func_name}'\n{'='*50}")
        
        user_prompt = (
            f"Please generate a complete pytest suite for the following function.\n"
            f"Assume you can import the function using: `from {target_dir}.{module_name} import {func_name}`\n\n"
            f"Function Source:\n{source_code}"
        )
        
        max_retries = 3
        current_attempt = 0
        message_history = None
        passed = False
        output_filename = f"tests/test_{func_name}.py"
        
        while current_attempt < max_retries:
            current_attempt += 1
            print(f"🧠 [Attempt {current_attempt}/3] Generating and validating tests...")
            
            result = test_bot.run_sync(user_prompt, message_history=message_history) if message_history else test_bot.run_sync(user_prompt)
            message_history = result.new_messages()
            agent_data: TestGenerationResult = result.output
            
            clean_code = agent_data.test_code.replace("```python", "").replace("```", "").strip()
            
            os.makedirs("tests", exist_ok=True)
            with open(output_filename, "w") as f:
                f.write(clean_code)
                
            passed, log = run_local_pytest(output_filename)
            
            if passed:
                print(f"✅ Local Sandbox Passed!")
                break
            else:
                print(f"⚠️ Validation Failed. Self-healing...")
                with open(output_filename, "r") as f:
                    bad_code = f.read()
                user_prompt = f"CRITICAL FIX REQUIRED!\nBroken Code:\n{bad_code}\n\nPytest Error:\n{log}\nFix syntax and imports."
                
        if passed:
            # --- HUMAN IN THE LOOP (HITL) ---
            print("\n" + "-"*40)
            print("📝 PROPOSED TEST CODE:")
            print("-" * 40)
            print(clean_code)
            print("-" * 40)
            
            user_input = input(f"\n🛑 Do you want to open a GitHub PR for {func_name}? (y/n): ").strip().lower()
            if user_input == 'y':
                # Map the test file to be saved inside a tests/ folder in the repo
                repo_file_path = f"tests/{output_filename}" 
                create_github_pr(func_name, repo_file_path, clean_code, agent_data.explanation)
            else:
                print("⏭️ PR Creation Skipped. Moving to next function.")
        else:
            print(f"⚠️ Agent failed to auto-heal '{func_name}'. Skipping.")

if __name__ == "__main__":
    run_autonomous_pipeline()