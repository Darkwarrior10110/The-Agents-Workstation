import pytest
from datetime import datetime
from core.schema import (
    TaskStatus, TaskPriority, ArtifactType, FilePatch, Artifact,
    StabilityScore, TracebackAnalysis, ExecutionReport, PreSaveValidationResult,
    ProjectState, Task, RepairStrategy, RepairTask, GoalState
)


class TestEnums:
    def test_task_status_values(self):
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.IN_PROGRESS == "in_progress"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"
        assert TaskStatus.BLOCKED == "blocked"

    def test_task_priority_values(self):
        assert TaskPriority.LOW == 1
        assert TaskPriority.MEDIUM == 2
        assert TaskPriority.HIGH == 3
        assert TaskPriority.CRITICAL == 4

    def test_artifact_type_values(self):
        assert ArtifactType.FILE == "file"
        assert ArtifactType.DIRECTORY == "directory"
        assert ArtifactType.CONFIG == "config"
        assert ArtifactType.PATCH == "patch"


class TestFilePatch:
    def test_minimal_creation(self):
        patch = FilePatch(path="test.py", search_block="old", replace_block="new")
        assert patch.path == "test.py"
        assert patch.search_block == "old"
        assert patch.replace_block == "new"
        assert patch.explanation == ""

    def test_full_creation(self):
        patch = FilePatch(path="test.py", search_block="old", replace_block="new", explanation="fix bug")
        assert patch.explanation == "fix bug"


class TestArtifact:
    def test_minimal_creation(self):
        art = Artifact(task_id="task1", path="test.py", artifact_type=ArtifactType.FILE, content="print('hello')")
        assert art.task_id == "task1"
        assert art.path == "test.py"
        assert art.content == "print('hello')"
        assert art.patches == []
        assert art.metadata == {}

    def test_with_patches(self):
        patch = FilePatch(path="test.py", search_block="old", replace_block="new")
        art = Artifact(
            task_id="task1", path="test.py", artifact_type=ArtifactType.PATCH,
            content="", patches=[patch]
        )
        assert len(art.patches) == 1
        assert art.patches[0].search_block == "old"

    def test_auto_id(self):
        art1 = Artifact(task_id="t1", path="a.py", artifact_type=ArtifactType.FILE, content="x")
        art2 = Artifact(task_id="t2", path="b.py", artifact_type=ArtifactType.FILE, content="y")
        assert art1.id != art2.id

    def test_auto_timestamp(self):
        art = Artifact(task_id="t1", path="a.py", artifact_type=ArtifactType.FILE, content="x")
        assert isinstance(art.created_at, datetime)


class TestStabilityScore:
    def test_default_values(self):
        score = StabilityScore()
        assert score.syntax_score == 1.0
        assert score.execution_score == 1.0
        assert score.dependency_score == 1.0
        assert score.repair_success_score == 1.0
        assert score.confidence_score == 1.0
        assert score.overall_score == 1.0

    def test_custom_values(self):
        score = StabilityScore(
            syntax_score=0.5, execution_score=0.8,
            dependency_score=1.0, repair_success_score=0.0,
            confidence_score=0.6, overall_score=0.58
        )
        assert score.syntax_score == 0.5
        assert score.overall_score == 0.58


class TestTracebackAnalysis:
    def test_minimal_creation(self):
        analysis = TracebackAnalysis(
            error_type="SyntaxError", error_message="invalid syntax",
            root_cause="missing colon", suggested_fix="add colon"
        )
        assert analysis.error_type == "SyntaxError"
        assert analysis.file_path is None
        assert analysis.line_number is None
        assert analysis.is_syntax_error is False


class TestExecutionReport:
    def test_minimal_creation(self):
        report = ExecutionReport(
            command="python test.py", exit_code=0,
            stdout="done", stderr="", duration=1.5
        )
        assert report.command == "python test.py"
        assert report.exit_code == 0
        assert report.is_stable is False

    def test_with_traceback(self):
        tb = TracebackAnalysis(
            error_type="ValueError", error_message="bad value",
            root_cause="invalid input", suggested_fix="validate input"
        )
        report = ExecutionReport(
            command="python test.py", exit_code=1,
            stdout="", stderr="error", duration=0.5,
            traceback_analysis=tb, is_stable=False
        )
        assert report.traceback_analysis.error_type == "ValueError"


class TestPreSaveValidationResult:
    def test_valid(self):
        result = PreSaveValidationResult(is_valid=True, file_path="test.py")
        assert result.is_valid
        assert result.errors == []
        assert result.warnings == []
        assert result.ast_valid

    def test_invalid_with_errors(self):
        result = PreSaveValidationResult(
            is_valid=False, file_path="test.py",
            errors=["Syntax error"], ast_valid=False
        )
        assert not result.is_valid
        assert len(result.errors) == 1


class TestProjectState:
    def test_default_values(self):
        state = ProjectState(project_id="p1", goal_id="g1", root_path="/tmp")
        assert state.status == "initializing"
        assert state.validation_status == "pending"
        assert state.stability_status == "unstable"
        assert state.artifacts == []
        assert state.repair_attempts == 0

    def test_with_artifacts(self):
        art = Artifact(task_id="t1", path="test.py", artifact_type=ArtifactType.FILE, content="x")
        state = ProjectState(project_id="p1", goal_id="g1", root_path="/tmp", artifacts=[art])
        assert len(state.artifacts) == 1


class TestTask:
    def test_minimal_creation(self):
        task = Task(goal_id="g1", agent_type="planner", task_type="plan", description="test task")
        assert task.priority == TaskPriority.MEDIUM
        assert task.status == TaskStatus.PENDING
        assert task.dependencies == []
        assert task.repair_attempts == 0

    def test_auto_fields(self):
        task1 = Task(goal_id="g1", agent_type="planner", task_type="plan", description="t1")
        task2 = Task(goal_id="g2", agent_type="backend", task_type="code", description="t2")
        assert task1.id != task2.id
        assert isinstance(task1.created_at, datetime)
        assert isinstance(task1.updated_at, datetime)


class TestRepairStrategy:
    def test_creation(self):
        strategy = RepairStrategy(
            root_cause="syntax error", impacted_agent="debug",
            exact_fix_steps=["find line", "fix it"],
            retry_strategy="retry 3x", fallback_strategy="manual"
        )
        assert strategy.root_cause == "syntax error"
        assert len(strategy.exact_fix_steps) == 2


class TestRepairTask:
    def test_creation(self):
        task = RepairTask(
            goal_id="g1", agent_type="debug", task_type="repair",
            description="fix bug", target_task_id="tt1",
            failing_check="syntax", assigned_agent="debug",
            repair_reason="bad code", repair_instructions="fix it"
        )
        assert task.target_task_id == "tt1"
        assert task.failing_check == "syntax"
        assert task.assigned_agent == "debug"
        assert task.artifact_path is None


class TestGoalState:
    def test_default_creation(self):
        state = GoalState(original_goal="build app")
        assert state.status == TaskStatus.PENDING
        assert state.tasks == {}
        assert state.overall_summary is None

    def test_with_tasks(self):
        task = Task(goal_id="g1", agent_type="planner", task_type="plan", description="plan")
        state = GoalState(original_goal="build app", tasks={"t1": task})
        assert len(state.tasks) == 1
        assert state.tasks["t1"].description == "plan"
