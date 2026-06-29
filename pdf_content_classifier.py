import logging
from pypdf import PdfReader
from js_classifier import classify_javascript
from embed_classifier import classify_embedded_file


def classify_pdf_content(pdf_path):
    """
    Deep-inspect a PDF's JavaScript and embedded files.
    Determines INTENT of active content, not just presence.

    Returns dict:
        js_verdict, js_apis, js_obfusc_score,
        embed_verdict, embed_details,
        recommendation : "PASS" | "SANITIZE" | "BLOCK"
        reason
    """
    result = {
        "js_verdict"      : "NONE",
        "js_apis"         : [],
        "js_obfusc_score" : 0,
        "embed_verdict"   : "NONE",
        "embed_details"   : [],
        "recommendation"  : "PASS",
        "reason"          : "No active content detected"
    }

    try:
        reader = PdfReader(pdf_path)
        root   = reader.trailer.get("/Root", {})
    except Exception as e:
        result["recommendation"] = "BLOCK"
        result["reason"]         = f"Could not parse PDF structure: {e}"
        return result

    names_dict = root.get("/Names", {})

    # ── JavaScript ────────────────────────────────────────────
    if "/JavaScript" in names_dict:
        js_code   = ""
        names_obj = names_dict["/JavaScript"]

        try:
            names_list = names_obj.get("/Names", [])
            for i in range(1, len(names_list), 2):
                js_obj = names_list[i].get_object()
                raw_js = js_obj.get("/JS", "")
                if hasattr(raw_js, "read_bytes"):
                    js_code += raw_js.read_bytes().decode("latin-1", errors="ignore")
                else:
                    js_code += str(raw_js)
        except Exception as e:
            logging.warning(f"Could not extract JS from {pdf_path}: {e}")
            result["js_verdict"]      = "UNKNOWN"
            result["recommendation"] = "SANITIZE"
            result["reason"]         = "JavaScript present but could not be extracted"

        if js_code:
            verdict, apis, score = classify_javascript(js_code)
            result["js_verdict"]      = verdict
            result["js_apis"]         = apis
            result["js_obfusc_score"] = score

            if verdict == "MALICIOUS":
                result["recommendation"] = "BLOCK"
                result["reason"]         = f"Malicious JavaScript detected: {apis}"
            elif verdict == "UNKNOWN":
                result["recommendation"] = "SANITIZE"
                result["reason"]         = "JavaScript intent unclear — sanitize as precaution"
            else:
                result["reason"] = f"JavaScript classified as benign form validation: {apis}"

    # ── Embedded Files ────────────────────────────────────────
    if "/EmbeddedFiles" in names_dict:
        embed_obj = names_dict["/EmbeddedFiles"]
        verdicts  = []

        try:
            names_list = embed_obj.get("/Names", [])
            for i in range(1, len(names_list), 2):
                filename = str(names_list[i - 1])
                try:
                    filespec   = names_list[i].get_object()
                    ef         = filespec.get("/EF", {})
                    stream_ref = ef.get("/F") or ef.get("/UF")
                    if stream_ref is None:
                        verdicts.append("UNKNOWN")
                        result["embed_details"].append((filename, "unknown", "UNKNOWN"))
                        continue

                    stream     = stream_ref.get_object()
                    # pypdf returns DecodedStreamObject / EncodedStreamObject;
                    # get_data() is the correct API for decompressed bytes.
                    # read_raw_bytes() only exists on pikepdf streams.
                    try:
                        file_bytes = stream.get_data()
                    except Exception:
                        file_bytes = bytes(stream)
                    verdict, mime = classify_embedded_file(file_bytes, filename)
                    verdicts.append(verdict)
                    result["embed_details"].append((filename, mime, verdict))

                except Exception as e:
                    logging.warning(f"Could not inspect embedded file '{filename}': {e}")
                    verdicts.append("UNKNOWN")
                    result["embed_details"].append((filename, "error", "UNKNOWN"))

        except Exception as e:
            logging.warning(f"Could not iterate embedded files in {pdf_path}: {e}")
            verdicts.append("UNKNOWN")

        if "DANGEROUS" in verdicts:
            result["embed_verdict"]  = "DANGEROUS"
            result["recommendation"] = "BLOCK"
            result["reason"] = (
                result["reason"] + " | Dangerous embedded file detected"
            ).lstrip(" | ")

        elif "UNKNOWN" in verdicts:
            result["embed_verdict"] = "MIXED"
            if result["recommendation"] == "PASS":
                result["recommendation"] = "SANITIZE"
                result["reason"] = (
                    result["reason"] + " | Embedded file type unclear — sanitize"
                ).lstrip(" | ")

        elif all(v == "SAFE" for v in verdicts):
            result["embed_verdict"] = "SAFE"
            if result["recommendation"] == "PASS":
                result["reason"] = (
                    result["reason"] + " | Embedded files classified as safe"
                ).lstrip(" | ")

    return result