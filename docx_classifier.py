import os
import zipfile
import logging


def classify_docx_content(docx_path):
    """
    Inspect a .docx file (which is a ZIP/OOXML container) for active content:
    VBA macros, external template injection, and embedded OLE objects.

    Returns dict:
        macro_verdict     : "NONE" | "PRESENT"
        external_ref      : "NONE" | "FOUND"
        embedded_objects  : list of embedded object filenames
        recommendation    : "PASS" | "SANITIZE" | "BLOCK"
        reason            : human-readable explanation
    """
    result = {
        "macro_verdict"    : "NONE",
        "external_ref"     : "NONE",
        "embedded_objects" : [],
        "recommendation"   : "PASS",
        "reason"           : "No active content detected"
    }

    if not zipfile.is_zipfile(docx_path):
        result["recommendation"] = "BLOCK"
        result["reason"]         = "File has .docx extension but is not a valid zip/OOXML container"
        return result

    try:
        with zipfile.ZipFile(docx_path) as z:
            names = z.namelist()

            # ── VBA macros ────────────────────────────────────────
            # A macro-enabled document always contains this part,
            # regardless of whether the extension is .docx or .docm.
            if "word/vbaProject.bin" in names:
                result["macro_verdict"]  = "PRESENT"
                result["recommendation"] = "BLOCK"
                result["reason"]         = "VBA macro project (vbaProject.bin) found — macros are never safe to auto-pass"

            # ── Remote template injection ──────────────────────────
            # settings.xml.rels can point document.xml's template
            # reference at an external URL, which Word will silently
            # fetch and execute on open ("template injection").
            rels_path = "word/_rels/settings.xml.rels"
            if rels_path in names:
                try:
                    rels_xml = z.read(rels_path).decode("utf-8", errors="ignore")
                    if "http://" in rels_xml or "https://" in rels_xml:
                        result["external_ref"] = "FOUND"
                        if result["recommendation"] != "BLOCK":
                            result["recommendation"] = "BLOCK"
                            result["reason"] = "External template reference found in settings.xml.rels (possible template injection)"
                        else:
                            result["reason"] += " | External template reference also found"
                except Exception as e:
                    logging.warning(f"Could not read {rels_path} in {docx_path}: {e}")

            # ── Embedded OLE objects ────────────────────────────────
            # word/embeddings/*.bin can wrap an arbitrary executable
            # disguised as an "embedded spreadsheet" or similar.
            embedded = [n for n in names if n.startswith("word/embeddings/")]
            if embedded:
                result["embedded_objects"] = embedded
                if result["recommendation"] == "PASS":
                    result["recommendation"] = "SANITIZE"
                    result["reason"] = f"Embedded OLE object(s) found: {embedded} — sanitize as precaution"
                else:
                    result["reason"] += f" | Embedded OLE object(s) also found: {embedded}"

    except Exception as e:
        result["recommendation"] = "BLOCK"
        result["reason"]         = f"Could not parse .docx structure: {e}"

    return result