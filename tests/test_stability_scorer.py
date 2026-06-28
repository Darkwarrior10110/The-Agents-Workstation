import pytest
from core.stability_scorer import StabilityScorer
from core.schema import PreSaveValidationResult, ExecutionReport


class TestStabilityScorer:
    def test_calculate_perfect(self):
        validations = [PreSaveValidationResult(is_valid=True, file_path="a.py")]
        executions = [ExecutionReport(command="test", exit_code=0, stdout="ok", stderr="", duration=1.0, is_stable=True)]
        result = StabilityScorer.calculate(validations, executions, 0, 3)
        assert result.overall_score == 1.0
        assert result.syntax_score == 1.0
        assert result.execution_score == 1.0
        assert result.confidence_score == 1.0

    def test_calculate_failed_validations(self):
        validations = [PreSaveValidationResult(is_valid=False, file_path="a.py", errors=["bad"])]
        result = StabilityScorer.calculate(validations, [], 0, 3)
        assert result.syntax_score < 1.0
        assert result.overall_score < 1.0

    def test_calculate_failed_execution(self):
        execution = ExecutionReport(command="test", exit_code=1, stdout="", stderr="fail", duration=0.5)
        result = StabilityScorer.calculate([], [execution], 0, 3)
        assert result.execution_score < 1.0
        assert result.overall_score < 1.0

    def test_calculate_with_repairs(self):
        result = StabilityScorer.calculate([], [], 2, 3)
        assert result.repair_success_score < 1.0

    def test_calculate_max_repairs(self):
        result = StabilityScorer.calculate([], [], 3, 3)
        assert result.repair_success_score == 0.25

    def test_confidence_drops_with_bad_syntax(self):
        v = PreSaveValidationResult(is_valid=False, file_path="a.py", errors=["bad"], ast_valid=False)
        result = StabilityScorer.calculate([v], [], 0, 3)
        assert result.confidence_score == 0.9
