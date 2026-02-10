"""
Validators for PRD, PRP and Task consistency
Enhanced with full traceability validation and parallel processing
"""

from __future__ import annotations

import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import yaml
from jsonschema import ValidationError, validate

logger = logging.getLogger(__name__)

# Pre-compile regex patterns for better performance
API_CALL_PATTERN = re.compile(r"(GET|POST|PUT|DELETE|PATCH)\s+([/a-zA-Z0-9\-_{}]+)", re.IGNORECASE)
FETCH_PATTERNS = [
    re.compile(r'fetch\(["\']([^"\']+)["\']', re.IGNORECASE),
    re.compile(r'axios\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']', re.IGNORECASE),
    re.compile(r'\.get\(["\']([^"\']+)["\']', re.IGNORECASE),
    re.compile(r'\.post\(["\']([^"\']+)["\']', re.IGNORECASE),
]


class ValidationResult:
    """Result of validation operation"""

    def __init__(self, valid: bool, errors: list[str] | None = None, warnings: list[str] | None = None):
        self.valid = valid
        self.errors = errors or []
        self.warnings = warnings or []

    def __bool__(self) -> bool:
        return self.valid

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
        }


class PRPValidator:
    """Validator for PRP files with enhanced traceability"""

    def __init__(self, schemas_dir: Path | None = None):
        """
        Initialize validator

        Args:
            schemas_dir: Directory containing JSON schemas
        """
        self.schemas_dir = schemas_dir or Path(__file__).parent.parent / "schemas"
        self.schemas: dict[str, Any] = {}
        self._load_schemas()

    def _load_schemas(self) -> None:
        """Load JSON schemas from schemas directory"""
        if not self.schemas_dir.exists():
            return

        for schema_file in self.schemas_dir.glob("*.json"):
            try:
                with open(schema_file, encoding="utf-8") as f:
                    self.schemas[schema_file.stem] = json.load(f)
            except Exception as e:
                print(f"Error loading schema {schema_file}: {e}")

    def _load_file(self, file_path: Path) -> dict[str, Any]:
        """Load JSON or YAML file"""
        content = file_path.read_text(encoding="utf-8")

        if file_path.suffix == ".json":
            return json.loads(content)
        # Try to extract YAML frontmatter from markdown
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
        if match:
            return yaml.safe_load(match.group(1)) or {}
        return yaml.safe_load(content) or {}

    def _extract_fr_ids(self, content: str) -> set[str]:
        """
        Extract all FR-XXX IDs from content

        Args:
            content: Text content to search

        Returns:
            Set of FR IDs found
        """
        # Pattern: FR-001, FR-002, etc.
        pattern = r"FR-(\d+)"
        matches = re.findall(pattern, content)
        return {f"FR-{match}" for match in matches}

    def _extract_us_ids(self, content: str) -> set[str]:
        """
        Extract all US-XXX IDs from content

        Args:
            content: Text content to search

        Returns:
            Set of US IDs found
        """
        # Pattern: US-001, US-002, etc.
        pattern = r"US-(\d+)"
        matches = re.findall(pattern, content)
        return {f"US-{match}" for match in matches}

    def validate_prp(self, prp_file: Path, schema_name: str = "prp-phase-schema") -> ValidationResult:
        """
        Validate PRP file against schema

        Args:
            prp_file: Path to PRP file
            schema_name: Name of schema to use

        Returns:
            ValidationResult
        """
        if schema_name not in self.schemas:
            return ValidationResult(False, errors=[f"Schema '{schema_name}' not found"])

        try:
            data = self._load_file(prp_file)
            schema = self.schemas[schema_name]
            validate(instance=data, schema=schema)
            return ValidationResult(True)
        except ValidationError as e:
            return ValidationResult(
                False,
                errors=[f"Validation error: {e.message} at path: {'.'.join(str(p) for p in e.path)}"],
            )
        except Exception as e:
            return ValidationResult(False, errors=[f"Error validating file: {str(e)}"])

    def validate_dependencies(self, prps: list[Path]) -> ValidationResult:
        """
        Validate dependencies between PRPs

        Args:
            prps: List of PRP file paths

        Returns:
            ValidationResult
        """
        phase_data = {}
        errors = []

        # Load all phases
        for prp_file in prps:
            try:
                data = self._load_file(prp_file)
                phase_id = data.get("phase")
                if phase_id:
                    phase_data[phase_id] = data
            except Exception as e:
                errors.append(f"Error loading {prp_file}: {e}")

        # Check dependencies
        for phase_id, phase in phase_data.items():
            deps = phase.get("dependencies", [])
            for dep in deps:
                if dep not in phase_data:
                    errors.append(f"Phase {phase_id} depends on {dep} which doesn't exist")

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def validate_consistency(self, prd: dict, prps: list[dict]) -> ValidationResult:
        """
        Validate that PRPs are consistent with PRD

        Args:
            prd: PRD dictionary
            prps: List of PRP dictionaries

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        # Extract feature IDs from PRD (only MUST priority)
        prd_features = {}
        for fr in prd.get("functional_requirements", []):
            fr_id = fr.get("id")
            priority = fr.get("priority", "").upper()
            if fr_id and priority == "MUST":
                prd_features[fr_id] = {
                    "id": fr_id,
                    "title": fr.get("title", ""),
                    "acceptance_criteria": fr.get("acceptance_criteria", []),
                    "priority": priority,
                }

        # Extract FR references from PRPs
        prp_content = json.dumps(prps)
        referenced_frs = self._extract_fr_ids(prp_content)

        # Check if all MUST features are referenced
        for fr_id, fr_data in prd_features.items():
            if fr_id not in referenced_frs:
                warnings.append(f"MUST feature {fr_id} ({fr_data['title']}) is not referenced in any PRP")

        # Check if referenced features exist in PRD
        for fr_id in referenced_frs:
            if (
                fr_id not in prd_features
                and not fr_id.startswith("US-")
                and not any(fr.get("id") == fr_id for fr in prd.get("functional_requirements", []))
            ):
                errors.append(f"Feature {fr_id} referenced in PRPs but not found in PRD")

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def _load_tasks_for_traceability(self, tasks_dir: Path) -> tuple[set[str], dict[str, dict]]:
        """Load and parse tasks for traceability validation"""
        task_files = list(tasks_dir.glob("TASK.*.md")) + list(tasks_dir.glob("TASK.*.json"))
        task_ids = set()
        task_data_map = {}
        errors = []

        for task_file in task_files:
            try:
                if task_file.suffix == ".json":
                    data = self._load_file(task_file)
                    task_id = data.get("task_id")
                    if task_id:
                        task_ids.add(task_id)
                        task_data_map[task_id] = data
                else:
                    # Extract from markdown
                    content = task_file.read_text(encoding="utf-8")
                    match = re.search(r"TASK\.([A-Z]+-\d+)", content)
                    if match:
                        task_id = match.group(1)
                        task_ids.add(task_id)
            except Exception as e:
                errors.append(f"Error loading task {task_file}: {e}")

        # We might want to handle errors differently, but for now we return what we found
        return task_ids, task_data_map

    def _validate_task_acceptance_criteria(self, fr_id: str, fr_data: dict, task_data_map: dict) -> list[str]:
        """Validate acceptance criteria coverage for a requirement"""
        warnings = []
        if fr_id in task_data_map:
            task = task_data_map[fr_id]
            task_acceptance = task.get("acceptance_criteria", [])
            prd_acceptance = fr_data.get("acceptance_criteria", [])

            for prd_criterion in prd_acceptance:
                prd_keywords = set(prd_criterion.lower().split())
                found = False
                for task_criterion in task_acceptance:
                    task_keywords = set(task_criterion.lower().split())
                    if len(prd_keywords & task_keywords) >= len(prd_keywords) * 0.5:
                        found = True
                        break

                if not found and prd_criterion:
                    warnings.append(
                        f"Acceptance criterion '{prd_criterion[:50]}...' from {fr_id} "
                        f"may not be fully covered in task"
                    )
        return warnings

    def validate_traceability(self, prd_file: Path, tasks_dir: Path) -> ValidationResult:
        """
        Validate full traceability: PRD → Tasks

        Ensures 100% traceability of functional requirements to tasks

        Args:
            prd_file: Path to PRD structured JSON
            tasks_dir: Directory containing task files

        Returns:
            ValidationResult with traceability validation
        """
        errors = []
        warnings = []

        # Load PRD
        prd_data = self._load_file(prd_file)

        # Extract MUST priority functional requirements
        must_frs = {}
        for fr in prd_data.get("functional_requirements", []):
            fr_id = fr.get("id")
            priority = fr.get("priority", "").upper()
            if fr_id and priority == "MUST":
                must_frs[fr_id] = {
                    "id": fr_id,
                    "title": fr.get("title", ""),
                    "acceptance_criteria": fr.get("acceptance_criteria", []),
                }

        # Load tasks
        task_ids, task_data_map = self._load_tasks_for_traceability(tasks_dir)

        # Validate traceability: Every MUST FR must have a corresponding Task
        for fr_id, fr_data in must_frs.items():
            if fr_id not in task_ids:
                errors.append(f"MUST requirement {fr_id} ({fr_data['title']}) has no corresponding Task")

        # Validate acceptance criteria mapping
        for fr_id, fr_data in must_frs.items():
            warnings.extend(self._validate_task_acceptance_criteria(fr_id, fr_data, task_data_map))

        # Check for orphaned tasks (tasks without corresponding FR)
        all_frs = {fr.get("id") for fr in prd_data.get("functional_requirements", [])}
        for task_id in task_ids:
            if not task_id.startswith("US-") and task_id not in must_frs:
                if task_id not in all_frs:
                    warnings.append(f"Task {task_id} has no corresponding requirement in PRD")

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_all(self, prps_dir: Path, prd_file: Path | None = None, tasks_dir: Path | None = None) -> dict:
        """
        Validate all PRPs in directory with full traceability

        Args:
            prps_dir: Directory containing PRP files
            prd_file: Optional PRD file for consistency check
            tasks_dir: Optional tasks directory for traceability validation

        Returns:
            Dictionary with validation results
        """
        prp_files = list(prps_dir.glob("*.json")) + list(prps_dir.glob("*.md"))
        results = {}

        # Validate each PRP
        for prp_file in prp_files:
            result = self.validate_prp(prp_file)
            results[prp_file.name] = result.to_dict()

        # Validate dependencies
        dep_result = self.validate_dependencies(prp_files)
        results["dependencies"] = dep_result.to_dict()

        # Validate consistency with PRD if provided
        if prd_file and prd_file.exists():
            prd_data = self._load_file(prd_file)
            prps_data = [self._load_file(f) for f in prp_files]
            consistency_result = self.validate_consistency(prd_data, prps_data)
            results["consistency"] = consistency_result.to_dict()

        # Validate traceability PRD → Tasks if both provided
        if prd_file and tasks_dir and prd_file.exists() and tasks_dir.exists():
            traceability_result = self.validate_traceability(prd_file, tasks_dir)
            results["traceability"] = traceability_result.to_dict()

        return results

    def _load_openapi_endpoints(self, api_specs: Path, errors: list[str]) -> dict[str, dict]:
        """Load and parse OpenAPI endpoints"""
        endpoints = {}
        try:
            api_data = self._load_file(api_specs)
            paths = api_data.get("paths", {})
            for path, methods in paths.items():
                for method, spec in methods.items():
                    if method.lower() in ["get", "post", "put", "delete", "patch"]:
                        endpoint_key = f"{method.upper()} {path}"
                        endpoints[endpoint_key] = {
                            "path": path,
                            "method": method.upper(),
                            "summary": spec.get("summary", ""),
                            "operationId": spec.get("operationId", ""),
                        }
        except Exception as e:
            errors.append(f"Error loading OpenAPI spec: {e}")
        return endpoints

    def _validate_single_task_contract(
        self, task_file: Path, endpoints: dict[str, dict]
    ) -> tuple[list[str], list[str]]:
        """Validate a single task file against API contract"""
        task_errors = []
        task_warnings = []

        try:
            task_content = task_file.read_text(encoding="utf-8")

            # Match API calls
            matches = API_CALL_PATTERN.finditer(task_content)
            for match in matches:
                method = match.group(1).upper()
                path = match.group(2)
                normalized_path = path.split("?")[0].split("#")[0]
                endpoint_key = f"{method} {normalized_path}"

                # Key check
                if endpoint_key not in endpoints:
                    # Pattern check
                    found = False
                    for spec_endpoint_key in endpoints:
                        spec_method, spec_path = spec_endpoint_key.split(" ", 1)
                        if spec_method == method:
                            pattern_path = re.sub(r"\{[^}]+\}", r"[^/]+", spec_path)
                            pattern_path = pattern_path.replace("/", r"\/")
                            if re.match(f"^{pattern_path}$", normalized_path):
                                found = True
                                break
                    if not found:
                        task_errors.append(
                            f"Task {task_file.name} references non-existent endpoint: {method} {normalized_path}"
                        )

            # Match Fetch calls
            for pattern in FETCH_PATTERNS:
                matches = pattern.finditer(task_content)
                for match in matches:
                    url = match.group(-1)
                    if url.startswith("http"):
                        from urllib.parse import urlparse

                        parsed = urlparse(url)
                        path = parsed.path
                    else:
                        path = url.split("?")[0]

                    found = any(
                        endpoint["path"] == path
                        or re.match(
                            re.sub(r"\{[^}]+\}", r"[^/]+", endpoint["path"]).replace("/", r"\/"),
                            path,
                        )
                        for endpoint in endpoints.values()
                    )

                    if not found and path.startswith("/api"):
                        task_warnings.append(f"Task {task_file.name} may reference unvalidated endpoint: {path}")

        except Exception as e:
            task_warnings.append(f"Error analyzing task {task_file.name}: {e}")

        return task_errors, task_warnings

    def validate_contract_integrity(self, api_specs: Path, ui_tasks_dir: Path) -> ValidationResult:
        """
        Deep Cross-Validation: Verifies API contract integrity with parallel processing

        Validates that UI tasks (F4) match the OpenAPI spec generated in F3.
        Detects "broken contracts" - when API changes invalidate UI implementations.

        Args:
            api_specs: Path to OpenAPI specification file (F3 output)
            ui_tasks_dir: Directory containing UI/UX tasks (F4)

        Returns:
            ValidationResult with contract integrity check
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Load endpoints
        endpoints = self._load_openapi_endpoints(api_specs, errors)
        if errors:
            return ValidationResult(False, errors=errors)

        # Load UI tasks
        ui_task_files = list(ui_tasks_dir.glob("TASK.*.md")) + list(ui_tasks_dir.glob("TASK.*.json"))

        # Process tasks in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self._validate_single_task_contract, task_file, endpoints): task_file
                for task_file in ui_task_files
            }

            for future in as_completed(futures):
                try:
                    task_errors, task_warnings = future.result()
                    errors.extend(task_errors)
                    warnings.extend(task_warnings)
                except Exception as e:
                    task_file = futures[future]
                    logger.error("Error processing task %s: %s", task_file.name, e)
                    warnings.append(f"Error processing task {task_file.name}: {e}")

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def generate_transient_mock(self, openapi_spec: Path, port: int = 4010) -> dict:
        """
        Generate transient mock server from OpenAPI spec (F3)

        Creates an ephemeral mock server that the AI agent can use to test UI (F4)
        during development. Uses Prism or similar mock server.

        Args:
            openapi_spec: Path to OpenAPI specification file
            port: Port for mock server (default: 4010)

        Returns:
            Dictionary with mock server information
        """
        import subprocess
        import time

        errors: list[str] = []
        warnings: list[str] = []

        # Check if Prism is available
        try:
            result = subprocess.run(["prism", "--version"], check=False, capture_output=True, text=True, timeout=5)
            prism_available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            prism_available = False

        if not prism_available:
            warnings.append("Prism não está instalado. Instale com: npm install -g @stoplight/prism-cli")
            warnings.append("Mock server não será iniciado automaticamente.")
            return {
                "success": False,
                "errors": errors,
                "warnings": warnings,
                "mock_url": None,
                "command": f"prism mock {openapi_spec} -p {port}",
            }

        # Generate mock server command
        mock_command = ["prism", "mock", str(openapi_spec), "-p", str(port)]

        try:
            # Start mock server in background
            process = subprocess.Popen(mock_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # Wait a bit for server to start
            time.sleep(2)

            # Check if process is still running
            if process.poll() is None:
                mock_url = f"http://localhost:{port}"
                return {
                    "success": True,
                    "errors": errors,
                    "warnings": warnings,
                    "mock_url": mock_url,
                    "process_id": process.pid,
                    "command": " ".join(mock_command),
                    "message": f" Mock server iniciado em {mock_url}",
                }
            # Process exited, check for errors
            stdout, stderr = process.communicate()
            errors.append(f"Mock server falhou ao iniciar: {stderr}")
            return {
                "success": False,
                "errors": errors,
                "warnings": warnings,
                "mock_url": None,
                "command": " ".join(mock_command),
            }

        except Exception as e:
            errors.append(f"Erro ao iniciar mock server: {e}")
            return {
                "success": False,
                "errors": errors,
                "warnings": warnings,
                "mock_url": None,
                "command": " ".join(mock_command),
            }
