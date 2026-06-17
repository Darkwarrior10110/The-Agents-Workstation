from core.schema import StabilityScore, PreSaveValidationResult, ExecutionReport
from typing import List

class StabilityScorer:
    """
    Computes a quantifiable stability score based on validation and execution results.
    """
    
    @staticmethod
    def calculate(
        validations: List[PreSaveValidationResult], 
        executions: List[ExecutionReport],
        repair_attempts: int,
        max_repairs: int
    ) -> StabilityScore:
        score = StabilityScore()
        
        # 1. Syntax Score (0.0 to 1.0)
        # Deduct for ast failures or json format errors
        syntax_penalties = sum(1 for v in validations if not v.is_valid or not v.ast_valid)
        score.syntax_score = max(0.0, 1.0 - (syntax_penalties * 0.25))
        
        # 2. Execution Score (0.0 to 1.0)
        execution_penalties = sum(1 for e in executions if not e.is_stable)
        score.execution_score = max(0.0, 1.0 - (execution_penalties * 0.3))
        
        # 3. Dependency Score (0.0 to 1.0)
        dep_penalties = 0
        for e in executions:
            if e.traceback_analysis and e.traceback_analysis.root_cause in ["import_error", "dependency_error"]:
                dep_penalties += 1
        score.dependency_score = max(0.0, 1.0 - (dep_penalties * 0.4))
        
        # 4. Repair Success Score (0.0 to 1.0)
        if repair_attempts > 0:
            # The more attempts it took, the lower the score. If it hit max, it's very low.
            score.repair_success_score = max(0.1, 1.0 - (repair_attempts / (max_repairs + 1)))
        else:
            score.repair_success_score = 1.0
            
        # 5. Overall Score & Confidence
        # Weighted average
        score.overall_score = (
            (score.syntax_score * 0.4) + 
            (score.execution_score * 0.4) + 
            (score.dependency_score * 0.1) + 
            (score.repair_success_score * 0.1)
        )
        
        # Confidence score drops sharply if executions fail entirely
        if score.execution_score == 0.0 or score.syntax_score < 0.5:
            score.confidence_score = 0.2
        else:
            score.confidence_score = score.overall_score
            
        return score
