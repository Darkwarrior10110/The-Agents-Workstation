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


class TestBuildResult:
    def test_defaults(self):
        r = BuildResult(status=ValidationStatus.PASSED)
        assert r.errors == []
        assert r.warnings == []


class TestRuntimeResult:
    def test_creation(self):
        r = RuntimeResult(
            status=ValidationStatus.PASSED,
            port=8000,
            health_check_url="http://localhost:8000"
        )
        assert r.port == 8000


class TestSupervisorReport:
    def test_minimal_creation(self):
        r = SupervisorReport(
            goal_id="g1",
            project_id="p1",
            overall_health=ValidationStatus.PASSED,
            total_tasks=5,
            failed_tasks=[],
            validation_results=[],
            summary="All good",
            execution_stats={}
        )
        assert r.goal_id == "g1"
        assert r.overall_health == ValidationStatus.PASSED
        assert r.total_tasks == 5
