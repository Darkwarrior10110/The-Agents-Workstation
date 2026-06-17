import os
from typing import Dict, Any, List
from core.logger import system_logger

class SupervisorAdvisoryBuilder:
    """
    Lightweight deterministic helper to produce a read-only architectural advisory 
    based on the current state, memory, and code summaries.
    """

    @staticmethod
    def build(memory_ctx: Dict[str, Any], snapshot: Dict[str, Any], dep_map: Dict[str, Any], code_sum: Dict[str, Any]) -> List[str]:
        advisories = []
        try:
            # 1. Unstable Files Warning
            unstable_files = memory_ctx.get("unstable_files", {})
            for f_path, count in unstable_files.items():
                if count > 1:
                    advisories.append(f"WARNING: The file '{f_path}' has failed validation/execution {count} times. Exercise extreme caution and do not repeat previous patterns.")

            # 2. Re-use existing components (Code Summary)
            if code_sum:
                exports_info = []
                for file_path, data in code_sum.items():
                    exports = data.get("exports", [])
                    if exports:
                        exports_info.append(f"{file_path} exports: {', '.join(exports)}")
                if exports_info:
                    advisories.append("ARCHITECTURAL REUSE: " + " | ".join(exports_info) + ". Reuse these instead of duplicating.")
            
            # 3. Failed Patches Hint
            failed_patches = memory_ctx.get("failed_patches", {})
            if failed_patches:
                problematic_files = list(failed_patches.keys())
                advisories.append(f"REPAIR HISTORY: Patches have repeatedly failed on {', '.join(problematic_files)}. Carefully review diagnostic messages before attempting new patches.")
            
            if not advisories:
                advisories.append("No specific architectural warnings at this time. Proceed with standard generation.")
                
        except Exception as e:
            system_logger.error(f"[ADVISORY BUILDER] Error generating advisory: {str(e)}")
            return ["Advisory generation failed. Proceed with caution."]
            
        return advisories
