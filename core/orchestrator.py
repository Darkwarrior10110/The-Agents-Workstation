from typing import Any, Dict, List, Optional
from agents.base_agent import BaseAgent, AgentResponse
from agents.planner_agent import PlannerAgent
from agents.backend_agent import BackendAgent
from agents.frontend_agent import FrontendAgent
from agents.terminal_agent import TerminalAgent
from agents.supervisor_agent import SupervisorAgent
from agents.debug_agent import DebugAgent
from core.self_healing.runtime_repair_agent import RuntimeRepairAgent
from core.schema import Task, TaskStatus, GoalState, ProjectState, Artifact, ArtifactType, FilePatch
from core.logger import system_logger
from core.memory import SharedMemory
from fastapi.encoders import jsonable_encoder
import asyncio
import os
from datetime import datetime

class Orchestrator:
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {
            "planner": PlannerAgent(),
            "backend": BackendAgent(),
            "frontend": FrontendAgent(),
            "terminal": TerminalAgent(),
            "supervisor": SupervisorAgent(),
            "debug": DebugAgent(),
            "runtime_repair": RuntimeRepairAgent()
        }
        self.goal_states: Dict[str, GoalState] = {}
        self.project_states: Dict[str, ProjectState] = {}
        self.memory = SharedMemory()
        self.cancel_requested = False

    def terminate_mission(self):
        self.cancel_requested = True

    def _ensure_project_dir(self, goal_id: str) -> str:
        project_path = f"projects/generated_projects/{goal_id}"
        if not os.path.exists(project_path):
            os.makedirs(project_path)
        return project_path

    def _write_artifact(self, root_path: str, artifact: Artifact):
        from core.pre_save_validator import PreSaveValidator
        
        full_path = os.path.join(root_path, artifact.path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        if artifact.artifact_type == ArtifactType.PATCH:
            if not os.path.exists(full_path):
                system_logger.error(f"[PATCH] Cannot patch non-existent file: {full_path}")
                return
            
            with open(full_path, "r") as f:
                content = f.read()
                
            patch_applied = False
            for patch in artifact.patches:
                if patch.search_block in content:
                    content = content.replace(patch.search_block, patch.replace_block)
                    patch_applied = True
                    system_logger.info(f"[PATCH] Applied block to {artifact.path}")
                    # Anti-Loop Memory: Record every applied patch. If the cycle repeats, the LLM will know this patch didn't fix the issue.
                    self.memory.record_failed_patch(artifact.path, patch.search_block, patch.replace_block)
                else:
                    from core.patch_diagnostics import PatchDiagnostics
                    diagnostic = PatchDiagnostics.analyze_search_block_failure(patch.search_block, content)
                    system_logger.error(f"[PATCH] Search block not found in {artifact.path}: {diagnostic}")
                    self.memory.record_failed_patch(artifact.path, patch.search_block, patch.replace_block, reason=diagnostic)
                    raise ValueError(f"Patch application failed: Exact search block not found in {artifact.path}. {diagnostic}")
            
            if patch_applied:
                # Pre-save validation of the patched content
                val_result = PreSaveValidator.validate(artifact.path, content)
                if not val_result.is_valid:
                    error_msg = " | ".join(val_result.errors)
                    system_logger.error(f"[PRE-SAVE VALIDATION] Patch rejected for {artifact.path}: {error_msg}")
                    raise ValueError(f"Pre-save validation failed after patching: {error_msg}")
                    
                with open(full_path, "w") as f:
                    f.write(content)
                self.memory.record_repair(artifact.task_id, f"Patched {artifact.path}", True)
        else:
            # Pre-save validation of new content
            val_result = PreSaveValidator.validate(artifact.path, artifact.content)
            if not val_result.is_valid:
                error_msg = " | ".join(val_result.errors)
                system_logger.error(f"[PRE-SAVE VALIDATION] Artifact rejected for {artifact.path}: {error_msg}")
                raise ValueError(f"Pre-save validation failed for generated artifact: {error_msg}")
                
            if val_result.warnings:
                for warning in val_result.warnings:
                    system_logger.warning(f"[PRE-SAVE WARNING] {artifact.path}: {warning}")
                    
            # Simple overwrite protection
            if os.path.exists(full_path):
                system_logger.warning(f"File already exists, overwriting: {full_path}")
                
            with open(full_path, "w") as f:
                f.write(artifact.content)
            
            system_logger.info(f"Artifact written safely: {full_path}")
            self.memory.add_generated_file(artifact.path, artifact.metadata.get("explanation", ""))
            
            try:
                from core.runtime_state import state_manager
                state_manager.push_event("file_generated", {"path": artifact.path})
            except ImportError:
                pass

    async def process_goal(self, goal_description: str) -> Dict[str, Any]:
        self.cancel_requested = False
        system_logger.info(f"New goal received: {goal_description}")
        
        try:
            from core.runtime_state import state_manager
            state_manager.push_event("goal_started", {"goal": goal_description})
        except ImportError:
            pass
            
        # 1. Planning phase
        state_manager.push_event("agent_status", {"agent": "planner", "status": "Working", "task": "Brainstorming plan for goal"})
        planner = self.agents["planner"]
        plan_response = await planner.execute(goal_description)
        state_manager.push_event("agent_status", {"agent": "planner", "status": "Idle", "task": ""})
        
        if self.cancel_requested:
            return {"status": "failed", "error": "Mission terminated by user."}
        
        if plan_response.status != TaskStatus.COMPLETED:
            return {"status": "failed", "error": "Planning failed"}
            
        goal_state = plan_response.output
        self.goal_states[goal_state.goal_id] = goal_state
        
        # Initialize Project State
        project_path = self._ensure_project_dir(goal_state.goal_id)
        project_state = ProjectState(
            project_id=goal_state.goal_id,
            goal_id=goal_state.goal_id,
            root_path=project_path
        )
        self.project_states[goal_state.goal_id] = project_state
        
        system_logger.info(f"Project initialized at: {project_path}")
        
        # Pipeline Enforcement: Ensure Supervisor task exists
        has_supervisor = any(t.agent_type == "supervisor" for t in goal_state.tasks.values())
        if not has_supervisor:
            import uuid
            from core.schema import TaskPriority, Task
            sup_id = str(uuid.uuid4())
            goal_state.tasks[sup_id] = Task(
                goal_id=goal_state.goal_id,
                agent_type="supervisor",
                task_type="final_validation",
                description="Final QA validation of all generated artifacts.",
                priority=TaskPriority.CRITICAL,
                dependencies=[tid for tid, t in goal_state.tasks.items() if t.agent_type != "supervisor"]
            )
            system_logger.warning("[PIPELINE ENFORCEMENT] Injected missing Supervisor task to guarantee validation pipeline.")

        # Pipeline Enforcement: Ensure Terminal task exists
        has_terminal = any(t.agent_type == "terminal" for t in goal_state.tasks.values())
        if not has_terminal:
            import uuid
            from core.schema import TaskPriority, Task
            term_id = str(uuid.uuid4())
            goal_state.tasks[term_id] = Task(
                goal_id=goal_state.goal_id,
                agent_type="terminal",
                task_type="runtime_validation",
                description="Ensure application runtime works.",
                priority=TaskPriority.HIGH,
                dependencies=[tid for tid, t in goal_state.tasks.items() if t.agent_type in ["frontend", "backend"]],
                input_data={"command": "python3 -m http.server 8000"} # Generic fallback
            )
            # Make sure supervisor depends on this terminal task
            for t in goal_state.tasks.values():
                if t.agent_type == "supervisor" and term_id not in t.dependencies:
                    t.dependencies.append(term_id)
            system_logger.warning("[PIPELINE ENFORCEMENT] Injected missing Terminal validation task to enforce pipeline.")
        
        # 2. Execution phase
        MAX_REPAIR_ATTEMPTS = 3
        repair_cycle = 0
        
        while repair_cycle <= MAX_REPAIR_ATTEMPTS:
            if self.cancel_requested:
                system_logger.warning("Mission terminated by user.")
                break
                
            executed_tasks = set()
            
            while len(executed_tasks) < len(goal_state.tasks):
                if self.cancel_requested:
                    break
                    
                ready_tasks = []
                for t_id, task in goal_state.tasks.items():
                    if t_id in executed_tasks:
                        continue
                    
                    # If task is already completed (from previous cycle) and is not supervisor, skip execution
                    if task.status == TaskStatus.COMPLETED and task.agent_type != "supervisor":
                        executed_tasks.add(t_id)
                        continue
                        
                    # Special Case: Supervisor must run last, regardless of previous failures
                    if task.agent_type == "supervisor":
                        other_tasks = [oid for oid in goal_state.tasks if oid != t_id]
                        if all(ot in executed_tasks for ot in other_tasks):
                            ready_tasks.append((t_id, task))
                        continue
                        
                    # Normal task dependency check (a failed dependency is still 'executed')
                    if all(dep in executed_tasks for dep in task.dependencies):
                        ready_tasks.append((t_id, task))
                
                if not ready_tasks:
                    system_logger.warning("Deadlock or all tasks blocked.")
                    # Force supervisor to run if we are deadlocked
                    supervisor_tasks = [t_id for t_id, task in goal_state.tasks.items() if task.agent_type == "supervisor" and t_id not in executed_tasks]
                    if supervisor_tasks:
                        for t_id in supervisor_tasks:
                            ready_tasks.append((t_id, goal_state.tasks[t_id]))
                    else:
                        break
                    
                for t_id, task in ready_tasks:
                    agent = self.agents.get(task.agent_type)
                    if not agent:
                        system_logger.error(f"Agent {task.agent_type} not found.")
                        task.status = TaskStatus.FAILED
                        executed_tasks.add(t_id)
                        continue
                    
                    system_logger.info(f"[PIPELINE TRACKING] Executing Task {t_id} via {task.agent_type.upper()} AGENT")
                    
                    # Context with project path, safely serialized
                    from core.project_snapshot import ProjectSnapshotGenerator
                    from core.dependency_map import DependencyMapBuilder
                    from core.code_summary import CodeSummaryBuilder
                    from core.supervisor_advisory import SupervisorAdvisoryBuilder
                    from core.frontend_snapshot import FrontendSnapshotGenerator
                    from core.frontend_dependency_map import FrontendDependencyMapBuilder
                    from core.frontend_summary import FrontendSummaryBuilder
                    
                    mem_ctx = self.memory.get_context()
                    snapshot = ProjectSnapshotGenerator.generate_snapshot(project_path)
                    dep_map = DependencyMapBuilder.build(project_path)
                    code_sum = CodeSummaryBuilder.build(project_path)
                    advisory = SupervisorAdvisoryBuilder.build(mem_ctx, snapshot, dep_map, code_sum)
                    frontend_snapshot = FrontendSnapshotGenerator.generate_snapshot(project_path)
                    frontend_dep_map = FrontendDependencyMapBuilder.build(project_path)
                    frontend_code_sum = FrontendSummaryBuilder.build(project_path)

                    context = jsonable_encoder({
                        "goal_state": goal_state,
                        "project_state": project_state,
                        "project_path": project_path,
                        "memory": mem_ctx,
                        "project_snapshot": snapshot,
                        "dependency_map": dep_map,
                        "code_summary": code_sum,
                        "supervisor_advisory": advisory,
                        "frontend_snapshot": frontend_snapshot,
                        "frontend_dependency_map": frontend_dep_map,
                        "frontend_summary": frontend_code_sum
                    })                    
                    try:
                        try:
                            from core.runtime_state import state_manager
                            state_manager.push_event("agent_status", {"agent": task.agent_type, "status": "Working", "task": getattr(task, "description", "")})
                        except ImportError:
                            pass
                            
                        response = await agent.execute(task, context=context)
                        
                        try:
                            from core.runtime_state import state_manager
                            state_manager.push_event("agent_status", {"agent": task.agent_type, "status": "Idle", "task": ""})
                        except ImportError:
                            pass
                        
                        # Handle Artifacts safely
                        if response.status == TaskStatus.COMPLETED and isinstance(response.output, dict):
                            raw_artifacts = response.output.get("artifacts", [])
                            try:
                                for art_data in raw_artifacts:
                                    artifact = Artifact(**art_data)
                                    self._write_artifact(project_path, artifact)
                                    project_state.artifacts.append(artifact)
                            except ValueError as val_err:
                                system_logger.warning(f"[VALIDATION FEEDBACK] {str(val_err)}")
                                response.status = TaskStatus.FAILED
                                response.output["error"] = f"Validation Error: {str(val_err)}"
                            
                            # Handle Supervisor Report
                            if task.agent_type == "supervisor" and "overall_health" in response.output:
                                system_logger.info(f"Project Health Report: {response.output['overall_health']}")
                        
                        # Update task state
                        task.status = response.status
                        task.output_data = response.output
                        task.logs.extend(response.logs)
                        system_logger.info(f"[STATUS MONITORING] Agent {task.agent_type.upper()} completed task {t_id} with status: {task.status.upper()}")
                        
                        if task.status == TaskStatus.FAILED:
                            self.memory.record_failure(task.agent_type, task.input_data.get("path"))
                            
                    except Exception as e:
                        system_logger.error(f"CRITICAL: Agent {task.agent_type} crashed during task {t_id}: {str(e)}")
                        task.status = TaskStatus.FAILED
                        task.output_data = {"error": f"Agent crashed: {str(e)}"}
                        task.logs.append(f"AGENT CRASH: {str(e)}")
                        self.memory.record_failure(task.agent_type, task.input_data.get("path"))
                    finally:
                        task.updated_at = datetime.now()
                        executed_tasks.add(t_id)

            # Check if supervisor passed
            supervisor_task = next((t for t in goal_state.tasks.values() if t.agent_type == "supervisor"), None)
            if supervisor_task and supervisor_task.status == TaskStatus.COMPLETED:
                system_logger.info("[STATUS] Project validation passed and stabilized successfully.")
                project_state.stability_status = "stable"
                project_state.validation_status = "passed"
                break
                
            # If supervisor failed, check for repair tasks OR infra alerts
            if supervisor_task and supervisor_task.output_data:
                infra_alerts = supervisor_task.output_data.get("infra_alerts", [])
                repair_tasks_data = supervisor_task.output_data.get("repair_tasks", [])
                
                if not repair_tasks_data and not infra_alerts:
                    break
                    
                repair_cycle += 1
                if repair_cycle > MAX_REPAIR_ATTEMPTS:
                    system_logger.error("[STATUS] Max repair/retry attempts reached. Stopping auto-repair.")
                    project_state.stability_status = "unstable"
                    if infra_alerts:
                        project_state.stability_status = "blocked"
                    break
                    
                if infra_alerts:
                    backoff_seconds = 2 ** repair_cycle
                    system_logger.warning(f"[INFRA] Provider failure detected. Initiating {backoff_seconds}s backoff.")
                    await asyncio.sleep(backoff_seconds)
                    
                    # Reset blocked/failed tasks caused by infra to pending
                    for t_id, task in goal_state.tasks.items():
                        if any(alert.get("task_id") == t_id for alert in infra_alerts):
                            task.status = TaskStatus.PENDING
                            task.output_data = None
                            task.repair_attempts += 1
                else:
                    system_logger.info(f"[REPAIR] --- INITIATING REPAIR CYCLE {repair_cycle} ---")
                    project_state.repair_attempts = repair_cycle
                    
                    from core.schema import RepairTask
                    for r_data in repair_tasks_data:
                        repair_task = RepairTask(**r_data)
                        agent = self.agents.get(repair_task.assigned_agent)
                        if not agent: continue
                        
                        target_id = repair_task.target_task_id
                        if target_id in goal_state.tasks:
                            goal_state.tasks[target_id].repair_attempts += 1
                            goal_state.tasks[target_id].last_failure_reason = repair_task.repair_reason
                        
                        system_logger.info(f"[REPAIR] Creating repair task for {repair_task.assigned_agent} to fix: {repair_task.failing_check}")
                        try:
                            from core.project_snapshot import ProjectSnapshotGenerator
                            from core.dependency_map import DependencyMapBuilder
                            from core.code_summary import CodeSummaryBuilder
                            from core.supervisor_advisory import SupervisorAdvisoryBuilder
                            from core.frontend_snapshot import FrontendSnapshotGenerator
                            from core.frontend_dependency_map import FrontendDependencyMapBuilder
                            from core.frontend_summary import FrontendSummaryBuilder
                            mem_ctx = self.memory.get_context()
                            snapshot = ProjectSnapshotGenerator.generate_snapshot(project_path)
                            dep_map = DependencyMapBuilder.build(project_path)
                            code_sum = CodeSummaryBuilder.build(project_path)
                            advisory = SupervisorAdvisoryBuilder.build(mem_ctx, snapshot, dep_map, code_sum)
                            frontend_snapshot = FrontendSnapshotGenerator.generate_snapshot(project_path)
                            frontend_dep_map = FrontendDependencyMapBuilder.build(project_path)
                            frontend_code_sum = FrontendSummaryBuilder.build(project_path)
                            
                            context = jsonable_encoder({
                                "goal_state": goal_state,
                                "project_state": project_state,
                                "project_path": project_path,
                                "repair_mode": True,
                                "memory": mem_ctx,
                                "project_snapshot": snapshot,
                                "dependency_map": dep_map,
                                "code_summary": code_sum,
                                "supervisor_advisory": advisory,
                                "frontend_snapshot": frontend_snapshot,
                                "frontend_dependency_map": frontend_dep_map,
                                "frontend_summary": frontend_code_sum
                            })
                            
                            try:
                                from core.runtime_state import state_manager
                                state_manager.push_event("agent_status", {"agent": repair_task.assigned_agent, "status": "Working", "task": getattr(repair_task, "description", "")})
                                state_manager.push_event("increment_telemetry", {"key": "repair_attempts"})
                            except ImportError:
                                pass
                                
                            r_response = await agent.execute(repair_task, context=context)
                            
                            try:
                                from core.runtime_state import state_manager
                                state_manager.push_event("agent_status", {"agent": repair_task.assigned_agent, "status": "Idle", "task": ""})
                            except ImportError:
                                pass
                            
                            if r_response.status == TaskStatus.COMPLETED and isinstance(r_response.output, dict):
                                raw_artifacts = r_response.output.get("artifacts", [])
                                try:
                                    for art_data in raw_artifacts:
                                        artifact = Artifact(**art_data)
                                        full_path = os.path.join(project_path, artifact.path)
                                        import shutil
                                        if os.path.exists(full_path):
                                            shutil.copy(full_path, full_path + f".bak_repair_{repair_cycle}")
                                        self._write_artifact(project_path, artifact)
                                        project_state.artifacts.append(artifact)
                                    
                                    if target_id in goal_state.tasks:
                                        goal_state.tasks[target_id].repaired_by = repair_task.assigned_agent
                                        goal_state.tasks[target_id].repair_history.append({
                                            "cycle": repair_cycle,
                                            "reason": repair_task.repair_reason,
                                            "status": "repaired"
                                        })
                                except ValueError as val_err:
                                    system_logger.warning(f"[REPAIR VALIDATION FEEDBACK] {str(val_err)}")
                                    r_response.status = TaskStatus.FAILED
                                    r_response.output["error"] = f"Validation Error: {str(val_err)}"
                                    if target_id in goal_state.tasks:
                                        goal_state.tasks[target_id].last_failure_reason = f"Patch Validation Error: {str(val_err)}"
                        except Exception as e:
                            system_logger.error(f"[REPAIR] Repair task failed: {str(e)}")
                
                # Reset supervisor to run again
                system_logger.info("[VALIDATOR] Re-running validation after repair/backoff")
                supervisor_task.status = TaskStatus.PENDING
                supervisor_task.output_data = None
            else:
                break

        # Final status check
        if any(t.status == TaskStatus.FAILED for t in goal_state.tasks.values()):
            goal_state.status = TaskStatus.FAILED
            project_state.status = "failed"
            project_state.validation_status = "failed"
            project_state.stability_status = "unstable"
        else:
            goal_state.status = TaskStatus.COMPLETED
            project_state.status = "completed"
            project_state.validation_status = "passed"
            project_state.stability_status = "stable"
            
        return {
            "goal_state": goal_state.dict(),
            "project_state": project_state.dict()
        }
