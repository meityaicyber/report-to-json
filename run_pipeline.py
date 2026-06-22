#!/usr/bin/env python3
"""
run_pipeline.py
=================
Main entry point for the full three-stage malware-detection pipeline.

Stage 1  YARA + ClamAV parallel scan  ─────────────────────────────
Stage 2  Deep content analysis (REVIEW files only)  ────────────────
         • JS intent classification  (js_classifier)
         • Embedded file MIME detection (embed_classifier + python-magic)
         • Ghostscript sanitization  (sanitizer)
Stage 3  Final routing + tabulated report  ─────────────────────────
         MALICIOUS → quarantine/   (with entity list + page numbers)
         CLEAN / CLEAN_SANITIZED → left in place
         REVIEW (INCONCLUSIVE) → review/  (manual triage needed)

Usage
-----
    python src/run_pipeline.py --root "/path/to/Report formats"
    python src/run_pipeline.py --root ./samples --no-move     # dry run
    python src/run_pipeline.py --root ./samples --no-deep     # skip Stage 2
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import shutil
import hashlib
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from combined_scanner import (
    CombinedScanner, DEFAULT_QUARANTINE_DIR, DEFAULT_REVIEW_DIR, VERDICT_ICON,
)
from clamav_scanner import PDFStructuralAnalyzer

try:
    from tabulate import tabulate
except ImportError:
    tabulate = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_FILE   = PROJECT_ROOT / "output" / "scan_log.txt"

SCAN_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".rtf",
    ".exe", ".js", ".zip", ".txt",
}


# ── Helpers ─────────────────────────────────────────────────────────────────

def setup_logging() -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
    )


def _table(title: str, rows: list, headers: list) -> None:
    if not rows:
        return
    if tabulate:
        fmt = tabulate(rows, headers=headers, tablefmt="grid")
    else:
        fmt = "\n".join(["\t".join(map(str, r)) for r in [headers] + rows])
    print(f"\n{title}\n")
    print(fmt)
    logging.info(f"\n{title}\n{fmt}")


def _short_location(result: dict) -> str:
    """One-line location string for the summary table."""
    deep = result.get("deep_analysis")
    if deep and deep.get("malicious_entities"):
        ents = deep["malicious_entities"]
        pages = sorted({str(e["page"]) for e in ents})
        return "; ".join(pages)
    loc = result.get("yara_location_summary", "-")
    return loc if loc != "n/a" else "-"


def _entity_detail_rows(result: dict) -> list[list]:
    """Expand malicious_entities into one row per entity for the detail table."""
    rows = []
    for e in result.get("malicious_entities", []):
        rows.append([
            result["filename"],
            result["final_verdict"],
            e.get("type", "?"),
            e.get("severity", "?"),
            str(e.get("page", "?")),
            e.get("detail", ""),
        ])
    return rows


# ── Pipeline runner ─────────────────────────────────────────────────────────
def get_file_sha256(file_path: str | Path) -> str:
    """Calculate the unique SHA-256 hash of a file to identify duplicates."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
def run_pipeline(
    root_folder: str,
    move_files: bool = True,
    require_clamav: bool = True,
    run_deep: bool = True,
    json_output: Path = None,
) -> dict:
    if not os.path.isdir(root_folder):
        logging.error(f"Root folder not found: {root_folder}")
        return {}

    scanner  = CombinedScanner(
        move_files=move_files,
        require_clamav=require_clamav,
        run_deep_analysis=run_deep,
    )
    analyzer = PDFStructuralAnalyzer()

    counters = {"total": 0, "clean": 0, "clean_sanitized": 0,
                "malicious": 0, "review": 0}
    summary_rows   = []   # one row per file → Combined Scan Results table
    entity_rows    = []   # one row per finding → Malicious Entities table
    pdf_struct_rows = []  # one row per PDF → PDF Structural Analysis table
    all_results    = []
    start_time     = datetime.now()

    logging.info(f"Starting pipeline: {root_folder}")
    logging.info(f"Deep analysis: {'enabled' if run_deep else 'disabled'}")
    logging.info("=" * 72)

    for cur_path, _dirs, files in os.walk(root_folder):
        # Skip our own output dirs if they happen to be nested inside root
        if Path(cur_path).resolve() in (
            DEFAULT_QUARANTINE_DIR.resolve(), DEFAULT_REVIEW_DIR.resolve()
        ):
            continue

        for fname in sorted(files):
            ext = os.path.splitext(fname)[1].lower()
            if ext not in SCAN_EXTENSIONS:
                continue

            fpath = os.path.join(cur_path, fname)
            logging.info(f"Scanning: {fpath}")

            result = scanner.scan(fpath)
            all_results.append(result)

            fv = result["final_verdict"]
            counters["total"] += 1
            counters[fv.lower()] = counters.get(fv.lower(), 0) + 1

            icon = VERDICT_ICON.get(fv, "❓")
            logging.info(
                f"  {icon} {result['filename']}  final={fv}"
                f"  stage1={result['stage1_verdict']}"
                f"  YARA={result['yara_verdict']}"
                f"  ClamAV={result['clamav_status']}"
            )
            da = result.get("deep_analysis")
            if da and da.get("deep_analysis_performed"):
                logging.info(
                    f"    [deep] rec={da['deep_recommendation']}"
                    f"  js={da['js_verdict']}"
                    f"  embed={da['embed_verdict']}"
                    f"  → {da['final_verdict']}"
                )
            for e in result.get("malicious_entities", []):
                logging.warning(
                    f"    [{e['severity']}] {e['type']} @ page {e['page']}: {e['detail']}"
                )

            # Summary table row
            summary_rows.append([
                result["filename"],
                result["yara_verdict"],
                result["clamav_status"],
                result["stage1_verdict"],
                da["deep_recommendation"] if (da and da.get("deep_analysis_performed")) else "—",
                fv,
                Path(result["routed_to"]).parent.name if result["routed_to"] else "in place",
            ])

            # Malicious entity detail rows
            entity_rows.extend(_entity_detail_rows(result))

            # PDF structural analysis
            if ext == ".pdf":
                target = result["routed_to"] or fpath
                if Path(target).exists():
                    struct = analyzer.analyze(target)
                    pdf_struct_rows.append([
                        result["filename"],
                        struct.get("pages"),
                        struct.get("encrypted"),
                        struct.get("javascript"),
                        struct.get("embedded_files"),
                        struct.get("risk_level"),
                    ])

    elapsed = (datetime.now() - start_time).total_seconds()

    # ── Console + log output ─────────────────────────────────────────
    logging.info("")
    logging.info("=" * 72)
    logging.info("PIPELINE SUMMARY")
    logging.info("=" * 72)
    logging.info(f"Root folder    : {root_folder}")
    logging.info(f"Elapsed        : {elapsed:.2f}s")
    logging.info(f"Total          : {counters['total']}")
    logging.info(f"Clean          : {counters.get('clean', 0)}")
    logging.info(f"Clean+Sanitized: {counters.get('clean_sanitized', 0)}")
    logging.info(f"Malicious      : {counters.get('malicious', 0)}  → {DEFAULT_QUARANTINE_DIR.name}/")
    logging.info(f"Review (manual): {counters.get('review', 0)}  → {DEFAULT_REVIEW_DIR.name}/")

    _table(
        "Pipeline Summary",
        [
            ["Total Files",           counters["total"]],
            ["✅  Clean",              counters.get("clean", 0)],
            ["✅🧼  Clean (sanitized)", counters.get("clean_sanitized", 0)],
            ["🛑  Malicious",          counters.get("malicious", 0)],
            ["🔍  Review (manual)",    counters.get("review", 0)],
        ],
        ["Metric", "Count"],
    )

    _table(
        "Combined Scan Results  (Stage 1 = YARA+ClamAV  │  Stage 2 = Deep Analysis)",
        summary_rows,
        ["File", "YARA", "ClamAV", "Stage-1", "Deep-Rec", "Final Verdict", "Routed To"],
    )

    if entity_rows:
        _table(
            "🔴 Malicious / Suspicious Entities  (what was found + where)",
            entity_rows,
            ["File", "Verdict", "Entity Type", "Severity", "Page / Location", "Detail"],
        )

    if pdf_struct_rows:
        _table(
            "PDF Structural Analysis  (supplementary — not part of verdict)",
            pdf_struct_rows,
            ["PDF", "Pages", "Encrypted", "Has JS", "Embedded Files", "Risk"],
        )

    logging.info(f"\nLog: {LOG_FILE}")

    # ── JSON report ──────────────────────────────────────────────────
    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        with open(json_output, "w") as fh:
            json.dump({
                "generated_at":   datetime.now().isoformat(),
                "root_folder":    root_folder,
                "elapsed_seconds": elapsed,
                "counters":       counters,
                "results":        all_results,
            }, fh, indent=2, default=str)
        logging.info(f"JSON report: {json_output}")

    return counters


# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="YARA + ClamAV + Deep Analysis + Ghostscript pipeline"
    )
    ap.add_argument("--root", required=True, help="Folder to scan recursively")
    ap.add_argument("--no-move",  action="store_true",
                    help="Dry run — don't move files")
    ap.add_argument("--no-deep",  action="store_true",
                    help="Skip Stage-2 deep analysis (review files stay in review/)")
    ap.add_argument("--no-require-clamav", action="store_true",
                    help="Continue with YARA-only if ClamAV is unavailable")
    ap.add_argument("--output",
                    default=str(PROJECT_ROOT / "output" / "pipeline_results.json"),
                    help="JSON report output path")
    args = ap.parse_args()

    setup_logging()
    run_pipeline(
        root_folder=args.root,
        move_files=not args.no_move,
        require_clamav=not args.no_require_clamav,
        run_deep=not args.no_deep,
        json_output=Path(args.output),
    )
