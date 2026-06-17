import os
import re
from typing import Dict, Any
from core.logger import system_logger

class FrontendSummaryBuilder:
    """
    Lightweight semantic analyzer to identify UI components, custom hooks,
    and prop interfaces in frontend files.
    """
    IGNORED_DIRS = {"node_modules", ".next", ".nuxt", "build", "dist", ".git", "__pycache__"}
    ALLOWED_EXTS = {".js", ".jsx", ".ts", ".tsx"}
    MAX_FILE_SIZE = 200 * 1024
    
    @staticmethod
    def build(root_path: str) -> Dict[str, Any]:
        summaries = {}
        if not os.path.exists(root_path):
            return summaries
            
        comp_re = re.compile(r'(?:function|const|class)\s+([A-Z][A-Za-z0-9_]*)\s*[:=\(]')
        hook_re = re.compile(r'(?:function|const)\s+(use[A-Z][A-Za-z0-9_]*)\s*[:=\(]')
        props_re = re.compile(r'(?:interface|type)\s+([A-Za-z0-9_]+Props)')
        
        try:
            for current_root, dirs, files in os.walk(root_path):
                dirs[:] = [d for d in dirs if d not in FrontendSummaryBuilder.IGNORED_DIRS and not d.startswith(".")]
                for f in files:
                    if not any(f.endswith(ext) for ext in FrontendSummaryBuilder.ALLOWED_EXTS):
                        continue
                        
                    full_path = os.path.join(current_root, f)
                    rel_path = os.path.relpath(full_path, root_path)
                    
                    if os.path.getsize(full_path) > FrontendSummaryBuilder.MAX_FILE_SIZE:
                        continue
                        
                    try:
                        with open(full_path, "r", encoding="utf-8") as file_obj:
                            content = file_obj.read()
                            
                        components = list(set(comp_re.findall(content)))
                        hooks = list(set(hook_re.findall(content)))
                        props = list(set(props_re.findall(content)))
                        
                        if components or hooks or props:
                            summaries[rel_path] = {
                                "components": components,
                                "hooks": hooks,
                                "props_interfaces": props,
                                "purpose": "UI Component" if components else ("Custom Hook" if hooks else "Frontend Module")
                            }
                    except Exception as e:
                        system_logger.warning(f"[FRONTEND SUMMARY] Failed to parse {rel_path}: {str(e)}")
        except Exception as e:
            system_logger.error(f"[FRONTEND SUMMARY] Catastrophic failure: {str(e)}")
            
        return summaries
