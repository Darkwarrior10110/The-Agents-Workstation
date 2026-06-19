from typing import Any, Dict, List, Optional
from agents.base_agent import BaseAgent, AgentResponse
from core.schema import Task, TaskStatus, Artifact, ArtifactType
from core.gemini_client import GeminiClient
from core.prompts import BACKEND_GENERATION_PROMPT, REPAIR_GENERATION_PROMPT
from core.cache_manager import ArtifactCache
import json
import os

class BackendAgent(BaseAgent):
    def __init__(self, name: str = "Backend", role: str = "Senior Backend Engineer"):
        super().__init__(name, role)
        self.client = GeminiClient()
        self.cache = ArtifactCache()
        self.max_file_size = 100 * 1024  # 100KB safeguard

    async def execute(self, task: Task, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        self.log(f"Backend generating code for: {task.description}")
        
        # Band Integration: Receive work
        try:
            from core.band_service import band_service
            import asyncio
            asyncio.create_task(band_service.publish_backend_start(task.description))
        except Exception as e:
            self.log(f"Band Integration Error: {str(e)}", "warning")
        
        is_repair = getattr(task, "repair_instructions", None) is not None
        
        # Check cache if not repairing
        if not is_repair:
            cached_art = self.cache.get(task.description, task.input_data)
            if cached_art:
                self.log("Using cached artifact for backend.")
                return AgentResponse(
                    agent_name=self.name,
                    status=TaskStatus.COMPLETED,
                    output={"artifacts": [cached_art.dict()]},
                    logs=[f"Restored {cached_art.path} from cache."]
                )
        
        target_path = task.input_data.get("path", "backend/main.py")
        
        if is_repair:
            broken_code = ""
            full_path = os.path.join(context.get("project_path", ""), target_path) if context else ""
            if full_path and os.path.exists(full_path):
                with open(full_path, "r") as f:
                    broken_code = f.read()
                    
            prompt = REPAIR_GENERATION_PROMPT.format(
                path=target_path,
                failing_check=getattr(task, "failing_check", "Validation failure"),
                repair_reason=getattr(task, "repair_reason", "Unknown"),
                repair_instructions=task.repair_instructions,
                context=json.dumps(context or {}, default=str),
                broken_code=broken_code
            )
        else:
            prompt = BACKEND_GENERATION_PROMPT.format(
                description=task.description,
                path=target_path,
                context=json.dumps(context or {}, default=str)
            )
        
        try:
            raw_response = await self.client.generate_content(prompt)
            data = json.loads(raw_response)
            
            code = data.get("code", "")
            if not code or len(code) > self.max_file_size:
                raise ValueError("Generated code is empty or exceeds size limits.")

            artifact = Artifact(
                task_id=task.id,
                path=target_path,
                artifact_type=ArtifactType.FILE,
                content=code,
                metadata={
                    "language": "python",
                    "framework": "fastapi",
                    "explanation": data.get("explanation"),
                    "requirements": data.get("requirements", [])
                }
            )
            
            # Save successful generation to cache
            if not is_repair:
                self.cache.set(task.description, task.input_data, artifact)
            
            self.log(f"Successfully generated backend artifact: {target_path}")
            
            # Band Integration: Complete work
            try:
                from core.band_service import band_service
                import asyncio
                asyncio.create_task(band_service.publish_backend_complete(target_path))
            except Exception as e:
                self.log(f"Band Integration Error: {str(e)}", "warning")
                
            return AgentResponse(
                agent_name=self.name,
                status=TaskStatus.COMPLETED,
                output={"artifacts": [artifact.dict()]},
                logs=[f"Generated {target_path} using Gemini."]
            )

        except Exception as e:
            self.log(f"Backend Generation Error: {str(e)}", "error")
            return AgentResponse(
                agent_name=self.name,
                status=TaskStatus.FAILED,
                output={"error": str(e)},
                logs=[f"FAILED to generate backend code: {str(e)}"]
            )
