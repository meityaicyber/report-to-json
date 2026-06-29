import os

# MIME types safe to pass through as embedded files
SAFE_EMBED_TYPES = {
    "image/jpeg",
    "image/png",
    "image/tiff",
    "image/gif",
    "application/xml",
    "text/xml",
    "text/plain",
    "application/json",
    "font/ttf",
    "font/otf",
    "application/octet-stream",
}

# MIME types that are always dangerous as embedded files
DANGEROUS_EMBED_TYPES = {
    "application/x-msdownload",
    "application/x-dosexec",
    "application/x-sharedlib",
    "application/javascript",
    "application/x-sh",
    "application/x-python",
    "application/x-perl",
    "application/x-ruby",
    "application/zip",
    "application/x-rar-compressed",
    "application/x-7z-compressed",
}

EXT_MIME_FALLBACK = {
    ".exe": "application/x-msdownload",
    ".dll": "application/x-sharedlib",
    ".js":  "application/javascript",
    ".sh":  "application/x-sh",
    ".py":  "application/x-python",
    ".zip": "application/zip",
    ".xml": "application/xml",
    ".jpg": "image/jpeg",
    ".png": "image/png",
    ".ttf": "font/ttf",
}


def classify_embedded_file(file_bytes, filename=""):
    """
    Classify an embedded file extracted from a PDF.
    Uses python-magic if available, falls back to extension mapping.

    Returns:
        verdict : "SAFE" | "DANGEROUS" | "UNKNOWN"
        mime    : detected MIME type string
    """
    mime = "unknown"

    try:
        import magic
        mime = magic.from_buffer(file_bytes, mime=True)
    except ImportError:
        ext = os.path.splitext(filename)[1].lower()
        mime = EXT_MIME_FALLBACK.get(ext, "unknown")

    if mime in DANGEROUS_EMBED_TYPES:
        return "DANGEROUS", mime
    if mime in SAFE_EMBED_TYPES:
        return "SAFE", mime
    return "UNKNOWN", mime