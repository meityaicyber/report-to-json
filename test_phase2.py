"""
Phase 2 verification script.
Test LLM schema inference and extraction with Ollama.
"""

import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from llm_extractor import LLMExtractor
from schema_validator import SchemaValidator


def main():
    """Test Phase 2 LLM integration."""
    
    print("\n" + "="*70)
    print("Phase 2: LLM Integration Test")
    print("="*70)
    
    # Check if Ollama is running
    extractor = LLMExtractor(model="llama3.1:latest", host="localhost", port=11434)
    
    print("\n[1] Checking Ollama connection...")
    try:
        # Try a simple connection
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"    ✓ Ollama connected")
            print(f"    ✓ Available models: {len(models)}")
            
            # Check for llama3.1
            if any('llama' in m.get('name', '').lower() for m in models):
                print(f"    ✓ llama3.1:latest model available")
            else:
                print(f"    ⚠️  llama3.1 not in model list")
                print(f"       Run: ollama pull llama3.1")
        else:
            print(f"    ❌ Ollama returned status {response.status_code}")
            return
    except Exception as e:
        print(f"    ❌ Cannot connect to Ollama: {e}")
        print(f"       Make sure Ollama is running: ollama serve")
        return
    
    # Load a test markdown file
    print("\n[2] Loading test Markdown...")
    test_md_file = Path(__file__).parent / 'test_outputs' / '1-Audit Report_normalized.md'
    
    if not test_md_file.exists():
        print(f"    ⚠️  Test markdown not found: {test_md_file}")
        print(f"       Run test_phase1.py first")
        return
    
    with open(test_md_file, 'r', encoding='utf-8') as f:
        test_markdown = f.read()
    
    print(f"    ✓ Loaded {len(test_markdown)} characters")
    
    # Test schema inference (Pass 1)
    print("\n[3] Testing schema inference (Pass 1)...")
    print("    This may take 30-60 seconds on first run...")
    
    try:
        inferred_schema = extractor.infer_schema(
            test_markdown,
            doc_type_hint="network_audit_report"
        )
        
        if '_error' in inferred_schema:
            print(f"    ⚠️  Inference returned error: {inferred_schema['_error']}")
        else:
            print(f"    ✓ Schema inferred successfully")
            
            # Show schema structure
            sections = inferred_schema.get('sections', {})
            print(f"    ✓ Found {len(sections)} section definitions:")
            for section_name in list(sections.keys())[:5]:
                print(f"      - {section_name}")
            if len(sections) > 5:
                print(f"      ... and {len(sections) - 5} more")
            
            # Save schema for inspection
            schema_file = Path(__file__).parent / 'test_outputs' / 'inferred_schema.json'
            with open(schema_file, 'w') as f:
                json.dump(inferred_schema, f, indent=2)
            print(f"    ✓ Saved schema: {schema_file}")
    
    except Exception as e:
        print(f"    ❌ Schema inference failed: {e}")
        return
    
    # Test data extraction (Pass 2)
    print("\n[4] Testing data extraction (Pass 2)...")
    print("    This may take 30-60 seconds...")
    
    try:
        # Use just the first section for testing (to keep it quick)
        section_hint = "Executive Summary"
        extracted = extractor.extract(
            test_markdown[:2000],  # Use just first 2000 chars
            inferred_schema,
            section_hint=section_hint
        )
        
        if '_extraction_status' in extracted and extracted['_extraction_status'] == 'failed':
            print(f"    ⚠️  Extraction failed: {extracted.get('_error', 'Unknown')}")
        else:
            print(f"    ✓ Extraction successful")
            
            # Show extracted structure
            sections = extracted.get('sections', {})
            print(f"    ✓ Extracted {len(sections)} sections")
            
            # Save extracted data for inspection
            extracted_file = Path(__file__).parent / 'test_outputs' / 'extracted_sample.json'
            with open(extracted_file, 'w') as f:
                json.dump(extracted, f, indent=2)
            print(f"    ✓ Saved extraction: {extracted_file}")
    
    except Exception as e:
        print(f"    ❌ Extraction failed: {e}")
        return
    
    # Test validation
    print("\n[5] Testing schema validation...")
    
    validator = SchemaValidator()
    
    # Prepare a sample output
    sample_output = {
        '_meta': {
            'pipeline_version': '1.0.0',
            'source_file': 'test.pdf',
            'document_type': 'audit_report',
            'extraction_timestamp': '2024-01-01T00:00:00',
            'image_placeholder_count': 5
        },
        'sections': extracted.get('sections', {})
    }
    
    warnings = validator.validate(sample_output, inferred_schema)
    
    if not warnings:
        print(f"    ✓ Validation passed (no issues)")
    else:
        print(f"    ⚠️  Validation warnings: {len(warnings)}")
        for warning in warnings[:5]:
            print(f"      - {warning}")
        if len(warnings) > 5:
            print(f"      ... and {len(warnings) - 5} more")
    
    print("\n" + "="*70)
    print("Phase 2 verification complete!")
    print("="*70 + "\n")
    
    print("Next steps:")
    print("  1. Review test outputs in test_outputs/ directory")
    print("  2. Verify schema structure matches document layout")
    print("  3. Check extracted data for accuracy")
    print("  4. Run Phase 3 full pipeline test: python -m src.pipeline --help")


if __name__ == '__main__':
    main()
