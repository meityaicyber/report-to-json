"""
Schema validation for extracted JSON output.
Validates against base schema and checks for quality issues.
"""

import json
import re
from typing import List, Optional
from pathlib import Path
import jsonschema


class SchemaValidator:
    """Validate extracted JSON against base and inferred schemas."""

    def __init__(self):
        self.base_schema = self._load_base_schema()
        self.hallucination_patterns = [
            r'\[insert',
            r'<insert',
            r'\bTODO\b',
            r'N/A \(not provided\)',
            r'as mentioned above',
            r'see above',
        ]

    def validate(self, output: dict, inferred_schema: Optional[dict] = None) -> List[str]:
        """
        Validate extracted JSON output.
        
        Args:
            output: Extracted JSON object
            inferred_schema: Optional schema to validate against
            
        Returns:
            List of validation warning strings. Empty = valid.
        """
        warnings = []
        
        # 1. Base schema conformance
        base_warnings = self._validate_base_schema(output)
        warnings.extend(base_warnings)
        
        # 2. Inferred schema conformance (soft validation)
        if inferred_schema:
            schema_warnings = self._validate_inferred_schema(output, inferred_schema)
            warnings.extend(schema_warnings)
        
        # 3. Check for null-only sections
        null_sections = self._check_null_sections(output)
        warnings.extend(null_sections)
        
        # 4. Check for hallucination markers
        hallucination_warnings = self._check_hallucinations(output)
        warnings.extend(hallucination_warnings)
        
        # 5. Check image placeholder count
        image_warnings = self._check_image_count(output)
        warnings.extend(image_warnings)
        
        # 6. Check for raw_text_fallback presence
        fallback_warnings = self._check_fallbacks(output)
        warnings.extend(fallback_warnings)
        
        return warnings

    def _load_base_schema(self) -> dict:
        """Load base schema from schemas/base.schema.json."""
        paths = [
            Path(__file__).parent.parent / 'schemas' / 'base.schema.json',
            Path('schemas') / 'base.schema.json',
            Path('.') / 'schemas' / 'base.schema.json',
        ]
        
        for path in paths:
            if path.exists():
                with open(path, 'r') as f:
                    return json.load(f)
        
        # Fallback schema
        return {
            'required': ['_meta', 'sections'],
            'properties': {
                '_meta': {
                    'required': ['pipeline_version', 'source_file', 'document_type', 'extraction_timestamp']
                },
                'sections': {'type': 'object'}
            }
        }

    def _validate_base_schema(self, output: dict) -> List[str]:
        """Validate output against base schema."""
        warnings = []
        
        # Check required top-level keys
        if '_meta' not in output:
            warnings.append("SCHEMA_ERROR: Missing _meta object")
            return warnings
        
        if 'sections' not in output:
            warnings.append("SCHEMA_ERROR: Missing sections object")
            return warnings
        
        meta = output['_meta']
        
        # Check required _meta fields
        required_meta = ['pipeline_version', 'source_file', 'document_type', 'extraction_timestamp']
        for field in required_meta:
            if field not in meta:
                warnings.append(f"SCHEMA_ERROR: Missing _meta.{field}")
            elif meta[field] is None:
                warnings.append(f"SCHEMA_ERROR: _meta.{field} is null")
        
        return warnings

    def _validate_inferred_schema(self, output: dict, inferred_schema: dict) -> List[str]:
        """Validate output against inferred schema (soft validation)."""
        warnings = []
        
        try:
            # Check that sections structure matches inferred schema
            sections = output.get('sections', {})
            inferred_sections = inferred_schema.get('sections', {})
            
            for section_key in inferred_sections.keys():
                if section_key not in sections:
                    warnings.append(f"SCHEMA_WARNING: Expected section '{section_key}' not found in output")
            
            # Try full jsonschema validation
            try:
                jsonschema.validate(output, inferred_schema)
            except jsonschema.ValidationError as e:
                warnings.append(f"SCHEMA_WARNING: {e.message}")
        
        except Exception as e:
            warnings.append(f"SCHEMA_WARNING: Validation check failed: {e}")
        
        return warnings

    def _check_null_sections(self, output: dict) -> List[str]:
        """Check for sections that are completely null or empty."""
        warnings = []
        
        sections = output.get('sections', {})
        
        for section_key, section_value in sections.items():
            if section_value is None:
                warnings.append(f"SECTION_EMPTY: Section '{section_key}' is null")
            elif isinstance(section_value, dict) and all(v is None for v in section_value.values()):
                warnings.append(f"SECTION_EMPTY: Section '{section_key}' contains only null values")
            elif isinstance(section_value, (list, dict)) and len(section_value) == 0:
                warnings.append(f"SECTION_EMPTY: Section '{section_key}' is empty")
        
        return warnings

    def _check_hallucinations(self, output: dict) -> List[str]:
        """Check for suspicious hallucination markers in output."""
        warnings = []
        
        # Serialize output to search for patterns
        output_str = json.dumps(output, indent=2)
        
        for pattern in self.hallucination_patterns:
            matches = re.findall(pattern, output_str, re.IGNORECASE)
            if matches:
                warnings.append(f"HALLUCINATION_SUSPECT: Found pattern '{pattern}' ({len(matches)} times)")
        
        return warnings

    def _check_image_count(self, output: dict) -> List[str]:
        """Check that image placeholder count is consistent."""
        warnings = []
        
        meta = output.get('_meta', {})
        reported_count = meta.get('image_placeholder_count')
        
        if reported_count is not None:
            # Count IMAGE_PLACEHOLDER mentions in output
            output_str = json.dumps(output, indent=2)
            actual_count = output_str.count('IMAGE_PLACEHOLDER')
            
            if actual_count != reported_count:
                warnings.append(
                    f"IMAGE_COUNT_MISMATCH: "
                    f"Reported {reported_count} but found {actual_count} image placeholders"
                )
        
        return warnings

    def _check_fallbacks(self, output: dict) -> List[str]:
        """Check for raw_text_fallback presence (indicates extraction failure)."""
        warnings = []
        
        # Check top-level
        if output.get('raw_text_fallback') is not None:
            warnings.append(
                f"EXTRACTION_FALLBACK: raw_text_fallback present at top level"
            )
        
        # Check in sections
        sections = output.get('sections', {})
        for section_key, section_value in sections.items():
            if isinstance(section_value, dict) and section_value.get('raw_text_fallback') is not None:
                warnings.append(
                    f"EXTRACTION_FALLBACK: raw_text_fallback present in section '{section_key}'"
                )
        
        return warnings

    def generate_report(self, warnings: List[str]) -> str:
        """Generate human-readable validation report."""
        if not warnings:
            return "✓ Validation passed: no issues detected"
        
        # Group warnings by type
        grouped = {}
        for warning in warnings:
            warning_type = warning.split(':')[0]
            if warning_type not in grouped:
                grouped[warning_type] = []
            grouped[warning_type].append(warning)
        
        report_lines = [f"⚠️  Validation warnings ({len(warnings)} total):\n"]
        
        for warning_type in sorted(grouped.keys()):
            report_lines.append(f"\n{warning_type}:")
            for warning in grouped[warning_type]:
                report_lines.append(f"  - {warning}")
        
        return '\n'.join(report_lines)
