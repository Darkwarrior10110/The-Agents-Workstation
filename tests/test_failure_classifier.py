import pytest
from core.failure_classifier import FailureClassifier, FailureCategory


class TestFailureClassifier:
    def test_classify_code_failure(self):
        result = FailureClassifier.classify("SyntaxError: invalid syntax")
        assert result.category == FailureCategory.CODE_FAILURE

    def test_classify_provider_failure(self):
        result = FailureClassifier.classify("429 Too Many Requests")
        assert result.category == FailureCategory.PROVIDER_FAILURE

    def test_classify_import_error(self):
        result = FailureClassifier.classify("ModuleNotFoundError: No module named 'flask'")
        assert result.category == FailureCategory.DEPENDENCY_FAILURE

    def test_classify_timeout(self):
        result = FailureClassifier.classify("timeout: Connection timed out")
        assert result.category == FailureCategory.TIMEOUT_FAILURE

    def test_classify_unknown_failure(self):
        result = FailureClassifier.classify("Some random error")
        assert result.category == FailureCategory.UNKNOWN_FAILURE

    def test_classify_runtime_failure(self):
        result = FailureClassifier.classify("Connection refused")
        assert result.category == FailureCategory.RUNTIME_FAILURE

    def test_classify_returns_reason(self):
        result = FailureClassifier.classify("SyntaxError: bad syntax")
        assert isinstance(result.reason, str)
