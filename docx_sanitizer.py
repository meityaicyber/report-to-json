import os
import shutil
import zipfile
import logging

SANITIZED_DIR = "sanitized"


def docx_sanitize(input_docx, output_dir=SANITIZED_DIR):
    """
    Sanitize a .docx by rebuilding the zip container with macro
    (vbaProject.bin) and embedded OLE objects removed.

    This does NOT use Ghostscript -- .docx is OOXML/zip, not PDF,
    so Ghostscript has no knowledge of its internals. Instead this
    rewrites the zip, dropping the dangerous parts entry by entry.

    Returns output path on success, None on failure.
    """
    os.makedirs(output_dir, exist_ok=True)
    filename    = f"sanitized_{os.path.basename(input_docx)}"
    output_path = os.path.join(output_dir, filename)

    # Parts we strip out on sanitize.
    strip_prefixes = ("word/embeddings/",)
    strip_exact    = {"word/vbaProject.bin"}

    try:
        with zipfile.ZipFile(input_docx, "r") as zin:
            names = zin.namelist()

            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zout:
                for name in names:
                    if name in strip_exact:
                        continue
                    if any(name.startswith(p) for p in strip_prefixes):
                        continue

                    data = zin.read(name)

                    # Also neutralize external template refs inside
                    # settings.xml.rels rather than dropping the file
                    # entirely (dropping it can corrupt the document).
                    if name == "word/_rels/settings.xml.rels":
                        text = data.decode("utf-8", errors="ignore")
                        if "http://" in text or "https://" in text:
                            # Replace remote target with a harmless
                            # same-document placeholder reference.
                            import re
                            text = re.sub(
                                r'Target="https?://[^"]*"',
                                'Target="NULL"',
                                text
                            )
                            data = text.encode("utf-8")

                    zout.writestr(name, data)

    except Exception as e:
        logging.error(f"docx sanitization failed for {input_docx}: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return None

    logging.info(f"Sanitized docx written: {output_path}")
    return output_path