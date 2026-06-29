#!/usr/bin/env python3
"""
clamav_scanner.py
===================
ClamAV integration for the document pipeline - refactored from the
original standalone script. Fixes applied:

  - All paths resolved relative to the PROJECT ROOT (via __file__),
    not the current working directory, so it behaves the same
    whether you run `python src/clamav_scanner.py` from the project
    root or `python clamav_scanner.py` from inside src/.
  - Quarantine/log directories created with parents=True so first-run
    on a fresh checkout doesn't fail.
  - Optional `signature_db` parameter: pass a custom .ndb file (via
    `clamscan -d <db>`) for environments where `freshclam` cannot
    reach the ClamAV CDN (offline machines, CI runners, sandboxes
    behind an egress allowlist). See clamav_signatures/test_eicar.ndb
    for a worked example - this is a standard, documented ClamAV
    technique for self-testing without a network-fetched database,
    NOT a replacement for the real database in production.
  - Constructor no longer hard-requires clamscan at import time -
    raises a clear, actionable EnvironmentError instead so the
    combined pipeline can decide whether to hard-fail or degrade to
    YARA-only.

Install ClamAV itself (the `clamscan` binary is a system package, not
a pip package):
    macOS:          brew install clamav
    Ubuntu/Debian:  sudo apt install clamav clamav-freshclam
    Then either run `freshclam` (needs internet access to
    database.clamav.net) or pass signature_db= to use a custom/local
    signature file instead.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple, Union

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_QUARANTINE_DIR = PROJECT_ROOT / "quarantine"
DEFAULT_SIGNATURE_DB = PROJECT_ROOT / "clamav_signatures" / "test_eicar.ndb"
SCAN_TIMEOUT_SECONDS = 500


class ClamAVScanner:
    def __init__(
        self,
        quarantine_dir: Union[str, Path] = DEFAULT_QUARANTINE_DIR,
        update_db: bool = False,
        signature_db: Optional[Union[str, Path]] = None,
    ):
        self.quarantine_dir = Path(quarantine_dir)
        self.signature_db = Path(signature_db) if signature_db else None

        if not shutil.which("clamscan"):
            raise EnvironmentError(
                "clamscan not found on PATH. Install ClamAV first:\n"
                "  macOS:  brew install clamav\n"
                "  Ubuntu: sudo apt install clamav clamav-freshclam"
            )

        if update_db:
            self._update_database()

        # If no real database is present AND no custom signature_db was
        # given, fall back to the bundled test signature so the scanner
        # is still usable out of the box (clearly logged, not silent).
        if self.signature_db is None and not self._system_db_present():
            if DEFAULT_SIGNATURE_DB.exists():
                logging.warning(
                    "No ClamAV system database found (run freshclam to get "
                    "the real one). Falling back to the bundled test "
                    f"signature: {DEFAULT_SIGNATURE_DB}"
                )
                self.signature_db = DEFAULT_SIGNATURE_DB
            else:
                raise EnvironmentError(
                    "No ClamAV signature database available. Run "
                    "`freshclam` (needs internet access) or pass "
                    "signature_db= pointing at a .ndb file."
                )

        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"ClamAVScanner ready. Quarantine dir: {self.quarantine_dir}")
        if self.signature_db:
            logging.info(f"Using signature DB override: {self.signature_db}")

    @staticmethod
    def _system_db_present() -> bool:
        db_dir = Path("/var/lib/clamav")
        if not db_dir.exists():
            return False
        return any(db_dir.glob("*.cvd")) or any(db_dir.glob("*.cld"))

    def _update_database(self) -> None:
        """Update ClamAV signatures using freshclam (requires internet access)."""
        logging.info("Updating ClamAV signature database...")
        try:
            result = subprocess.run(
                ["freshclam"], capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                logging.info("Database updated successfully.")
            else:
                logging.warning(f"freshclam returned non-zero status:\n{result.stderr}")
        except FileNotFoundError:
            logging.warning("freshclam not found. Skipping database update.")
        except subprocess.TimeoutExpired:
            logging.warning("freshclam timed out. Proceeding with current database.")

    def scan_file(self, file_path: Union[str, Path]) -> Tuple[str, Union[str, dict]]:
        """
        Scan a single file using ClamAV.
        Returns:
            ("CLEAN",    output)
            ("INFECTED", {"malware": str, "raw_output": str})
            ("ERROR",    error_message)
        """
        cmd = ["clamscan", "--no-summary"]
        if self.signature_db:
            cmd += ["-d", str(self.signature_db)]
        cmd.append(str(file_path))

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=SCAN_TIMEOUT_SECONDS
            )
            output = result.stdout.strip()

            if result.returncode == 0:
                return "CLEAN", output

            elif result.returncode == 1:
                malware_name = "Unknown"
                try:
                    first_line = output.split("\n")[0]
                    if ":" in first_line and "FOUND" in first_line:
                        malware_name = first_line.split(":")[1].replace("FOUND", "").strip()
                except Exception:
                    pass
                return "INFECTED", {"malware": malware_name, "raw_output": output}

            else:
                return "ERROR", result.stderr.strip() or f"clamscan exited {result.returncode}"

        except subprocess.TimeoutExpired:
            return "ERROR", f"Scan timed out after {SCAN_TIMEOUT_SECONDS} seconds"
        except Exception as e:
            return "ERROR", str(e)

    def move_to_quarantine(self, file_path: Union[str, Path]) -> Optional[str]:
        """Move an infected file to the quarantine folder. Returns destination path or None."""
        file_path = Path(file_path)
        timestamp = int(time.time())
        destination = self.quarantine_dir / f"{timestamp}_{file_path.name}"
        try:
            shutil.move(str(file_path), str(destination))
            logging.warning(f"Quarantined: {file_path} -> {destination}")
            return str(destination)
        except Exception as e:
            logging.error(f"Failed to quarantine {file_path}: {e}")
            return None


class PDFStructuralAnalyzer:
    """Lightweight supplementary risk-scoring heuristic for PDFs (kept from
    the original script). Not part of the YARA/ClamAV decision matrix -
    surfaced as additional context only."""

    def analyze(self, pdf_path: Union[str, Path]) -> dict:
        from pypdf import PdfReader

        features = {
            "encrypted": False,
            "pages": 0,
            "javascript": False,
            "embedded_files": 0,
            "risk_score": 0,
            "risk_level": "LOW",
        }
        try:
            reader = PdfReader(str(pdf_path))
            features["encrypted"] = reader.is_encrypted
            features["pages"] = len(reader.pages)
            root = reader.trailer.get("/Root", {})

            if "/Names" in root:
                names = root["/Names"]
                if "/JavaScript" in names:
                    features["javascript"] = True
                    features["risk_score"] += 40
                if "/EmbeddedFiles" in names:
                    embedded = names["/EmbeddedFiles"]
                    try:
                        count = len(embedded.get("/Names", [])) // 2
                        features["embedded_files"] = count
                        features["risk_score"] += count * 30
                    except Exception:
                        pass

            if features["encrypted"]:
                features["risk_score"] += 20
            if features["pages"] > 500:
                features["risk_score"] += 10

            score = features["risk_score"]
            features["risk_level"] = "HIGH" if score >= 80 else "MEDIUM" if score >= 40 else "LOW"
            return features

        except Exception as e:
            return {"error": str(e), "risk_level": "UNKNOWN"}
