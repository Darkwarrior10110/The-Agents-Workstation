from typing import Any, Dict, List, Optional
from agents.base_agent import BaseAgent, AgentResponse
from core.schema import Task, TaskStatus, Artifact, ArtifactType
from core.gemini_client import GeminiClient
from core.prompts import FRONTEND_GENERATION_PROMPT, STATIC_FRONTEND_PROMPT, REPAIR_GENERATION_PROMPT
from core.cache_manager import ArtifactCache
import json
import os

class FrontendAgent(BaseAgent):
    def __init__(self, name: str = "Frontend", role: str = "Senior Frontend Engineer"):
        super().__init__(name, role)
        self.client = GeminiClient()
        self.cache = ArtifactCache()
        self.max_file_size = 150 * 1024  # 150KB safeguard for frontend

    async def execute(self, task: Task, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        self.log(f"Frontend generating code for: {task.description}")
        
        is_repair = getattr(task, "repair_instructions", None) is not None
        
        # Check cache if not repairing
        if not is_repair:
            cached_art = self.cache.get(task.description, task.input_data)
            if cached_art:
                self.log("Using cached artifact for frontend.")
                return AgentResponse(
                    agent_name=self.name,
                    status=TaskStatus.COMPLETED,
                    output={"artifacts": [cached_art.model_dump()]},
                    logs=[f"Restored {cached_art.path} from cache."]
                )
                
        framework = task.input_data.get("framework", "react")
        target_path = task.input_data.get("path")
        
        if framework == "static_html":
            target_path = target_path or "app/static/index.html"
            if target_path.endswith((".js", ".jsx")):
                target_path = target_path.replace(".jsx", ".html").replace(".js", ".html")
            prompt_template = STATIC_FRONTEND_PROMPT
            lang_meta = "html"
        else:
            target_path = target_path or "frontend/src/App.js"
            if target_path.endswith(".html"):
                target_path = target_path.replace(".html", ".js")
            prompt_template = FRONTEND_GENERATION_PROMPT
            lang_meta = "javascript"

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
            prompt = prompt_template.format(
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
                    "language": lang_meta,
                    "framework": framework,
                    "explanation": data.get("explanation"),
                    "dependencies": data.get("dependencies", [])
                }
            )
            
            # Save successful generation to cache
            if not is_repair:
                self.cache.set(task.description, task.input_data, artifact)
            
            self.log(f"Successfully generated frontend artifact: {target_path}")
            return AgentResponse(
                agent_name=self.name,
                status=TaskStatus.COMPLETED,
                output={"artifacts": [artifact.model_dump()]},
                logs=[f"Generated {target_path} using Gemini."]
            )

        except Exception as e:
            self.log(f"Frontend Generation Error: {str(e)}", "error")
            return AgentResponse(
                agent_name=self.name,
                status=TaskStatus.FAILED,
                output={"error": str(e)},
                logs=[f"FAILED to generate frontend code: {str(e)}"]
            )
