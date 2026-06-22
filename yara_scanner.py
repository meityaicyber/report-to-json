#!/usr/bin/env python3
"""
yara_scanner.py
================
Malware-detection scanning layer for the Document Standardization Pipeline.

Compiles every .yar/.yara rule file in `rules/`, scans one file or a whole
directory of PDF/Office documents, prints a human-readable report, and
writes a structured JSON report for record-keeping / auditing.

Reference: YARA documentation - https://virustotal.github.io/yara/
           yara-python API    - https://github.com/VirusTotal/yara-python

Usage
-----
    python src/yara_scanner.py --input samples/report.pdf
    python src/yara_scanner.py --input-dir samples/ --output output/scan_results.json
    python src/yara_scanner.py --input-dir samples/ --rules rules/ -v
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yara

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RULES_DIR = PROJECT_ROOT / "rules"
SCAN_EXTENSIONS = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".rtf"}

# severity -> verdict precedence (checked top to bottom)
SEVERITY_TO_VERDICT = [
    ("high", "MALICIOUS"),
    ("medium", "SUSPICIOUS"),
    ("test", "TEST_SIGNATURE_DETECTED"),
]
VERDICT_ICON = {
    "MALICIOUS": "\U0001F6D1",               # stop sign
    "SUSPICIOUS": "\u26A0\uFE0F ",            # warning
    "TEST_SIGNATURE_DETECTED": "\U0001F9EA",  # test tube
    "CLEAN": "\u2705",                        # check mark
    "ERROR": "\u274C",                        # cross mark
}


def compile_rules(rules_dir: Path) -> yara.Rules:
    """Compile every .yar/.yara file in rules_dir into a single namespaced ruleset."""
    rule_files = sorted(rules_dir.glob("*.yar")) + sorted(rules_dir.glob("*.yara"))
    if not rule_files:
        raise FileNotFoundError(f"No .yar/.yara files found in {rules_dir}")

    filepaths = {f.stem: str(f) for f in rule_files}
    print(f"[+] Compiling {len(filepaths)} rule file(s): {', '.join(filepaths)}")
    return yara.compile(filepaths=filepaths)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _verdict_from_findings(findings: list[dict]) -> str:
    severities_present = {f["meta"].get("severity") for f in findings}
    for severity, verdict in SEVERITY_TO_VERDICT:
        if severity in severities_present:
            return verdict
    return "CLEAN"


def scan_file(rules: yara.Rules, path: Path, timeout: int = 60) -> dict:
    start = time.perf_counter()
    matches = rules.match(filepath=str(path), timeout=timeout)
    elapsed = round(time.perf_counter() - start, 4)

    findings = []
    for m in matches:
        findings.append({
            "rule": m.rule,
            "namespace": m.namespace,
            "tags": m.tags,
            "meta": dict(m.meta),
            "matched_strings": [
                {
                    "identifier": s.identifier,
                    "offset": s.instances[0].offset if s.instances else None,
                    "matched_data_hex": (
                        s.instances[0].matched_data[:40].hex() if s.instances else None
                    ),
                }
                for s in m.strings
            ],
        })

    # informational-only rules (severity "info") don't drive the verdict
    verdict_findings = [f for f in findings if f["meta"].get("severity") != "info"]

    return {
        "file": str(path),
        "filename": path.name,
        "sha256": sha256_of(path),
        "size_bytes": path.stat().st_size,
        "scan_time_seconds": elapsed,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "verdict": _verdict_from_findings(verdict_findings),
        "rule_matches": findings,
    }


def collect_targets(input_path: str | None, input_dir: str | None) -> list[Path]:
    targets: list[Path] = []
    if input_path:
        p = Path(input_path)
        if not p.exists():
            raise FileNotFoundError(p)
        targets.append(p)
    if input_dir:
        d = Path(input_dir)
        if not d.exists():
            raise FileNotFoundError(d)
        targets.extend(
            f for f in sorted(d.rglob("*"))
            if f.is_file() and f.suffix.lower() in SCAN_EXTENSIONS
        )
    return targets


def print_report(result: dict, verbose: bool = False) -> None:
    icon = VERDICT_ICON.get(result["verdict"], "?")
    print(f"\n{icon} {result['file']}  ->  {result['verdict']}")
    print(f"   sha256: {result['sha256']}")
    print(f"   size:   {result['size_bytes']} bytes | scan time: {result['scan_time_seconds']}s")

    matches = [f for f in result["rule_matches"] if f["meta"].get("severity") != "info"]
    if not matches:
        print("   no suspicious rule matches")
    for f in matches:
        sev = f["meta"].get("severity", "?").upper()
        print(f"   - [{sev}] {f['rule']}: {f['meta'].get('description', '')}")
        if verbose:
            for s in f["matched_strings"]:
                print(f"       match: {s['identifier']} @ offset {s['offset']} "
                      f"(hex: {s['matched_data_hex']})")


def main() -> None:
    ap = argparse.ArgumentParser(description="YARA malware scanner for the document pipeline")
    ap.add_argument("--input", help="Path to a single file to scan")
    ap.add_argument("--input-dir", help="Path to a directory to scan recursively")
    ap.add_argument("--rules", default=str(DEFAULT_RULES_DIR), help="Directory containing .yar rule files")
    ap.add_argument("--output", default=None, help="Path to write the JSON results report")
    ap.add_argument("-v", "--verbose", action="store_true", help="Show matched string offsets")
    args = ap.parse_args()

    if not args.input and not args.input_dir:
        ap.error("Provide --input <file> and/or --input-dir <directory>")

    rules = compile_rules(Path(args.rules))
    targets = collect_targets(args.input, args.input_dir)
    if not targets:
        print("[!] No matching files found to scan (supported extensions: "
              f"{', '.join(sorted(SCAN_EXTENSIONS))})")
        sys.exit(1)

    print(f"[+] Scanning {len(targets)} file(s)...")
    results = []
    for t in targets:
        try:
            result = scan_file(rules, t)
        except yara.Error as e:
            result = {
                "file": str(t), "filename": t.name, "verdict": "ERROR",
                "error": str(e), "rule_matches": [],
            }
        results.append(result)
        print_report(result, verbose=args.verbose)

    summary = {
        "total_files": len(results),
        "clean": sum(1 for r in results if r.get("verdict") == "CLEAN"),
        "test_signature_detected": sum(1 for r in results if r.get("verdict") == "TEST_SIGNATURE_DETECTED"),
        "suspicious": sum(1 for r in results if r.get("verdict") == "SUSPICIOUS"),
        "malicious": sum(1 for r in results if r.get("verdict") == "MALICIOUS"),
        "errors": sum(1 for r in results if r.get("verdict") == "ERROR"),
    }
    print("\n" + "=" * 60)
    print("SCAN SUMMARY:", json.dumps(summary, indent=2))

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "pipeline_stage": "malware_scan",
            "scanner": "yara-python",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "rules_dir": str(args.rules),
            "summary": summary,
            "results": results,
        }
        with open(out_path, "w") as fh:
            json.dump(report, fh, indent=2)
        print(f"\n[+] Full results written to {out_path}")


if __name__ == "__main__":
    main()
