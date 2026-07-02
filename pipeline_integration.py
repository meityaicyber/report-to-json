#!/usr/bin/env python3
"""
pipeline_integration.py
========================
Drop-in pre-processing gate for the existing `doc-pipeline` project
(Document Standardization Pipeline using Qwen2.5-VL).

Import `malware_gate()` and call it as the FIRST step in
`src/pipeline.py`, before any file is opened by pdfplumber, the VLM,
or python-docx. Untrusted input should never reach a parser before
it has been screened.

Example wiring inside the existing src/pipeline.py:

    from pipeline_integration import malware_gate

    def process_document(input_path, ...):
        scan_result = malware_gate(input_path)
        if scan_result["verdict"] in ("MALICIOUS", "SUSPICIOUS"):
            raise MalwareDetectedError(scan_result)
        # ... existing Route 1 / Route 2 extraction continues only
        #     after a CLEAN (or accepted TEST_SIGNATURE_DETECTED) verdict
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the scanner importable regardless of where this file is copied to
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / ".engine"))

from yara_scanner import compile_rules, scan_file, DEFAULT_RULES_DIR  # noqa: E402


class MalwareDetectedError(Exception):
    """Raised when malware_gate() blocks a file from entering the pipeline."""

    def __init__(self, scan_result: dict):
        self.scan_result = scan_result
        rules_hit = ", ".join(m["rule"] for m in scan_result["rule_matches"])
        super().__init__(
            f"Blocked '{scan_result['file']}' - verdict={scan_result['verdict']} "
            f"(rules: {rules_hit})"
        )


# Compile once, reuse across every file in a batch run (mirrors how the
# existing pipeline shares one loaded VLM instance across extractors).
_RULES = None


def _get_rules():
    global _RULES
    if _RULES is None:
        _RULES = compile_rules(DEFAULT_RULES_DIR)
    return _RULES


def malware_gate(input_path: str, block_on: tuple[str, ...] = ("MALICIOUS", "SUSPICIOUS")) -> dict:
    """
    Scan a single input file before it is handed to the extraction pipeline.

    Parameters
    ----------
    input_path : str
        Path to the PDF/DOCX/etc. file about to be processed.
    block_on : tuple[str, ...]
        Verdicts that should raise MalwareDetectedError. Defaults to
        blocking MALICIOUS and SUSPICIOUS, but letting
        TEST_SIGNATURE_DETECTED and CLEAN pass through (adjust per your
        risk tolerance - e.g. add "TEST_SIGNATURE_DETECTED" if you want
        EICAR-style hits to also halt processing).

    Returns
    -------
    dict : the full scan result (also written nowhere by default - the
           caller decides whether/where to log it for an audit trail).

    Raises
    ------
    MalwareDetectedError if the verdict is in `block_on`.
    """
    rules = _get_rules()
    result = scan_file(rules, Path(input_path))

    if result["verdict"] in block_on:
        raise MalwareDetectedError(result)

    return result


if __name__ == "__main__":
    # Quick manual test: python pipeline_integration.py <file>
    if len(sys.argv) != 2:
        print("Usage: python pipeline_integration.py <file>")
        sys.exit(1)

    try:
        res = malware_gate(sys.argv[1])
        print(f"[OK] '{sys.argv[1]}' passed the malware gate - verdict: {res['verdict']}")
    except MalwareDetectedError as e:
        print(f"[BLOCKED] {e}")
        sys.exit(2)
