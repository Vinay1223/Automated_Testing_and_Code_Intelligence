import os
import subprocess
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel

# 1. Import our custom AST Profiler (Agent 1)
from revision_3_profiler import CodeProfiler

load_dotenv()

# 2. Define structured output
class TestGenerationResult(BaseModel):
    explanation: str = Field(description="Explanation of the test cases.")
    test_code: str = Field(description="Pure, valid, executable pytest code. No markdown backticks.")

model = GroqModel(
    model_name='llama-3.3-70b-versatile',
)

# 3. Test Generator Agent (Agent 2)
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
    """The Sandbox Executor (Agent 3)"""
    try:
        result = subprocess.run(
            ["uv", "run", "pytest", filename],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    except Exception as e:
        return False, f"Failed to execute test runner: {str(e)}"

def run_autonomous_pipeline():
    print("🚀 Starting Autonomous Multi-Agent Pipeline...")
    
    # --- PHASE 1: Profiling ---
    target_dir = "sample_repo"
    profiler = CodeProfiler(target_dir)
    discovered_functions = profiler.profile_repository()
    
    if not discovered_functions:
        print("⚠️ No functions found. Check your sample_repo directory.")
        return
        
    print(f"📊 Profiler found {len(discovered_functions)} functions. Initiating Test Generation...\n")
    
    # --- PHASE 2: Orchestration Loop ---
    for target in discovered_functions:
        func_name = target['name']
        file_path = target['file']
        source_code = target['source_code']
        
        print(f"==================================================")
        print(f"🎯 Target Acquired: '{func_name}' from {file_path}")
        print(f"==================================================")
        
        # We dynamically figure out the import path based on the file location
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        
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
        
        # --- PHASE 3: The Self-Healing Sandbox ---
        while current_attempt < max_retries:
            current_attempt += 1
            print(f"🧠 [Attempt {current_attempt}/3] Asking Agent 2 to generate tests for {func_name}...")
            
            if message_history is None:
                result = test_bot.run_sync(user_prompt)
            else:
                result = test_bot.run_sync(user_prompt, message_history=message_history)
                
            message_history = result.new_messages()
            agent_data: TestGenerationResult = result.output
            
            clean_code = agent_data.test_code.replace("```python", "").replace("```", "").strip()
            
            os.makedirs("tests", exist_ok=True)
            with open(output_filename, "w") as f:
                f.write(clean_code)
                
            passed, log = run_local_pytest(output_filename)
            
            if passed:
                print(f"🎉 Success! Tests for '{func_name}' generated perfectly.")
                break
            else:
                print(f"❌ Validation Failed. Triggering self-healing loop...")
                with open(output_filename, "r") as f:
                    bad_code = f.read()
                    
                user_prompt = (
                    f"CRITICAL FIX REQUIRED!\n"
                    f"The code you just generated caused an execution failure.\n\n"
                    f"--- YOUR BROKEN CODE ---\n{bad_code}\n-----------------------\n\n"
                    f"--- PYTEST ERROR ---\n{log}\n--------------------\n\n"
                    f"Fix the syntax, check the imports (from {target_dir}.{module_name} import {func_name}), and ensure correct exception handling."
                )
                
        if not passed:
            print(f"⚠️ Agent failed to auto-heal '{func_name}' after {max_retries} retries. Skipping to next target.")
            
    print("\n🏁 Pipeline complete! Check your directory for the generated test files.")

if __name__ == "__main__":
    run_autonomous_pipeline()