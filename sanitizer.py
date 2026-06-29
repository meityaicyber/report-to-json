import os
import shutil
import logging
import subprocess

SANITIZED_DIR = "sanitized"


def ghostscript_sanitize(input_pdf, output_dir=SANITIZED_DIR):
    """
    Sanitize a PDF using Ghostscript.
    Strips JS, actions, embedded executables.
    Preserves text, images, fonts, tables.

    Returns output path on success, None on failure.
    """
    if not shutil.which("gs"):
        logging.error("Ghostscript (gs) not found. Cannot sanitize.")
        return None

    os.makedirs(output_dir, exist_ok=True)
    filename    = f"sanitized_{os.path.basename(input_pdf)}"
    output_path = os.path.join(output_dir, filename)

    result = subprocess.run([
        "gs",
        "-dBATCH",
        "-dNOPAUSE",
        "-dNOJAVASCRIPT",
        "-dNOAUTOROTATEPAGES",
        "-dNOSAFER",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-sOutputFile={output_path}",
        input_pdf
    ], capture_output=True, text=True, timeout=60)

    if result.returncode != 0:
        logging.error(f"Ghostscript failed for {input_pdf}:\n{result.stderr}")
        return None

    logging.info(f"Sanitized PDF written: {output_path}")
    return output_path