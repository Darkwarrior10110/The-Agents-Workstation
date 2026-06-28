from typing import Any, Dict, Optional
from agents.base_agent import BaseAgent, AgentResponse
from core.schema import Task, TaskStatus, Artifact, ArtifactType, FilePatch
from core.gemini_client import GeminiClient
from core.prompts import DEBUG_PATCH_PROMPT
from core.traceback_analyzer import TracebackAnalyzer
from core.execution_tester import ExecutionTester
from core.logger import system_logger
import json
import os
import re

class RuntimeRepairAgent(BaseAgent):
    def __init__(self, name: str = "RuntimeRepair", role: str = "Autonomous Runtime Repair Engine"):
        super().__init__(name, role)
        self.client = GeminiClient()

    async def execute(self, task: Task, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        self.log(f"RuntimeRepairAgent analyzing execution failure for task {task.target_task_id}")
        
        project_path = context.get("project_path", "") if context else ""
        repair_instructions = getattr(task, "repair_instructions", "")
        
        # 1. Parse stderr / Traceback
        analysis = TracebackAnalyzer.analyze(repair_instructions, "")
        
        # 2. Detect and Auto-install missing dependencies
        if analysis.root_cause == "dependency_error":
            missing_pkg = self._extract_missing_package(analysis.error_message)
            if missing_pkg:
                self.log(f"Auto-installing missing dependency: {missing_pkg}")
                # Auto-install
                import asyncio
                await asyncio.to_thread(ExecutionTester.run_safe, f"pip install {missing_pkg}", project_path)
                
                # Update requirements.txt
                req_path = os.path.join(project_path, "requirements.txt")
                if os.path.exists(req_path):
                    with open(req_path, "a") as f:
                        f.write(f"\n{missing_pkg}\n")
                        
                return AgentResponse(
                    agent_name=self.name,
                    status=TaskStatus.COMPLETED,
                    output={"action": "installed_dependency", "package": missing_pkg},
                    logs=[f"Auto-healed missing dependency: {missing_pkg}"]
                )

        # 3. Handle Code Patches (FastAPI form/body mismatch, import paths, etc.)
        target_path = task.input_data.get("path") or getattr(task, "artifact_path", "")
        if not target_path and analysis.file_path:
            # Try to relative-ize the path
            if project_path in analysis.file_path:
                target_path = os.path.relpath(analysis.file_path, project_path)
            else:
                target_path = os.path.basename(analysis.file_path)

        if not target_path:
            return AgentResponse(
                agent_name=self.name,
                status=TaskStatus.FAILED,
                output={"error": "Could not determine target path for repair."},
                logs=["No target path identified for patching."]
            )

        broken_code = ""
        full_path = os.path.join(project_path, target_path)
        
        if os.path.exists(full_path):
            with open(full_path, "r") as f:
                broken_code = f.read()

        enhanced_instructions = repair_instructions
        enhanced_instructions += f"\n[AUTO-ANALYSIS] Root Cause: {analysis.root_cause}. Suggestion: {analysis.suggested_fix}"
        if analysis.line_number:
            enhanced_instructions += f"\n[AUTO-ANALYSIS] Focus on Line: {analysis.line_number}"
            
        # Detect FastAPI mismatch specifically
        if "422" in enhanced_instructions or "Unprocessable Entity" in enhanced_instructions:
            enhanced_instructions += "\n[HEURISTIC] Possible FastAPI Form vs JSON body mismatch. Ensure endpoint uses `Form(...)`."

        mem = context.get("memory", {}) if context else {}
        failed_patches = mem.get("failed_patches", {}).get(target_path, [])
        if failed_patches:
            enhanced_instructions += "\n\n[ANTI-LOOP MEMORY] You have previously attempted the following patches which DID NOT resolve the issue. DO NOT suggest these exact patches again:\n"
            for idx, fp in enumerate(failed_patches):
                reason = fp.get('reason', 'Applied but failed validation/runtime')
                enhanced_instructions += f"--- Failed Attempt {idx+1} | {reason} ---\nReplaced:\n{fp.get('search_block')}\n\nWith:\n{fp.get('replace_block')}\n\n"

        prompt = DEBUG_PATCH_PROMPT.format(
            path=target_path,
            failing_check=getattr(task, "failing_check", "Runtime Execution Crash"),
            repair_reason=getattr(task, "repair_reason", analysis.root_cause),
            repair_instructions=enhanced_instructions,
            context=json.dumps(context or {}, default=str),
            broken_code=broken_code
        )
        
        try:
            raw_response = await self.client.generate_content(prompt)
            data = json.loads(raw_response)
            
            patches_data = data.get("patches", [])
            
            # Confidence Scoring
            repair_confidence = 0.9 if analysis.line_number and patches_data else 0.5
            
            artifact = Artifact(
                task_id=task.id,
                path=target_path,
                artifact_type=ArtifactType.PATCH,
                content="", 
                patches=[FilePatch(**p) for p in patches_data],
                metadata={
                    "language": "diff",
                    "explanation": "Runtime patches generated",
                    "repair_confidence": repair_confidence
                }
            )
            
            return AgentResponse(
                agent_name=self.name,
                status=TaskStatus.COMPLETED,
                output={"artifacts": [artifact.model_dump()], "repair_confidence": repair_confidence},
                logs=[f"RuntimeRepairAgent emitted patches for {target_path}."]
            )

        except Exception as e:
            self.log(f"RuntimeRepairAgent Generation Error: {str(e)}", "error")
            return AgentResponse(
                agent_name=self.name,
                status=TaskStatus.FAILED,
                output={"error": str(e)},
                logs=[f"FAILED to generate runtime patches: {str(e)}"]
            )

    def _extract_missing_package(self, error_message: str) -> Optional[str]:
        match = re.search(r"No module named '([^']+)'", error_message)
        if match:
            return match.group(1)
        return None
