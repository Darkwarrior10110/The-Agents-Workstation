import re
from core.schema import TracebackAnalysis
from core.logger import system_logger

class TracebackAnalyzer:
    """
    Analyzes Python tracebacks and stderr to extract the root cause,
    failing file, line number, and error category.
    """
    
    @staticmethod
    def analyze(stderr: str, stdout: str) -> TracebackAnalysis:
        combined_logs = stderr + "\n" + stdout
        
        # Defaults
        error_type = "UnknownError"
        error_message = "An unknown error occurred during execution."
        file_path = None
        line_number = None
        failing_code = None
        is_syntax_error = False
        
        # 1. Parse Python Traceback
        # Look for the last File "...", line X, in ...
        file_line_pattern = r'File "([^"]+)", line (\d+)'
        matches = re.findall(file_line_pattern, combined_logs)
        
        if matches:
            # Usually the last match is the most relevant in a traceback
            # unless it's deep in a library. We try to find the last local project file.
            for match in reversed(matches):
                if "/usr/lib" not in match[0] and "site-packages" not in match[0]:
                    file_path = match[0]
                    line_number = int(match[1])
                    break
            
            # If all were library files, just take the last one
            if not file_path:
                file_path = matches[-1][0]
                line_number = int(matches[-1][1])

        # 2. Extract Error Type and Message
        # Python tracebacks end with "ErrorType: error message"
        error_pattern = r'^([A-Z][a-zA-Z]+Error|Exception):\s*(.*)$'
        for line in reversed(combined_logs.splitlines()):
            err_match = re.match(error_pattern, line.strip())
            if err_match:
                error_type = err_match.group(1)
                error_message = err_match.group(2)
                break
                
        if error_type in ["SyntaxError", "IndentationError", "TabError"]:
            is_syntax_error = True
            
        # 3. Classify Root Cause
        root_cause = "runtime_crash"
        if is_syntax_error:
            root_cause = "syntax_error"
        elif error_type == "ImportError" or error_type == "ModuleNotFoundError":
            root_cause = "import_error"
        elif "No module named" in error_message:
            root_cause = "dependency_error"
        elif error_type in ["KeyError", "AttributeError", "TypeError", "ValueError"]:
            root_cause = "logic_error"
        elif "address already in use" in error_message.lower():
            root_cause = "port_conflict"
            
        # 4. Extract failing code line (often printed after the File "..." line)
        if line_number:
            lines = combined_logs.splitlines()
            for i, line in enumerate(lines):
                if f'File "{file_path}", line {line_number}' in line:
                    if i + 1 < len(lines):
                        failing_code = lines[i + 1].strip()
                    break

        suggested_fix = TracebackAnalyzer._suggest_fix(root_cause, error_type, error_message, failing_code)

        return TracebackAnalysis(
            error_type=error_type,
            error_message=error_message,
            file_path=file_path,
            line_number=line_number,
            failing_code=failing_code,
            root_cause=root_cause,
            suggested_fix=suggested_fix,
            is_syntax_error=is_syntax_error
        )

    @staticmethod
    def _suggest_fix(root_cause: str, error_type: str, error_message: str, failing_code: str = None) -> str:
        if root_cause == "syntax_error":
            return "Check indentation, brackets, and quotes near the failing line. Ensure Python 3 valid syntax."
        elif root_cause == "dependency_error":
            return f"Add the missing package to requirements.txt and run pip install. Error: {error_message}"
        elif root_cause == "import_error":
            return "Check if the module exists locally or if the import path is correct relative to the project root."
        elif root_cause == "logic_error":
            return f"A runtime {error_type} occurred. Check variable types and existence of attributes/keys."
        return "Analyze the traceback and implement a fix to address the crash."
