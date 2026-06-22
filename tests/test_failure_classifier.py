import pytest
from core.failure_classifier import FailureClassifier, FailureCategory


class TestFailureClassifier:
    def test_classify_code_failure(self):
        result = FailureClassifier.classify("SyntaxError: invalid syntax")
        assert result.category == FailureCategory.CODE_FAILURE

    def test_classify_provider_failure(self):
        result = FailureClassifier.classify("500 Internal Server Error")
        assert result.category == FailureCategory.PROVIDER_FAILURE

    def test_classify_import_error(self):
        result = FailureClassifier.classify("ModuleNotFoundError: No module named 'flask'")
        assert result.category == FailureCategory.CODE_FAILURE

    def test_classify_timeout(self):
        result = FailureClassifier.classify("timeout: Connection timed out")
        assert result.category == FailureCategory.PROVIDER_FAILURE

    def test_classify_unknown_failure(self):
        result = FailureClassifier.classify("Some random error")
        assert result.category == FailureCategory.UNKNOWN
