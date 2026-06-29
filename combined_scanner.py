#!/usr/bin/env python3
"""
combined_scanner.py
=====================
Full three-stage malware detection pipeline.

Stage 1 — Parallel broad scan (YARA + ClamAV)
  Both engines run simultaneously in a ThreadPoolExecutor. The combined
  verdict is derived from the decision matrix below.

Stage 2 — Deep content analysis  (REVIEW files only)
  Files that reach REVIEW are inspected by pdf_content_classifier:
    • JavaScript intent classification (js_classifier)
    • Embedded file MIME classification (embed_classifier)
  The deep analyzer then either:
    BLOCK    → final verdict MALICIOUS → quarantine/
    SANITIZE → Ghostscript strips active content → CLEAN_SANITIZED
    PASS     → final verdict CLEAN  (REVIEW was a false positive)
  Non-PDF REVIEW files (DOCX/etc.) skip deep analysis: no open-source
  tool can safely decompress and classify MS-OVBA macro source in pure
  Python — those files stay in review/ for manual triage.

Stage 1 decision matrix
------------------------
YARA verdict              ClamAV    Combined     Stage-2?
CLEAN                     CLEAN     CLEAN        no
MALICIOUS/TEST_SIG        INFECTED  MALICIOUS    no  (straight to quarantine)
SUSPICIOUS                any       REVIEW       YES
any                       ERROR     REVIEW       YES
disagreement (all others)           REVIEW       YES
"""

from __future__ import annotations

import concurrent.futures
import json
import logging
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from yara_scanner import compile_rules, scan_file as yara_scan_file, DEFAULT_RULES_DIR
from clamav_scanner import ClamAVScanner
from pdf_page_locator import locate_matches_by_page, describe_locations
from deep_analyzer import deep_analyze

DEFAULT_QUARANTINE_DIR = PROJECT_ROOT / "quarantine"
DEFAULT_REVIEW_DIR = PROJECT_ROOT / "review"
DEFAULT_SANITIZED_DIR = PROJECT_ROOT / "sanitized"

# Human-readable icons for the console
VERDICT_ICON = {
    "CLEAN":            "\u2705",   # ✅
    "CLEAN_SANITIZED":  "\u2705\U0001F9FC",  # ✅🧼
    "MALICIOUS":        "\U0001F6D1",  # 🛑
    "REVIEW":           "\U0001F50D",  # 🔍
}


class CombinedScanner:
    def __init__(
        self,
        rules_dir: Path = DEFAULT_RULES_DIR,
        quarantine_dir: Path = DEFAULT_QUARANTINE_DIR,
        review_dir: Path = DEFAULT_REVIEW_DIR,
        sanitized_dir: Path = DEFAULT_SANITIZED_DIR,
        update_clamav_db: bool = False,
        require_clamav: bool = True,
        clamav_signature_db: Optional[Path] = None,
        move_files: bool = True,
        run_deep_analysis: bool = True,
    ):
        self.rules_dir = Path(rules_dir)
        self.yara_rules = compile_rules(self.rules_dir)
        self.quarantine_dir = Path(quarantine_dir)
        self.review_dir = Path(review_dir)
        self.sanitized_dir = Path(sanitized_dir)
        self.move_files = move_files
        self.run_deep_analysis = run_deep_analysis

        for d in (self.quarantine_dir, self.review_dir, self.sanitized_dir):
            d.mkdir(parents=True, exist_ok=True)

        self.clamav: Optional[ClamAVScanner] = None
        try:
            self.clamav = ClamAVScanner(
                update_db=update_clamav_db,
                signature_db=clamav_signature_db,
            )
        except EnvironmentError as e:
            if require_clamav:
                raise
            logging.warning(f"ClamAV unavailable, YARA-only mode: {e}")

    # ── Stage 1 engines ─────────────────────────────────────────────
    def _run_yara(self, path: Path) -> dict:
        return yara_scan_file(self.yara_rules, path)

    def _run_clamav(self, path: Path):
        if self.clamav is None:
            return "ERROR", "ClamAV not configured"
        return self.clamav.scan_file(path)

    # ── Stage 1 decision matrix ──────────────────────────────────────
    @staticmethod
    def _combine(yara_verdict: str, clamav_status: str) -> str:
        if yara_verdict == "ERROR" or clamav_status == "ERROR":
            return "REVIEW"
        if yara_verdict == "SUSPICIOUS":
            return "REVIEW"
        if yara_verdict == "CLEAN" and clamav_status == "CLEAN":
            return "CLEAN"
        if yara_verdict in ("MALICIOUS", "TEST_SIGNATURE_DETECTED") \
                and clamav_status == "INFECTED":
            return "MALICIOUS"
        # All disagreements (MALICIOUS+CLEAN, CLEAN+INFECTED, etc.) → REVIEW
        return "REVIEW"

    # ── Physical file routing ────────────────────────────────────────
    def _move(self, path: Path, dest_dir: Path) -> Optional[str]:
        if not self.move_files:
            return None
        ts = int(time.time())
        dest = dest_dir / f"{ts}_{path.name}"
        try:
            shutil.move(str(path), str(dest))
            logging.info(f"  Moved [{dest_dir.name}/]: {path.name} → {dest}")
            return str(dest)
        except Exception as e:
            logging.error(f"  Move failed for {path}: {e}")
            return None

    # ── Main scan entry point ────────────────────────────────────────
    def scan(self, file_path: str) -> dict:
        path = Path(file_path)

        # ── Stage 1: YARA + ClamAV in parallel ──────────────────────
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            yf = ex.submit(self._run_yara, path)
            cf = ex.submit(self._run_clamav, path)
            yara_result = yf.result()
            clam_status, clam_details = cf.result()

        stage1_verdict = self._combine(yara_result["verdict"], clam_status)

        # Page-level localization for the YARA matches (PDF only)
        page_hits: dict = {}
        location_summary = "n/a"
        if path.suffix.lower() == ".pdf" and yara_result["rule_matches"]:
            page_hits = locate_matches_by_page(
                self.yara_rules, str(path), self.rules_dir
            )
            location_summary = describe_locations(
                page_hits,
                [m["rule"] for m in yara_result["rule_matches"]],
            )

        # ── Stage 2: Deep analysis for REVIEW files ──────────────────
        deep_result: Optional[dict] = None
        final_verdict = stage1_verdict
        routed_to: Optional[str] = None

        if stage1_verdict == "REVIEW" and self.run_deep_analysis:
            logging.info(f"  → Stage 2 deep analysis: {path.name}")
            deep_result = deep_analyze(
                path,
                sanitized_dir=self.sanitized_dir,
                yara_rules=self.yara_rules,
                rules_dir=self.rules_dir,
            )
            dv = deep_result["final_verdict"]

            if dv == "MALICIOUS":
                final_verdict = "MALICIOUS"
                routed_to = self._move(path, self.quarantine_dir)
                logging.warning(
                    f"  Deep analysis: MALICIOUS → quarantine: {path.name}"
                )
            elif dv in ("CLEAN", "CLEAN_SANITIZED"):
                final_verdict = dv   # CLEAN or CLEAN_SANITIZED
                routed_to = None     # stays in place (original or sanitized copy)
                logging.info(f"  Deep analysis: {dv} — file left in place")
            else:
                # INCONCLUSIVE (e.g. non-PDF DOCX)
                final_verdict = "REVIEW"
                routed_to = self._move(path, self.review_dir)
                logging.info(f"  Deep analysis: INCONCLUSIVE → review/")

        elif stage1_verdict == "MALICIOUS":
            routed_to = self._move(path, self.quarantine_dir)
        elif stage1_verdict == "REVIEW":
            # Deep analysis disabled — route to review as before
            routed_to = self._move(path, self.review_dir)
        # CLEAN → no move

        # ── Build output record ──────────────────────────────────────
        # Merge malicious_entities from deep analysis + page_hits from YARA
        entities = deep_result.get("malicious_entities", []) if deep_result else []

        # Also emit the YARA matches as structured entities if no deep analysis
        if not entities and yara_result["rule_matches"]:
            for m in yara_result["rule_matches"]:
                sev = m["meta"].get("severity", "info")
                if sev in ("high", "medium", "test"):
                    page_ref = (
                        min(page_hits.keys()) if page_hits else "document-level"
                    )
                    entities.append({
                        "type": "YARAMatch",
                        "detail": f"[{sev.upper()}] {m['rule']}: {m['meta'].get('description', '')}",
                        "page": page_ref,
                        "severity": "MALICIOUS" if sev == "high" else "SUSPICIOUS",
                    })

        return {
            # ── identification ──────────────────────────────────────
            "file":         str(path),
            "filename":     path.name,
            "scanned_at":   datetime.now(timezone.utc).isoformat(),
            # ── stage 1 ─────────────────────────────────────────────
            "yara_verdict":  yara_result["verdict"],
            "yara_matches":  [
                {
                    "rule":        m["rule"],
                    "severity":    m["meta"].get("severity"),
                    "description": m["meta"].get("description"),
                }
                for m in yara_result["rule_matches"]
            ],
            "clamav_status":  clam_status,
            "clamav_details": clam_details,
            "stage1_verdict": stage1_verdict,
            # ── stage 1 page localization ────────────────────────────
            "yara_location_summary": location_summary,
            "yara_page_breakdown":   page_hits,
            # ── stage 2 ─────────────────────────────────────────────
            "deep_analysis":  deep_result,
            # ── final ────────────────────────────────────────────────
            "final_verdict":       final_verdict,
            "malicious_entities":  entities,
            "routed_to":           routed_to,
        }


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        description="YARA + ClamAV + Deep Analysis combined scanner"
    )
    ap.add_argument("--input", help="Single file")
    ap.add_argument("--input-dir", help="Directory (recursive)")
    ap.add_argument("--no-move", action="store_true")
    ap.add_argument("--no-deep", action="store_true",
                    help="Skip Stage-2 deep analysis")
    ap.add_argument(
        "--output",
        default=str(PROJECT_ROOT / "output" / "combined_results.json"),
    )
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )
    scanner = CombinedScanner(
        move_files=not args.no_move,
        run_deep_analysis=not args.no_deep,
    )
    targets = []
    if args.input:
        targets.append(Path(args.input))
    if args.input_dir:
        exts = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt"}
        targets.extend(
            p for p in sorted(Path(args.input_dir).rglob("*"))
            if p.suffix.lower() in exts
        )
    if not targets:
        ap.error("Provide --input or --input-dir")

    results = []
    for t in targets:
        print(f"\nScanning: {t}")
        r = scanner.scan(str(t))
        icon = VERDICT_ICON.get(r["final_verdict"], "?")
        print(f"{icon} {r['filename']}  →  {r['final_verdict']}"
              f"  (YARA={r['yara_verdict']}, ClamAV={r['clamav_status']})")
        for e in r["malicious_entities"]:
            print(f"   [{e['severity']}] {e['type']} @ {e['page']}: {e['detail']}")
        if r["routed_to"]:
            print(f"   Moved to: {r['routed_to']}")
        results.append(r)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as fh:
        json.dump(
            {"generated_at": datetime.now(timezone.utc).isoformat(), "results": results},
            fh, indent=2,
        )
    print(f"\n[+] Report: {out}")
