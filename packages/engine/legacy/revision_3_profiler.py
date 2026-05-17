import ast
import os

class CodeProfiler:
    def __init__(self, target_directory: str):
        self.target_directory = target_directory

    def get_python_files(self) -> list[str]:
        """Recursively finds all Python files in the target directory."""
        py_files = []
        for root, _, files in os.walk(self.target_directory):
            for file in files:
                if file.endswith(".py") and not file.startswith("test_"):
                    py_files.append(os.path.join(root, file))
        return py_files

    def extract_functions(self, filepath: str) -> list[dict]:
        """Parses a Python file and extracts the source code for each function."""
        with open(filepath, "r", encoding="utf-8") as file:
            file_content = file.read()

        try:
            tree = ast.parse(file_content)
        except SyntaxError as e:
            print(f"Skipping {filepath} due to syntax error: {e}")
            return []

        functions = []
        # Walk through the syntax tree looking for function definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Extract the exact lines of code for this specific function
                func_source = ast.get_source_segment(file_content, node)
                functions.append({
                    "file": filepath,
                    "name": node.name,
                    "source_code": func_source
                })
        return functions

    def profile_repository(self) -> list[dict]:
        """Runs the full profile across the directory."""
        all_functions = []
        files = self.get_python_files()
        
        for file in files:
            funcs = self.extract_functions(file)
            all_functions.extend(funcs)
            
        return all_functions

if __name__ == "__main__":
    # Test the profiler on our sample_repo
    profiler = CodeProfiler("sample_repo")
    discovered_functions = profiler.profile_repository()
    
    print(f"🔍 Discovered {len(discovered_functions)} functions in the repository:\n")
    for idx, func in enumerate(discovered_functions):
        print(f"[{idx + 1}] Function: {func['name']} (Found in {func['file']})")
        print(f"Code:\n{func['source_code']}\n{'-'*40}")