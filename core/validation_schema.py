from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ValidationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"

class ErrorCategory(str, Enum):
    SYNTAX = "syntax"
    DEPENDENCY = "dependency"
    BUILD = "build"
    RUNTIME = "runtime"
    SECURITY = "security"
    INTEGRITY = "integrity"
    UNKNOWN = "unknown"

class ExecutionResult(BaseModel):
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    timestamp: datetime = Field(default_factory=datetime.now)

class ValidationResult(BaseModel):
    check_name: str
    status: ValidationStatus
    message: str
    error_category: Optional[ErrorCategory] = None
    details: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.now)

class BuildResult(BaseModel):
    component: str  # e.g., "frontend", "backend"
    status: ValidationStatus
    execution: Optional[ExecutionResult] = None
    errors: List[str] = []

class RuntimeResult(BaseModel):
    component: str
    status: ValidationStatus
    logs: List[str] = []
    ports_active: List[int] = []

class SupervisorReport(BaseModel):
    goal_id: str
    project_id: str
    overall_health: ValidationStatus
    total_tasks: int
    failed_tasks: List[str]
    validation_results: List[ValidationResult] = []
    build_results: List[BuildResult] = []
    runtime_results: List[RuntimeResult] = []
    execution_stats: Dict[str, Any] = {}
    summary: str
    created_at: datetime = Field(default_factory=datetime.now)
