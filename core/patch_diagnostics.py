import re

class PatchDiagnostics:
    """
    Lightweight utility to generate actionable diagnostics when a patch fails to apply.
    """
    @staticmethod
    def analyze_search_block_failure(search_block: str, file_content: str) -> str:
        if not search_block or not search_block.strip():
            return "Diagnostic: Search block was empty."
        
        # Check for whitespace-agnostic match
        def normalize(text):
            return re.sub(r'\s+', '', text)
        
        if normalize(search_block) in normalize(file_content):
            return "Diagnostic: Code exists in the file, but whitespace or indentation differs. Ensure exact matching of leading spaces and newlines."
        
        # Check if partial match exists (first line)
        lines = [line for line in search_block.splitlines() if line.strip()]
        if lines and lines[0].strip() in file_content:
            return "Diagnostic: First line of search block matched, but subsequent lines diverged. Check for partial modifications or hallucinated lines."
            
        return "Diagnostic: The search block was not found at all. You may be hallucinating code that does not exist in the current file state."
