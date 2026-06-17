import ast
import json
import re
from typing import List
from core.schema import PreSaveValidationResult
from core.logger import system_logger

class PreSaveValidator:
    """
    Validates files before they are written to disk.
    Ensures syntax correctness, formatting, and prevents corrupted code.
    """
    
    FORBIDDEN_PATTERNS = [
        r"rm\s+-rf",
        r"sudo\s",
        r"chmod\s+777",
        r"eval\(",
        r"exec\("
    ]

    @staticmethod
    def validate(file_path: str, content: str) -> PreSaveValidationResult:
        result = PreSaveValidationResult(is_valid=True, file_path=file_path)
        
        # 1. Encoding & Empty check
        if not content or len(content.strip()) == 0:
            result.is_valid = False
            result.errors.append("File content is empty.")
            return result
            
        try:
            content.encode('utf-8')
        except UnicodeEncodeError:
            result.is_valid = False
            result.errors.append("Invalid UTF-8 encoding detected.")
            return result

        # 2. File size check (prevent massive hallucinated files)
        if len(content) > 1024 * 1024 * 5: # 5MB limit
            result.is_valid = False
            result.errors.append("File size exceeds 5MB limit.")
            return result

        # 3. Forbidden patterns (Security)
        for pattern in PreSaveValidator.FORBIDDEN_PATTERNS:
            if re.search(pattern, content):
                result.is_valid = False
                result.errors.append(f"Forbidden pattern detected: {pattern}")
        
        # 4. Corrupted escaping / malformed quotes
        if "\\n" in content and "\\\\n" not in content and ".py" not in file_path:
            # Simple heuristic, often AI escapes newlines literally inside files
            # This is tricky as actual code might have \n, we will just warn
            if content.count("\\n") > 20:
                result.warnings.append("High number of literal '\\n' detected, possible escaping corruption.")

        # 5. Syntax validation based on extension
        if file_path.endswith('.py'):
            PreSaveValidator._validate_python(content, result)
        elif file_path.endswith('.json'):
            PreSaveValidator._validate_json(content, result)
        elif file_path.endswith(('.html', '.js', '.css', '.jsx', '.ts', '.tsx')):
            PreSaveValidator._validate_frontend(content, result)
            
        return result

    @staticmethod
    def _validate_python(content: str, result: PreSaveValidationResult):
        try:
            ast.parse(content)
            result.ast_valid = True
        except SyntaxError as e:
            result.is_valid = False
            result.ast_valid = False
            result.errors.append(f"Python Syntax Error: {str(e)} at line {e.lineno}")
        except Exception as e:
            result.is_valid = False
            result.ast_valid = False
            result.errors.append(f"Failed to parse Python code: {str(e)}")

        # Check for uncompleted blocks or missing imports
        if "pass" in content and "def " in content:
            result.warnings.append("Code contains 'pass' blocks. Might be incomplete.")

    @staticmethod
    def _validate_json(content: str, result: PreSaveValidationResult):
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            result.is_valid = False
            result.errors.append(f"JSON Formatting Error: {str(e)}")

    @staticmethod
    def _validate_frontend(content: str, result: PreSaveValidationResult):
        # Basic checks for frontend files
        if content.count("<") != content.count(">"):
            result.warnings.append("Mismatched angle brackets in frontend file.")
        if content.count("{") != content.count("}"):
            result.warnings.append("Mismatched curly braces in frontend file.")
