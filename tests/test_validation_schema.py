import pytest
from core.validation_schema import (
    SupervisorReport, ValidationResult, ValidationStatus,
    BuildResult, RuntimeResult, ErrorCategory
)


class TestValidationResult:
    def test_creation(self):
        r = ValidationResult(
            check_name="syntax_check",
            status=ValidationStatus.PASSED,
            message="All good",
            error_category=ErrorCategory.SYNTAX
        )
        assert r.check_name == "syntax_check"
        assert r.status == ValidationStatus.PASSED

    def test_default_details(self):
        r = ValidationResult(
            check_name="test", status=ValidationStatus.FAILED, message="fail"
        )
        assert r.details == {}
        assert r.error_category is None


class TestBuildResult:
    def test_defaults(self):
        r = BuildResult(component="backend", status=ValidationStatus.PASSED)
        assert r.errors == []
        assert r.execution is None

    def test_with_execution(self):
        from core.validation_schema import ExecutionResult
        exec_r = ExecutionResult(command="build", exit_code=0, stdout="ok", stderr="", duration=1.0)
        r = BuildResult(component="frontend", status=ValidationStatus.PASSED, execution=exec_r)
        assert r.execution.stdout == "ok"


class TestRuntimeResult:
    def test_creation(self):
        r = RuntimeResult(component="backend", status=ValidationStatus.PASSED)
        assert r.logs == []
        assert r.ports_active == []

    def test_with_ports(self):
        r = RuntimeResult(
            component="frontend", status=ValidationStatus.PASSED,
            logs=["started"], ports_active=[8000]
        )
        assert r.ports_active == [8000]
        assert len(r.logs) == 1


class TestSupervisorReport:
    def test_minimal_creation(self):
        r = SupervisorReport(
            goal_id="g1",
            project_id="p1",
            overall_health=ValidationStatus.PASSED,
            total_tasks=5,
            failed_tasks=[],
            summary="All good",
            execution_stats={}
        )
        assert r.goal_id == "g1"
        assert r.overall_health == ValidationStatus.PASSED
        assert r.total_tasks == 5

    def test_with_results(self):
        vr = ValidationResult(check_name="test", status=ValidationStatus.PASSED, message="ok")
        r = SupervisorReport(
            goal_id="g1", project_id="p1",
            overall_health=ValidationStatus.PASSED,
            total_tasks=1, failed_tasks=[],
            summary="ok", execution_stats={},
            validation_results=[vr]
        )
        assert len(r.validation_results) == 1
