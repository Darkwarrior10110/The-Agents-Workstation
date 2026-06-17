from enum import Enum
from pydantic import BaseModel
import re

class FailureSeverity(str, Enum):
    TRANSIENT = "transient"
    PERMANENT = "permanent"
    CRITICAL = "critical"

class FailureCategory(str, Enum):
    PROVIDER_FAILURE = "provider_failure"
    CODE_FAILURE = "code_failure"
    VALIDATION_FAILURE = "validation_failure"
    RUNTIME_FAILURE = "runtime_failure"
    DEPENDENCY_FAILURE = "dependency_failure"
    TIMEOUT_FAILURE = "timeout_failure"
    FILESYSTEM_FAILURE = "filesystem_failure"
    UNKNOWN_FAILURE = "unknown_failure"

class ClassifiedFailure(BaseModel):
    category: FailureCategory
    severity: FailureSeverity
    retryable: bool
    reason: str

class FailureClassifier:
    @staticmethod
    def classify(error_msg: str) -> ClassifiedFailure:
        msg_lower = error_msg.lower()
        
        # Provider Failures
        if any(kw in msg_lower for kw in ["429", "quota", "resource_exhausted", "rate limit", "503", "service unavailable", "overloaded", "providerfailure"]):
            return ClassifiedFailure(
                category=FailureCategory.PROVIDER_FAILURE, 
                severity=FailureSeverity.TRANSIENT, 
                retryable=True, 
                reason="Infrastructure/Provider outage or rate limit."
            )
            
        # Code/Generation Failures
        if any(kw in msg_lower for kw in ["syntaxerror", "indentationerror", "jsondecodeerror", "expecting value", "invalid syntax"]):
            return ClassifiedFailure(
                category=FailureCategory.CODE_FAILURE, 
                severity=FailureSeverity.PERMANENT, 
                retryable=False, 
                reason="Code compilation or JSON parsing failure."
            )
            
        # Runtime/Terminal Failures
        if any(kw in msg_lower for kw in ["connection refused", "port already in use", "address already in use", "command rejected"]):
            return ClassifiedFailure(
                category=FailureCategory.RUNTIME_FAILURE, 
                severity=FailureSeverity.TRANSIENT, 
                retryable=True, 
                reason="Runtime execution, network binding failure, or security block."
            )
            
        # Timeout Failures
        if "timeout" in msg_lower:
            return ClassifiedFailure(
                category=FailureCategory.TIMEOUT_FAILURE, 
                severity=FailureSeverity.TRANSIENT, 
                retryable=True, 
                reason="Execution timed out."
            )
            
        # Missing Dependency
        if any(kw in msg_lower for kw in ["modulenotfounderror", "no module named"]):
            return ClassifiedFailure(
                category=FailureCategory.DEPENDENCY_FAILURE, 
                severity=FailureSeverity.PERMANENT, 
                retryable=False, 
                reason="Missing required dependency."
            )
            
        return ClassifiedFailure(
            category=FailureCategory.UNKNOWN_FAILURE, 
            severity=FailureSeverity.PERMANENT, 
            retryable=False, 
            reason=f"Unknown failure occurred: {error_msg[:50]}..."
        )
