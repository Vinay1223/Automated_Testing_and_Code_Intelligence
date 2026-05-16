import os
import subprocess
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel

load_dotenv()

class TestGenerationResult(BaseModel):
    explanation: str = Field(description="Brief explanation of the test cases covered.")
    test_code: str = Field(description="The complete, valid, executable pytest python code string. DO NOT include markdown code blocks like ```python.")

model = GroqModel(
    model_name='llama-3.3-70b-versatile',
    # api_key=os.getenv("GROQ_API_KEY")
)

# System prompt explicitly demands clean compilation
test_bot = Agent(
    model=model,
    output_type=TestGenerationResult,
    # In revision_2_agent.py, update the system_prompt:
    system_prompt=(
        "You are an expert QA Engineer specializing in writing unit tests using pytest.\n"
        "Your goal is to write raw, clean, executable Python code strings.\n"
        "CRITICAL: Pay close attention to how the target code handles exceptions. If it explicitly raises a specific exception (like ValueError), your test must expect that exact exception type.\n"
        "The `test_code` field must contain ONLY pure Python code. Never include triple backticks (```python) or markdown inside the string itself."
    )
)

def run_local_pytest(filename: str) -> tuple[bool, str]:
    """Runs pytest on the generated file and returns (passed, execution_log)"""
    try:
        # Run pytest via uv to match your environment management
        result = subprocess.run(
            ["uv", "run", "pytest", filename],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return True, result.stdout
        else:
            # Combine stdout and stderr to capture syntax errors and failures
            return False, f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    except Exception as e:
        return False, f"Failed to execute test runner: {str(e)}"

def run_revision_2():
    output_filename = "test_target_code.py"
    
    print("📖 Reading target_code.py...")
    with open("target_code.py", "r") as f:
        source_code = f.read()

    # Establish the history structure for conversational self-healing
    user_prompt = f"Please generate a complete pytest suite for the following code:\n\n{source_code}"
    
    max_retries = 3
    current_attempt = 0
    message_history = None  # Tracks conversation state across loops
    
    while current_attempt < max_retries:
        current_attempt += 1
        print(f"\n🧠 [Attempt {current_attempt}/{max_retries}] Asking Agent to generate tests...")
        
        # Run agent while preserving historical context if it's a retry
        if message_history is None:
            result = test_bot.run_sync(user_prompt)
        else:
            # Pass previous execution failures back into context
            result = test_bot.run_sync(user_prompt, message_history=message_history)
            
        # Capture current state history
        message_history = result.new_messages()
        agent_data: TestGenerationResult = result.output
        
        # Clean up accidental backticks if the model ignores system rules
        clean_code = agent_data.test_code.replace("```python", "").replace("```", "").strip()
        
        print(f"💾 Saving code to {output_filename} and running validation sandbox...")
        with open(output_filename, "w") as f:
            f.write(clean_code)
            
        # Run the validation step automatically
        passed, log = run_local_pytest(output_filename)
        
        if passed:
            print("\n🎉 Success! The agent generated perfectly compiling code that passes all tests!")
            print(f"💡 Explanation:\n{agent_data.explanation}")
            break
        else:
            print(f"❌ Validation Failed! Syntax or runtime error encountered.")
            # Set up the feedback loop prompt
            user_prompt = (
                f"The test file you generated failed validation with the following errors:\n\n"
                f"{log}\n\n"
                f"Please inspect the errors, check your imports, eliminate any accidental markdown wrapped inside your strings, and fix the code."
            )
            
    if not passed:
        print("\n⚠️ Max retries reached. The system could not auto-heal the syntax natively.")

if __name__ == "__main__":
    run_revision_2()