import os
import ast
from typing import List, Dict, Any
from core.schema import Artifact, ArtifactType
from core.validation_schema import ValidationResult, ValidationStatus, ErrorCategory

class ArtifactValidator:
    @staticmethod
    def validate_artifact_content(artifact: Artifact) -> List[ValidationResult]:
        results = []
        if artifact.path.endswith(".py"):
            try:
                ast.parse(artifact.content)
            except SyntaxError as e:
                results.append(ValidationResult(
                    check_name="python_syntax_check",
                    status=ValidationStatus.FAILED,
                    message=f"Syntax error in {artifact.path}: {str(e)}",
                    error_category=ErrorCategory.SYNTAX,
                    details={"path": artifact.path}
                ))
        elif artifact.path.endswith(".html"):
            # Ensure it's not actually a React component masquerading as HTML
            if "import React" in artifact.content or "export default" in artifact.content:
                results.append(ValidationResult(
                    check_name="html_content_check",
                    status=ValidationStatus.FAILED,
                    message=f"React/JSX syntax found in HTML file: {artifact.path}",
                    error_category=ErrorCategory.INTEGRITY,
                    details={"path": artifact.path}
                ))
        return results

    @staticmethod
    def validate_file_extension_consistency(artifact: Artifact) -> List[ValidationResult]:
        results = []
        lang = artifact.metadata.get("language", "").lower()
        if lang == "python" and not artifact.path.endswith(".py"):
            results.append(ValidationResult(
                check_name="extension_consistency",
                status=ValidationStatus.FAILED,
                message=f"Python code saved with wrong extension: {artifact.path}",
                error_category=ErrorCategory.INTEGRITY,
                details={"path": artifact.path}
            ))
        elif lang in ["javascript", "typescript", "react", "html", "css", "json", "svg", "frontend"] and not artifact.path.endswith((".js", ".jsx", ".ts", ".tsx", ".css", ".html", ".json", ".svg")):
            results.append(ValidationResult(
                check_name="extension_consistency",
                status=ValidationStatus.FAILED,
                message=f"Frontend code saved with wrong extension: {artifact.path}",
                error_category=ErrorCategory.INTEGRITY,
                details={"path": artifact.path}
            ))
        return results

    @staticmethod
    def validate_artifacts(artifacts: List[Artifact]) -> List[ValidationResult]:
        results = []
        paths = set()
        
        for artifact in artifacts:
            # 1. Check for empty files
            if artifact.artifact_type == ArtifactType.FILE and not artifact.content.strip():
                results.append(ValidationResult(
                    check_name="empty_file_check",
                    status=ValidationStatus.FAILED,
                    message=f"Artifact at {artifact.path} is empty.",
                    error_category=ErrorCategory.INTEGRITY,
                    details={"path": artifact.path}
                ))
            
            # 2. Check for duplicate paths in session
            if artifact.path in paths:
                results.append(ValidationResult(
                    check_name="duplicate_path_check",
                    status=ValidationStatus.WARNING,
                    message=f"Duplicate artifact path detected: {artifact.path}",
                    error_category=ErrorCategory.INTEGRITY,
                    details={"path": artifact.path}
                ))
            paths.add(artifact.path)
            
            # 3. Basic path validation
            if ".." in artifact.path or artifact.path.startswith("/"):
                 results.append(ValidationResult(
                    check_name="path_traversal_check",
                    status=ValidationStatus.FAILED,
                    message=f"Unsafe path detected: {artifact.path}",
                    error_category=ErrorCategory.SECURITY,
                    details={"path": artifact.path}
                ))

            # 4. Content and Extension Validation
            if artifact.artifact_type == ArtifactType.FILE:
                results.extend(ArtifactValidator.validate_artifact_content(artifact))
                results.extend(ArtifactValidator.validate_file_extension_consistency(artifact))

        if not results:
            results.append(ValidationResult(
                check_name="artifact_integrity",
                status=ValidationStatus.PASSED,
                message="All artifacts passed integrity checks."
            ))
            
        return results

    @staticmethod
    def verify_project_structure(root_path: str, expected_files: List[str]) -> List[ValidationResult]:
        results = []
        for file_path in expected_files:
            full_path = os.path.join(root_path, file_path)
            if not os.path.exists(full_path):
                results.append(ValidationResult(
                    check_name="structure_check",
                    status=ValidationStatus.FAILED,
                    message=f"Missing expected file: {file_path}",
                    error_category=ErrorCategory.INTEGRITY
                ))
        
        if not results:
            results.append(ValidationResult(
                check_name="structure_check",
                status=ValidationStatus.PASSED,
                message="Project structure verified."
            ))
        return results
