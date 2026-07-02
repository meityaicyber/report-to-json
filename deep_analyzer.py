#!/usr/bin/env python3
"""
deep_analyzer.py
=================
Stage 2 of the pipeline: detailed content analysis for files that
reached the REVIEW bucket after the YARA + ClamAV parallel scan.

What it does for a PDF
-----------------------
1. Runs pdf_content_classifier.classify_pdf_content() which:
      - Extracts and classifies every JavaScript block via js_classifier
        (detects MALICIOUS APIs, obfuscation patterns, heap-spray)
      - Extracts and classifies every embedded file via embed_classifier
        (MIME detection via python-magic → SAFE | DANGEROUS | UNKNOWN)
2. Builds a human-readable `malicious_entities` list, each entry tagged
   with type, finding, and (for PDFs) the best-effort page number from
   pdf_page_locator (dual-strategy: raw content stream re-scan + pypdf
   decoded-text search).
3. Applies the recommendation from the classifier:
      PASS     → final_verdict = CLEAN (no action needed)
      SANITIZE → runs Ghostscript via sanitizer.ghostscript_sanitize()
                 Strips JS, embedded executables, /OpenAction etc.
                 → if GS succeeds:  CLEAN_SANITIZED  (safe copy in sanitized/)
                 → if GS fails:     MALICIOUS        (cannot be made safe)
      BLOCK    → final_verdict = MALICIOUS (quarantine without touching)

What it does for non-PDF (DOCX/XLSX/PPTX)
-------------------------------------------
Deep analysis of Office formats is beyond pure Python (macro source
lives inside MS-OVBA-compressed vbaProject.bin — unpacking requires
oletools, not included here). For now, non-PDF REVIEW files get
final_verdict = INCONCLUSIVE so they stay in review/ for human triage
rather than being silently passed or silently quarantined.

Return schema
--------------
{
  "deep_analysis_performed" : bool,
  "deep_skipped_reason"     : str | None,      # set when not a PDF
  "js_verdict"              : "NONE"|"BENIGN"|"UNKNOWN"|"MALICIOUS",
  "js_apis_found"           : [str],
  "js_obfuscation_score"    : int,             # 0-100+
  "embed_verdict"           : "NONE"|"SAFE"|"MIXED"|"DANGEROUS",
  "embed_details"           : [(filename, mime, verdict), ...],
  "deep_recommendation"     : "PASS"|"SANITIZE"|"BLOCK"|None,
  "deep_reason"             : str,
  "sanitized_path"          : str | None,      # path to GS output
  "malicious_entities"      : [
      {
        "type"     : "JavaScript" | "EmbeddedFile" | "ObfuscatedScript",
        "detail"   : str,        # human label
        "page"     : int | "document-level",
        "severity" : "MALICIOUS" | "DANGEROUS" | "SUSPICIOUS"
      }, ...
  ],
  "final_verdict"           : "CLEAN"|"CLEAN_SANITIZED"|"MALICIOUS"|"INCONCLUSIVE",
  "final_verdict_reason"    : str,
}
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional, Union

# Make sibling modules importable regardless of cwd
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / ".engine"))

from pdf_content_classifier import classify_pdf_content  # noqa: E402
from sanitizer import ghostscript_sanitize  # noqa: E402
from pdf_page_locator import locate_matches_by_page  # noqa: E402
from yara_scanner import DEFAULT_RULES_DIR  # noqa: E402
from pdf_content_classifier import classify_pdf_content
from sanitizer import ghostscript_sanitize
# Add these three new imports:
from docx_classifier import classify_docx_content
from docx_sanitizer import docx_sanitize
from txtclassifier import classify_txt_content

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SANITIZED_DIR = PROJECT_ROOT / "sanitized"


def _page_label(page_hits: dict, entity_type: str) -> Union[int, str]:
    """
    Return the page number for a JS/embed finding, or 'document-level'.
    page_hits is {page_num: [rule_names]} from pdf_page_locator.
    We use it as a coarse signal: if *any* page has a match, return that
    page number. Real JS-to-page attribution requires a full JS AST
    parser; this is the best we can do with a pure-Python approach.
    """
    if page_hits:
        return min(page_hits.keys())  # earliest page with any YARA match
    return "document-level"


def _build_malicious_entities(content_result: dict, page_hits: dict) -> list:
    """
    Convert the classifier output into a structured list of malicious
    entities, each annotated with a page number where possible.
    """
    entities = []
    page_label = _page_label(page_hits, "JavaScript")

    # ── JavaScript findings ────────────────────────────────────────────
    js_v = content_result.get("js_verdict", "NONE")
    js_apis = content_result.get("js_apis", [])
    js_score = content_result.get("js_obfusc_score", 0)

    if js_v == "MALICIOUS" and js_apis:
        for api in js_apis:
            entities.append({
                "type": "JavaScript",
                "detail": _describe_js_api(api),
                "page": page_label,
                "severity": "MALICIOUS",
            })
    elif js_v == "MALICIOUS" and js_score >= 50:
        entities.append({
            "type": "ObfuscatedScript",
            "detail": f"Obfuscated JavaScript (complexity score {js_score}/100+) "
                      f"— {', '.join(js_apis) if js_apis else 'no named APIs extracted'}",
            "page": page_label,
            "severity": "MALICIOUS",
        })
    elif js_v == "UNKNOWN" and js_apis:
        entities.append({
            "type": "JavaScript",
            "detail": f"Unclassified JavaScript with suspicious patterns: {', '.join(js_apis)}",
            "page": page_label,
            "severity": "SUSPICIOUS",
        })

    # ── Embedded file findings ──────────────────────────────────────────
    for filename, mime, verdict in content_result.get("embed_details", []):
        if verdict in ("DANGEROUS", "UNKNOWN"):
            entities.append({
                "type": "EmbeddedFile",
                "detail": f"Embedded file '{filename}' detected as {mime} → {verdict}",
                "page": "document-level",   # embedded files live in the doc catalog
                "severity": "DANGEROUS" if verdict == "DANGEROUS" else "SUSPICIOUS",
            })

    return entities


# Short labels for the JS APIs defined in js_classifier.MALICIOUS_JS_APIS
_JS_API_DESCRIPTIONS = {
    "exportDataObject": "exportDataObject — silently executes an embedded file object",
    "launchURL":        "launchURL — opens external URL / potential data exfiltration",
    "app.exec":         "app.exec — executes arbitrary system commands",
    "util.stringToStream": "util.stringToStream — encodes data for exfiltration",
    "Net.HTTP":         "Net.HTTP — raw network request from PDF context",
    "nLaunch":          "nLaunch — silent execution flag",
    "this.submitForm":  "this.submitForm — sends PDF data to an external server",
    "app.openDoc":      "app.openDoc — opens an external document (dropper pattern)",
    "app.launchURL":    "app.launchURL — variant of launchURL",
    # obfuscation flags from js_classifier
    "eval()":           "eval() — dynamic code execution (common in shellcode loaders)",
    "unescape()":       "unescape() — runtime payload decoding",
    "unicode escape sequences (shellcode pattern)":
                        "Unicode escape sequences — shellcode pattern (%uXXXX encoding)",
    "extremely long line (>500 chars) — obfuscation":
                        "Extremely long single line — obfuscated content",
    "heap spray pattern detected":
                        "Heap spray pattern — memory corruption exploit preparation",
}


def _describe_js_api(api: str) -> str:
    return _JS_API_DESCRIPTIONS.get(api, f"{api} — suspicious JavaScript API")


def deep_analyze(
    file_path: Union[str, Path],
    sanitized_dir: Union[str, Path] = DEFAULT_SANITIZED_DIR,
    yara_rules=None,
    rules_dir: Path = DEFAULT_RULES_DIR,
) -> dict:
    """
    Run Stage-2 deep analysis on a file that reached the REVIEW bucket.

    Parameters
    ----------
    file_path     : path to the file (still at its original location — routing
                    happens in combined_scanner.py based on final_verdict)
    sanitized_dir : where Ghostscript writes the clean copy on SANITIZE
    yara_rules    : compiled yara.Rules object (passed in to avoid recompiling)
    rules_dir     : path to .yar files (used for ASCII-string page localization)
    """
    path = Path(file_path)
    sanitized_dir = Path(sanitized_dir)

    base_result: dict = {
        "deep_analysis_performed": False,
        "deep_skipped_reason": None,
        "js_verdict": "NONE",
        "js_apis_found": [],
        "js_obfuscation_score": 0,
        "embed_verdict": "NONE",
        "embed_details": [],
        "deep_recommendation": None,
        "deep_reason": "No deep analysis performed",
        "sanitized_path": None,
        "malicious_entities": [],
        "final_verdict": "INCONCLUSIVE",
        "final_verdict_reason": "Deep analysis was not attempted",
    }

    ext = path.suffix.lower()

    # ── Non-PDF: skip gracefully ───────────────────────────────────────
    # if ext != ".pdf":
    #     base_result["deep_skipped_reason"] = (
    #         f"{ext} files: macro/VBA deep analysis requires oletools (not in scope). "
    #         "File stays in review/ for manual triage."
    #     )
    #     base_result["final_verdict"] = "INCONCLUSIVE"
    #     base_result["final_verdict_reason"] = base_result["deep_skipped_reason"]
    #     return base_result
    # --- 1. EARLY EXIT FOR UNSUPPORTED FORMATS (.xlsx, .pptx, etc) ---
    if ext not in {".pdf", ".docx", ".docm", ".txt"}:
        base_result["deep_skipped_reason"] = (
            f"{ext} files: deep analysis not supported. "
            "File stays in review/ for manual triage."
        )
        base_result["final_verdict"] = "INCONCLUSIVE"
        base_result["final_verdict_reason"] = base_result["deep_skipped_reason"]
        return base_result

    # --- 2. DOCX / DOCM DEEP ANALYSIS ---
    if ext in {".docx", ".docm"}:
        logging.info(f"[deep_analyze] Running OOXML inspection on {path.name}")
        content_result = classify_docx_content(str(path))
        recommendation = content_result.get("recommendation", "PASS")
        
        if content_result.get("macro_verdict") == "PRESENT":
            base_result["malicious_entities"].append({
                "type": "VBA Macro", "severity": "HIGH", "page": "N/A", "detail": "vbaProject.bin found"
            })
        if content_result.get("embedded_objects"):
            base_result["malicious_entities"].append({
                "type": "Embedded OLE", "severity": "MEDIUM", "page": "N/A", 
                "detail": f"Objects: {content_result['embedded_objects']}"
            })
            
        if recommendation == "PASS":
            base_result["final_verdict"] = "CLEAN"
            base_result["final_verdict_reason"] = "Deep analysis cleared DOCX content."
        elif recommendation == "SANITIZE":
            sanitized_path = docx_sanitize(str(path), str(sanitized_dir))
            if sanitized_path:
                base_result["sanitized_path"] = sanitized_path
                base_result["final_verdict"] = "CLEAN_SANITIZED"
                base_result["final_verdict_reason"] = f"Macros/OLE objects stripped. Clean copy: {sanitized_path}."
            else:
                base_result["final_verdict"] = "MALICIOUS"
                base_result["final_verdict_reason"] = "DOCX sanitization failed — treating as MALICIOUS."
        elif recommendation == "BLOCK":
            base_result["final_verdict"] = "MALICIOUS"
            base_result["final_verdict_reason"] = content_result.get("reason", "DOCX analysis issued BLOCK.")
            
        return base_result

    # --- 3. TXT DEEP ANALYSIS ---
    if ext == ".txt":
        logging.info(f"[deep_analyze] Running plain-text validation on {path.name}")
        content_result = classify_txt_content(str(path))
        recommendation = content_result.get("recommendation", "PASS")
        
        if recommendation == "PASS":
            base_result["final_verdict"] = "CLEAN"
            base_result["final_verdict_reason"] = "Confirmed genuine plain text."
        else:
            base_result["final_verdict"] = "MALICIOUS"
            base_result["final_verdict_reason"] = content_result.get("reason", "TXT analysis issued BLOCK.")
            base_result["malicious_entities"].append({
                "type": "Disguised Executable", "severity": "HIGH", "page": "N/A", 
                "detail": f"Actual MIME: {content_result.get('mime', 'unknown')}"
            })
            
        return base_result

    # --- 4. PDF DEEP ANALYSIS ---
    # (Your existing PDF code will naturally continue below this point because it didn't hit any of the returns above!)

    # ── PDF: run full content classification ───────────────────────────
    base_result["deep_analysis_performed"] = True

    try:
        content_result = classify_pdf_content(str(path))
    except Exception as e:
        logging.error(f"[deep_analyze] pdf_content_classifier failed for {path}: {e}")
        base_result["final_verdict"] = "INCONCLUSIVE"
        base_result["final_verdict_reason"] = f"Classifier error: {e}"
        return base_result

    base_result["js_verdict"] = content_result.get("js_verdict", "NONE")
    base_result["js_apis_found"] = content_result.get("js_apis", [])
    base_result["js_obfuscation_score"] = content_result.get("js_obfusc_score", 0)
    base_result["embed_verdict"] = content_result.get("embed_verdict", "NONE")
    base_result["embed_details"] = [
        list(t) for t in content_result.get("embed_details", [])
    ]
    recommendation = content_result.get("recommendation", "PASS")
    base_result["deep_recommendation"] = recommendation
    base_result["deep_reason"] = content_result.get("reason", "")

    # Page localization — best-effort page attribution for the findings
    page_hits: dict = {}
    if yara_rules is not None:
        try:
            page_hits = locate_matches_by_page(yara_rules, str(path), rules_dir)
        except Exception as e:
            logging.warning(f"[deep_analyze] Page localization failed: {e}")

    # Build the malicious entities list
    base_result["malicious_entities"] = _build_malicious_entities(content_result, page_hits)
    base_result["page_breakdown"] = page_hits

    # ── Apply recommendation → final_verdict ──────────────────────────
    if recommendation == "PASS":
        base_result["final_verdict"] = "CLEAN"
        base_result["final_verdict_reason"] = (
            "Deep analysis found no malicious intent: " + content_result.get("reason", "")
        )

    elif recommendation == "SANITIZE":
        logging.info(f"[deep_analyze] Running Ghostscript sanitization on {path.name}")
        sanitized_dir.mkdir(parents=True, exist_ok=True)
        sanitized_path = ghostscript_sanitize(str(path), str(sanitized_dir))

        if sanitized_path:
            base_result["sanitized_path"] = sanitized_path
            base_result["final_verdict"] = "CLEAN_SANITIZED"
            base_result["final_verdict_reason"] = (
                "Suspicious content stripped by Ghostscript. "
                f"Clean copy: {sanitized_path}. "
                "Original file still present for audit."
            )
            logging.info(
                f"[deep_analyze] Sanitized OK: {path.name} → {sanitized_path}"
            )
        else:
            base_result["final_verdict"] = "MALICIOUS"
            base_result["final_verdict_reason"] = (
                "Ghostscript sanitization FAILED — cannot safely process this file. "
                "Treating as MALICIOUS."
            )
            logging.warning(
                f"[deep_analyze] Sanitization FAILED for {path.name} — treating as MALICIOUS"
            )

    elif recommendation == "BLOCK":
        base_result["final_verdict"] = "MALICIOUS"
        base_result["final_verdict_reason"] = (
            "Deep analysis issued BLOCK: " + content_result.get("reason", "")
        )

    else:
        # Unexpected recommendation value — treat as inconclusive
        base_result["final_verdict"] = "INCONCLUSIVE"
        base_result["final_verdict_reason"] = (
            f"Unexpected recommendation '{recommendation}' — manual triage required"
        )

    return base_result
