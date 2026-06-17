from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

class TaskPriority(int, Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class ArtifactType(str, Enum):
    FILE = "file"
    DIRECTORY = "directory"
    CONFIG = "config"
    PATCH = "patch"

class FilePatch(BaseModel):
    path: str
    search_block: str
    replace_block: str
    explanation: str = ""

class Artifact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    path: str
    artifact_type: ArtifactType
    content: str
    patches: List[FilePatch] = []
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.now)

class StabilityScore(BaseModel):
    syntax_score: float = 1.0
    execution_score: float = 1.0
    dependency_score: float = 1.0
    repair_success_score: float = 1.0
    confidence_score: float = 1.0
    overall_score: float = 1.0

class TracebackAnalysis(BaseModel):
    error_type: str
    error_message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    failing_code: Optional[str] = None
    root_cause: str
    suggested_fix: str
    is_syntax_error: bool = False

class ExecutionReport(BaseModel):
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    traceback_analysis: Optional[TracebackAnalysis] = None
    is_stable: bool = False

class PreSaveValidationResult(BaseModel):
    is_valid: bool
    file_path: str
    errors: List[str] = []
    warnings: List[str] = []
    ast_valid: bool = True

class ProjectState(BaseModel):
    project_id: str
    goal_id: str
    root_path: str
    artifacts: List[Artifact] = []
    status: str = "initializing"
    validation_status: str = "pending"
    stability_status: str = "unstable"
    repair_attempts: int = 0
    stability_score: StabilityScore = Field(default_factory=StabilityScore)

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal_id: str
    agent_type: str
    task_type: str
    description: str
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: List[str] = []
    input_data: Dict[str, Any] = {}
    output_data: Optional[Dict[str, Any]] = None
    status: TaskStatus = TaskStatus.PENDING
    logs: List[str] = []
    repair_attempts: int = 0
    repaired_by: Optional[str] = None
    repair_history: List[Dict[str, Any]] = []
    last_failure_reason: Optional[str] = None
    active_port: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class RepairStrategy(BaseModel):
    root_cause: str
    impacted_agent: str
    exact_fix_steps: List[str]
    retry_strategy: str
    fallback_strategy: str

class RepairTask(Task):
    issue_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_task_id: str
    failing_check: str
    assigned_agent: str
    repair_reason: str
    artifact_path: Optional[str] = None
    repair_instructions: str
    validation_context: Dict[str, Any] = {}
    strategy: Optional[RepairStrategy] = None

class GoalState(BaseModel):
    goal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_goal: str
    tasks: Dict[str, Task] = {}
    status: TaskStatus = TaskStatus.PENDING
    overall_summary: Optional[str] = None
    metadata: Dict[str, Any] = {}
