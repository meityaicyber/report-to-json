import os
from embed_classifier import classify_embedded_file


def classify_txt_content(txt_path):
    """
    Check whether a .txt file is genuinely plain text, or a
    disguised script/binary wearing a .txt extension.

    Reuses classify_embedded_file()'s MIME logic -- a .txt file
    is just a single-file case of the same problem embedded
    files inside PDFs already solve.

    Returns dict:
        mime_verdict   : "SAFE" | "DANGEROUS" | "UNKNOWN"
        mime           : detected MIME type
        recommendation : "PASS" | "BLOCK"
        reason         : human-readable explanation
    """
    result = {
        "mime_verdict"  : "UNKNOWN",
        "mime"          : "unknown",
        "recommendation": "PASS",
        "reason"        : "File content matches plain text"
    }

    try:
        with open(txt_path, "rb") as f:
            file_bytes = f.read()
    except Exception as e:
        result["recommendation"] = "BLOCK"
        result["reason"]         = f"Could not read file: {e}"
        return result

    verdict, mime = classify_embedded_file(file_bytes, os.path.basename(txt_path))
    result["mime_verdict"] = verdict
    result["mime"]         = mime

    if verdict == "DANGEROUS":
        result["recommendation"] = "BLOCK"
        result["reason"]         = f".txt file content is actually '{mime}' — disguised file extension"
    elif verdict == "UNKNOWN" and mime != "text/plain":
        result["recommendation"] = "BLOCK"
        result["reason"]         = f".txt file content type could not be confirmed as text (detected: '{mime}')"
    else:
        result["reason"] = f"Confirmed plain text content (mime: {mime})"

    return result