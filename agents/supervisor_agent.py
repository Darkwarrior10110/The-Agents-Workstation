from typing import Any, Dict, List, Optional
from agents.base_agent import BaseAgent, AgentResponse
from core.schema import Task, TaskStatus, Artifact, RepairStrategy
from core.validation_schema import (
    SupervisorReport, ValidationResult, ValidationStatus, 
    BuildResult, RuntimeResult, ErrorCategory
)
from core.validator import ArtifactValidator
from core.failure_classifier import FailureClassifier, FailureCategory
import os

class SupervisorAgent(BaseAgent):
    def __init__(self, name: str = "Supervisor", role: str = "Quality Assurance & Project Lead"):
        super().__init__(name, role)

    def _route_issue(self, category: str, message: str) -> str:
        # Route ALL code generation, validation, and runtime execution issues to the DebugAgent
        # or RuntimeRepairAgent which act as the specialist patch engineers.
        if category in ["runtime", "dependency_failure", "process_crash", "import_error"]:
            return "runtime_repair"
        return "debug"

    def _generate_repair_strategy(self, issue: str, category: str, agent: str) -> RepairStrategy:
        """SYSTEM BRAIN: Analyze failure and formulate an intelligent repair strategy."""
        
        fallback = "If repair fails twice, escalate to human operator or drop feature requirement."
        retry = "Retry generation with exact failing line context."
        steps = []
        
        if category == "syntax" or "SyntaxError" in issue:
            root = "Code contains malformed syntax."
            steps = [
                "Locate the exact syntax error line using AST or traceback.",
                "Generate a targeted FilePatch to fix the indentation/syntax.",
                "Ensure surrounding imports are valid."
            ]
        elif category == "import_error" or category == "dependency_failure":
            root = f"Missing module or dependency: {issue}"
            steps = [
                "Parse the exact missing module name from the error.",
                "Execute 'pip install <module>' via TerminalAgent equivalent.",
                "Append the module to requirements.txt to ensure future stability."
            ]
            retry = "Auto-install dependencies before retry."
        elif category == "integrity" or "React/JSX syntax found in HTML" in issue:
            root = "Framework architecture mismatch. Agent generated React into a static HTML file."
            steps = [
                "Delete React specific code (imports, exports, classNames).",
                "Rewrite the UI using Vanilla JS and standard HTML5/CSS.",
                "Ensure file matches expected architecture."
            ]
            retry = "Force prompt template to STATIC_HTML."
        elif category == "runtime" or category == "process_crash" or "crashed on startup" in issue:
            root = f"Runtime process failed to initialize properly: {issue}"
            steps = [
                "Analyze stderr from the crashed process.",
                "Identify if the failure is due to a FastAPI form/JSON body mismatch (e.g. 422 errors).",
                "Generate patches to fix internal routing, schema, or missing Form(...) imports."
            ]
            fallback = "Revert to last known stable artifact state from cache."
        else:
            root = f"General {category} failure."
            steps = [
                "Analyze the provided error message.",
                "Determine the broken code segment.",
                "Generate a minimal patch."
            ]
            
        return RepairStrategy(
            root_cause=root,
            impacted_agent=agent,
            exact_fix_steps=steps,
            retry_strategy=retry,
            fallback_strategy=fallback
        )

    async def execute(self, task: Task, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        self.log(f"[SUPERVISOR] Initiated full project validation for: {task.goal_id}")
        
        goal_state = context.get("goal_state")
        project_state = context.get("project_state", {})
        project_path = context.get("project_path")
        
        if not goal_state or not project_path:
            return AgentResponse(
                agent_name=self.name,
                status=TaskStatus.FAILED,
                output={"error": "Incomplete context for validation"},
                logs=["VALIDATION ABORTED: Missing goal state or project path."]
            )

        # 1. Artifact Integrity Validation
        all_artifacts = []
        failed_tasks = []
        execution_errors = []
        infra_alerts = []
        executions = []
        
        for t_id, t_info in goal_state.get("tasks", {}).items():
            output_data = t_info.get("output_data") or {}
            
            # Collect Execution Reports for scoring
            if "exit_code" in output_data and "command" in output_data:
                from core.schema import ExecutionReport
                try:
                    executions.append(ExecutionReport(**output_data))
                except Exception:
                    pass

            if t_info.get("status") == TaskStatus.FAILED:
                failed_tasks.append(t_id)
                out_err = str(output_data.get("error", "Unknown execution failure"))
                
                classified = FailureClassifier.classify(out_err)
                
                if classified.category == FailureCategory.PROVIDER_FAILURE:
                    self.log(f"[SUPERVISOR] Provider failure detected on task {t_id}. Blocking code repair.")
                    infra_alerts.append({
                        "task_id": t_id,
                        "reason": classified.reason,
                        "error_message": out_err,
                        "agent": t_info.get('agent_type')
                    })
                    continue # Do not create code repair for provider failure
                
                if classified.category == FailureCategory.CODE_FAILURE:
                    reason = f"Code/Generation failure during {t_info.get('agent_type')} execution."
                    self.log(f"[SUPERVISOR] Detected malformed {t_info.get('agent_type')} artifact.")
                else:
                    reason = classified.reason
                    
                execution_errors.append({
                    "task_id": t_id,
                    "agent": t_info.get('agent_type'),
                    "reason": reason,
                    "error_message": out_err,
                    "target_path": t_info.get('input_data', {}).get('path')
                })
            
            if "artifacts" in output_data:
                for art_dict in output_data["artifacts"]:
                    all_artifacts.append(Artifact(**art_dict))

        # Deduplicate: Only validate the latest artifact for each file path
        latest_artifacts = {}
        for artifact in all_artifacts:
            latest_artifacts[artifact.path] = artifact
        all_artifacts = list(latest_artifacts.values())

        integrity_results = ArtifactValidator.validate_artifacts(all_artifacts)
        
        # Calculate Stability Score
        from core.stability_scorer import StabilityScorer
        from core.schema import PreSaveValidationResult
        # Mock pre-save validations for scoring based on actual integrity checks
        pseudo_validations = []
        for r in integrity_results:
            pseudo_validations.append(PreSaveValidationResult(
                is_valid=(r.status != ValidationStatus.FAILED),
                file_path=r.details.get("path", "unknown"),
                ast_valid=True # Assume ast is fine if not caught by pre-save
            ))
            
        repair_attempts = project_state.get("repair_attempts", 0)
        stability_score = StabilityScorer.calculate(pseudo_validations, executions, repair_attempts, max_repairs=3)
        self.log(f"[SCORING] Overall Stability: {stability_score.overall_score:.2f} | Confidence: {stability_score.confidence_score:.2f}")

        # 2. Structural Validation
        expected_files = [art.path for art in all_artifacts]
        has_python = any(art.path.endswith(".py") for art in all_artifacts)
        has_js_html = any(art.path.endswith((".js", ".jsx", ".html")) for art in all_artifacts)
        
        if not has_python and not has_js_html:
            integrity_results.append(ValidationResult(
                check_name="project_structure_presence",
                status=ValidationStatus.WARNING,
                message="No typical backend or frontend code files found in artifacts.",
                error_category=ErrorCategory.INTEGRITY
            ))

        structure_results = ArtifactValidator.verify_project_structure(
            project_path, 
            expected_files
        )

        validation_results = integrity_results + structure_results
        
        # Strict Supervisor Runtime Gate
        if stability_score.syntax_score < 1.0:
            self.log("[GATE] Rejecting build due to severe syntax/validation failures.", "error")
        if stability_score.execution_score < 0.5:
            self.log("[GATE] Rejecting build due to execution crash.", "error")
            
        # 3. Auto-Repair Foundation (Prepare repair instructions)
        repair_instructions = []
        repair_tasks_data = []
        
        # Skip generating code repair tasks if there are infra alerts blocking the workflow
        if not infra_alerts:
            for r in validation_results:
                if r.status == ValidationStatus.FAILED:
                    cat_val = getattr(r.error_category, "value", "unknown")
                    repair_instructions.append({
                        "issue": r.message,
                        "category": cat_val
                    })
                    assigned_agent = self._route_issue(cat_val, r.message)
                    
                    # Try to map validation failure to a specific task if path matches
                    target_path = r.details.get("path") if r.details else None
                    target_task_id = "unknown"
                    if target_path:
                        for t_id, t_info in goal_state.get("tasks", {}).items():
                            if t_info.get("input_data", {}).get("path") == target_path:
                                target_task_id = t_id
                                break
                                
                    self.log(f"[SUPERVISOR] Detected validation failure: {r.message}")
                    
                    strategy = self._generate_repair_strategy(r.message, cat_val, assigned_agent)

                    repair_tasks_data.append({
                        "goal_id": task.goal_id,
                        "target_task_id": target_task_id,
                        "agent_type": assigned_agent,
                        "task_type": f"repair_{assigned_agent}",
                        "description": f"Repair validation failure: {r.check_name}",
                        "failing_check": r.check_name,
                        "repair_reason": f"Validator caught {cat_val} issue.",
                        "assigned_agent": assigned_agent,
                        "repair_instructions": r.message,
                        "artifact_path": target_path,
                        "input_data": {"path": target_path} if target_path else {},
                        "strategy": strategy.model_dump()
                    })
                    
            for err_dict in execution_errors:
                repair_instructions.append({
                    "issue": err_dict["error_message"],
                    "category": ErrorCategory.RUNTIME.value
                })
                
                assigned_agent = self._route_issue(ErrorCategory.RUNTIME.value, str(err_dict["error_message"]))
                # Override assignment if the task itself failed (e.g. JSON generation failure in frontend)
                if err_dict["agent"] in ["frontend", "backend"]:
                    assigned_agent = err_dict["agent"]
                
                strategy = self._generate_repair_strategy(str(err_dict["error_message"]), ErrorCategory.RUNTIME.value, assigned_agent)
                    
                repair_tasks_data.append({
                    "goal_id": task.goal_id,
                    "target_task_id": err_dict["task_id"],
                    "agent_type": assigned_agent,
                    "task_type": f"repair_{assigned_agent}",
                    "description": f"Repair {err_dict['reason']}",
                    "failing_check": "execution_crash",
                    "repair_reason": err_dict['reason'],
                    "assigned_agent": assigned_agent,
                    "repair_instructions": err_dict['error_message'],
                    "artifact_path": err_dict["target_path"],
                    "input_data": {"path": err_dict["target_path"]} if err_dict["target_path"] else {},
                    "strategy": strategy.model_dump()
                })

        # 4. Aggregate results into a SupervisorReport
        overall_status = ValidationStatus.PASSED
        if any(r.status == ValidationStatus.FAILED for r in validation_results) or failed_tasks:
            overall_status = ValidationStatus.FAILED

        report = SupervisorReport(
            goal_id=task.goal_id,
            project_id=task.goal_id,
            overall_health=overall_status,
            total_tasks=len(goal_state.get("tasks", {})),
            failed_tasks=failed_tasks,
            validation_results=validation_results,
            summary="QA validation completed." if overall_status == ValidationStatus.PASSED else "QA validation detected issues.",
            execution_stats={
                "artifact_count": len(all_artifacts),
                "validation_checks_run": len(validation_results),
                "repair_instructions_prepared": len(repair_instructions),
                "repair_tasks_generated": len(repair_tasks_data),
                "infra_alerts_generated": len(infra_alerts)
            }
        )

        self.log(f"Final QA Health: {overall_status}")
        
        # Band Integration
        try:
            from core.band_service import band_service
            details = report.summary
            if overall_status == ValidationStatus.FAILED:
                details += f" ({len(failed_tasks)} tasks failed, {len(repair_tasks_data)} repair tasks generated)"
            await band_service.publish_supervisor_update(overall_status.name, details)
        except Exception as e:
            self.log(f"Band Integration Error: {str(e)}", "warning")
            
        return AgentResponse(
            agent_name=self.name,
            status=TaskStatus.COMPLETED if overall_status == ValidationStatus.PASSED else TaskStatus.FAILED,
            output={
                **report.model_dump(), 
                "repair_instructions": repair_instructions, 
                "repair_tasks": repair_tasks_data,
                "infra_alerts": infra_alerts
            },
            logs=[report.summary]
        )
