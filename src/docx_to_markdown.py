"""
DOCX to Markdown converter.
Extracts content from DOCX files and converts to normalized Markdown format.
"""

import re
from pathlib import Path
from typing import List, Tuple
from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table
from docx.oxml.shared import OxmlElement


class DOCXToMarkdownConverter:
    """Convert DOCX documents to raw Markdown format."""

    def __init__(self):
        self.image_counter = 0
        self.artifact_cleanup_regex = re.compile(r'(?<=[a-z])\s(?=[a-z]{1,3}\b)')

    def convert(self, docx_path: str) -> str:
        """
        Convert DOCX file to raw Markdown string.
        
        Args:
            docx_path: Path to DOCX file
            
        Returns:
            Raw Markdown string ready for normalization
        """
        self.image_counter = 0
        doc = Document(docx_path)
        
        markdown_parts = []
        
        # Walk document body in order (preserves paragraph/table interleaving)
        for element in doc.element.body:
            # Paragraphs
            if element.tag.endswith('p'):
                para = None
                # Find corresponding Paragraph object
                for p in doc.paragraphs:
                    if p._element is element:
                        para = p
                        break
                if para:
                    md = self._process_paragraph(para)
                    if md:
                        markdown_parts.append(md)
            
            # Tables
            elif element.tag.endswith('tbl'):
                table = None
                # Find corresponding Table object
                for t in doc.tables:
                    if t._element is element:
                        table = t
                        break
                if table:
                    md = self._process_table(table)
                    if md:
                        markdown_parts.append(md)
        
        return '\n\n'.join(markdown_parts)

    def _process_paragraph(self, para: Paragraph) -> str:
        """Process a paragraph and return Markdown representation."""
        text = para.text.strip()
        if not text:
            return ''
        
        # Clean cell artifacts (mid-word spaces)
        text = self.artifact_cleanup_regex.sub('', text)
        
        # Check for images in paragraph
        if self._paragraph_has_image(para):
            self._image_counter += 1
            return f'<!-- IMAGE_PLACEHOLDER: [image {self.image_counter}] -->'
        
        # Map Word heading styles to Markdown
        style_name = para.style.name if para.style else ''
        if style_name.startswith('Heading'):
            # Extract heading level: "Heading 1" -> 1, "Heading 2" -> 2, etc.
            try:
                level = int(style_name.split()[-1])
                heading_marker = '#' * level
                return f'{heading_marker} {text}'
            except (ValueError, IndexError):
                pass
        
        # Check if entire paragraph is bold and short -> HEADING_CANDIDATE
        if self._is_bold_paragraph(para) and len(text) < 80:
            return f'<!-- HEADING_CANDIDATE: {text} -->'
        
        # Preserve list bullets
        if para.style and para.style.name.startswith('List'):
            return f'- {text}'
        
        return text

    def _process_table(self, table: Table) -> str:
        """Process a table and return Markdown representation."""
        rows_data = []
        all_rows_empty = True
        
        for row in table.rows:
            row_data = []
            row_has_content = False
            
            for cell in row.cells:
                cell_text = self._process_table_cell(cell)
                if cell_text.strip():
                    row_has_content = True
                    all_rows_empty = False
                row_data.append(cell_text)
            
            if row_has_content:
                rows_data.append(row_data)
        
        if all_rows_empty or not rows_data:
            return ''
        
        # Check if table is 2 columns with short bold left cells (key-value pattern)
        if len(rows_data[0]) == 2 and self._is_kv_table(rows_data):
            return self._format_as_kv_block(rows_data)
        
        # Format as GFM table
        return self._format_as_gfm_table(rows_data)

    def _process_table_cell(self, cell) -> str:
        """Process a table cell and return text."""
        # Check for images
        if self._cell_has_image(cell):
            self._image_counter += 1
            return f'<!-- IMAGE_PLACEHOLDER: [image {self.image_counter}] -->'
        
        # Extract text from all paragraphs in cell
        text_parts = []
        for para in cell.paragraphs:
            text = para.text.strip()
            if text:
                # Clean artifacts
                text = self.artifact_cleanup_regex.sub('', text)
                text_parts.append(text)
        
        return ' '.join(text_parts)

    def _is_bold_paragraph(self, para: Paragraph) -> bool:
        """Check if entire paragraph is bold."""
        if not para.runs:
            return False
        
        for run in para.runs:
            if not run.bold:
                return False
        
        return True

    def _is_kv_table(self, rows_data: List[List[str]]) -> bool:
        """Check if table looks like a key-value table (2 cols, short bold left cells)."""
        if not rows_data or len(rows_data[0]) != 2:
            return False
        
        # Heuristic: if most left cells are short and bold-looking, treat as KV
        short_count = 0
        for row in rows_data:
            left_cell = row[0].strip()
            # Check if looks like a label (short, ends with colon or is all caps/short)
            if len(left_cell) < 40 and (left_cell.endswith(':') or len(left_cell.split()) <= 3):
                short_count += 1
        
        return short_count >= len(rows_data) * 0.6

    def _format_as_kv_block(self, rows_data: List[List[str]]) -> str:
        """Format table as key-value block."""
        lines = []
        for row in rows_data:
            key = row[0].strip()
            value = row[1].strip() if len(row) > 1 else ''
            lines.append(f'**{key}**: {value}')
        return '\n'.join(lines)

    def _format_as_gfm_table(self, rows_data: List[List[str]]) -> str:
        """Format table as GFM markdown table."""
        if not rows_data:
            return ''
        
        # Header
        headers = rows_data[0]
        lines = []
        lines.append('| ' + ' | '.join(headers) + ' |')
        
        # Separator
        separator = '|' + '|'.join([' --- '] * len(headers)) + '|'
        lines.append(separator)
        
        # Data rows
        for row in rows_data[1:]:
            # Pad row if needed
            while len(row) < len(headers):
                row.append('')
            lines.append('| ' + ' | '.join(row[:len(headers)]) + ' |')
        
        return '\n'.join(lines)

    def _paragraph_has_image(self, para: Paragraph) -> bool:
        """Check if paragraph contains images."""
        for run in para.runs:
            if self._run_has_image(run):
                return True
        return False

    def _run_has_image(self, run) -> bool:
        """Check if run contains images."""
        if run._element is None:
            return False
        
        # Look for drawing elements
        for child in run._element.iter():
            if 'drawing' in child.tag.lower() or 'pic' in child.tag.lower():
                return True
        
        return False

    def _cell_has_image(self, cell) -> bool:
        """Check if table cell contains images."""
        for para in cell.paragraphs:
            if self._paragraph_has_image(para):
                return True
        return False
