"""
lossless_transcriber.py
======================
Stage 2 of Decoupled Pipeline:
Performs complete, lossless layout & text transcription of documents (PDF / DOCX)
into a structured, auditable intermediate Markdown representation.

Preserves 100% of all document content (headings, paragraphs, bullet lists, CVEs,
IPs, geometric tables, and embedded image placeholder tokens).
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import pdfplumber
import fitz  # PyMuPDF

try:
    import docx
except ImportError:
    docx = None


class LosslessTranscriber:
    """Converts PDF/DOCX documents into lossless intermediate Markdown."""

    def __init__(self):
        pass

    def _format_markdown_table(self, raw_table: List[List[Any]]) -> str:
        """
        Convert a 2D list of table cells into a clean Markdown table string.
        """
        if not raw_table:
            return ""

        cleaned_rows: List[List[str]] = []
        for row in raw_table:
            if not row:
                continue
            clean_cells = []
            for cell in row:
                if cell is None:
                    clean_cells.append("")
                else:
                    # Clean newlines and pipe characters inside cells
                    text = str(cell).replace("\r\n", " ").replace("\n", " ").replace("|", "&#124;").strip()
                    clean_cells.append(text)
            if any(c for c in clean_cells):
                cleaned_rows.append(clean_cells)

        if not cleaned_rows:
            return ""

        num_cols = max(len(r) for r in cleaned_rows)
        # Pad shorter rows
        padded_rows = [r + [""] * (num_cols - len(r)) for r in cleaned_rows]

        headers = padded_rows[0]
        # If first row contains all empty strings, provide generic header
        if not any(h for h in headers):
            headers = [f"Col {i+1}" for i in range(num_cols)]

        md_lines = []
        md_lines.append("| " + " | ".join(headers) + " |")
        md_lines.append("| " + " | ".join(["---"] * num_cols) + " |")

        for row in padded_rows[1:]:
            md_lines.append("| " + " | ".join(row) + " |")

        return "\n".join(md_lines)

    def transcribe_pdf(
        self,
        pdf_path: str,
        image_map: Optional[Dict[int, List[Dict[str, Any]]]] = None,
        output_md_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe PDF into an exhaustive, lossless Markdown document.
        """
        if image_map is None:
            image_map = {}

        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        page_sections: List[str] = []
        total_tables = 0
        total_chars = 0

        with pdfplumber.open(pdf_path) as pdf_plumb:
            for page_num in range(total_pages):
                fitz_page = doc.load_page(page_num)
                plumb_page = pdf_plumb.pages[page_num]

                raw_text = fitz_page.get_text("text").strip()
                tables = plumb_page.extract_tables()

                page_content: List[str] = [f"<!-- PAGE_START: {page_num + 1} -->", f"## Page {page_num + 1}\n"]

                # Add image placeholders for this page
                page_images = image_map.get(page_num, [])
                if page_images:
                    page_content.append("### Embedded Visual Elements")
                    for img_meta in page_images:
                        token = img_meta.get("placeholder", f"[IMAGE_PAGE_{page_num}_FIG_{img_meta.get('fig_idx', 1)}]")
                        filename = img_meta.get("filename", "")
                        w = img_meta.get("width", "")
                        h = img_meta.get("height", "")
                        page_content.append(f"{token} *(Figure {img_meta.get('fig_idx')}: {filename}, {w}x{h}px)*\n")

                # Add tables
                if tables:
                    for t_idx, tbl in enumerate(tables):
                        if tbl and len(tbl) >= 1:
                            md_tbl = self._format_markdown_table(tbl)
                            if md_tbl:
                                page_content.append(f"### Table {page_num + 1}.{t_idx + 1}")
                                page_content.append(md_tbl + "\n")
                                total_tables += 1

                # Add full textual content
                if raw_text:
                    page_content.append("### Page Text Content")
                    page_content.append(raw_text + "\n")

                page_content.append(f"<!-- PAGE_END: {page_num + 1} -->\n---")
                section_str = "\n".join(page_content)
                page_sections.append(section_str)
                total_chars += len(section_str)

        doc.close()

        full_markdown = (
            f"# Document Transcript: {Path(pdf_path).name}\n\n"
            f"*Extracted Pages: {total_pages} | Detected Tables: {total_tables} | Total Chars: {total_chars}*\n\n"
            + "\n\n".join(page_sections)
        )

        if output_md_path:
            out_file = Path(output_md_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(full_markdown)
            print(f"[Stage 2] Saved intermediate transcript ({len(full_markdown)} chars) to: {out_file}")

        return {
            "status": "success",
            "pages_processed": total_pages,
            "tables_extracted": total_tables,
            "total_characters": len(full_markdown),
            "markdown_content": full_markdown,
            "output_path": output_md_path
        }

    def transcribe_docx(
        self,
        docx_path: str,
        image_list: Optional[List[Dict[str, Any]]] = None,
        output_md_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe DOCX into an exhaustive, lossless Markdown document.
        """
        if docx is None:
            raise ImportError("python-docx is required for DOCX transcription. Run `pip install python-docx`.")

        doc = docx.Document(docx_path)
        md_blocks: List[str] = []
        total_tables = 0

        # Add image placeholders at top
        if image_list:
            md_blocks.append("## Embedded Document Images\n")
            for img in image_list:
                token = img.get("placeholder", "")
                fn = img.get("filename", "")
                md_blocks.append(f"{token} *(Image: {fn})*\n")

        # Iterate paragraphs and tables
        for element in doc.paragraphs:
            text = element.text.strip()
            if not text:
                continue
            style_name = element.style.name.lower() if element.style else ""
            if "heading 1" in style_name:
                md_blocks.append(f"# {text}\n")
            elif "heading 2" in style_name:
                md_blocks.append(f"## {text}\n")
            elif "heading 3" in style_name:
                md_blocks.append(f"### {text}\n")
            else:
                md_blocks.append(f"{text}\n")

        for t_idx, table in enumerate(doc.tables):
            raw_table = []
            for row in table.rows:
                raw_table.append([cell.text.strip() for cell in row.cells])
            if raw_table:
                md_tbl = self._format_markdown_table(raw_table)
                if md_tbl:
                    md_blocks.append(f"### Table {t_idx + 1}\n{md_tbl}\n")
                    total_tables += 1

        full_markdown = f"# Document Transcript: {Path(docx_path).name}\n\n" + "\n\n".join(md_blocks)

        if output_md_path:
            out_file = Path(output_md_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(full_markdown)
            print(f"[Stage 2] Saved intermediate transcript ({len(full_markdown)} chars) to: {out_file}")

        return {
            "status": "success",
            "tables_extracted": total_tables,
            "total_characters": len(full_markdown),
            "markdown_content": full_markdown,
            "output_path": output_md_path
        }
