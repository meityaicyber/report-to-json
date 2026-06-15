"""
PDF to Markdown converter.
Extracts content from PDF files and converts to normalized Markdown format.
"""

import re
from typing import List, Dict, Any, Tuple, Optional, Set
import pdfplumber
import pymupdf
from pathlib import Path


class PDFToMarkdownConverter:
    """Convert PDF documents to raw Markdown format."""

    def __init__(self):
        self.image_counter = 0
        self.artifact_cleanup_regex = re.compile(r'(?<=[a-z])\s(?=[a-z]{1,3}\b)')
        # Patterns that should NEVER be treated as headings
        self._non_heading_patterns = [
            re.compile(r'^\d+$'),                                   # Pure numbers
            re.compile(r'^\d+\.\d+'),                               # Version numbers / decimals
            re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'),    # IP addresses
            re.compile(r'^https?://'),                               # URLs
            re.compile(r'^CVE-', re.IGNORECASE),                    # CVE IDs
            re.compile(r'^CWE-', re.IGNORECASE),                    # CWE IDs
            re.compile(r'^\w+@\w+'),                                # Email addresses
            re.compile(r'^N/?A$', re.IGNORECASE),                   # NA / N/A
            re.compile(r'^\d+\s'),                                  # Lines starting with a number + space (table rows)
            re.compile(r'^(Yes|No|Open|Closed|New|Repeat)$', re.IGNORECASE),  # Status values
            re.compile(r'^\|'),                                     # Table row fragments
            re.compile(r'^---'),                                    # Separator lines
            re.compile(r'^\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}'),       # Dates
            re.compile(r'^(Low|Medium|High|Critical)$', re.IGNORECASE),  # Severity values
            re.compile(r'^\d+\s*KB', re.IGNORECASE),                # File sizes
        ]

    def convert(self, pdf_path: str) -> str:
        """
        Convert PDF file to raw Markdown string.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Raw Markdown string ready for normalization
        """
        self.image_counter = 0
        markdown_parts = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_md = self._process_page_pdfplumber(page, page_num)
                    if page_md:
                        markdown_parts.append(page_md)
        except Exception as e:
            print(f"Warning: pdfplumber failed on {pdf_path}, falling back to pymupdf: {e}")
            markdown_parts = self._convert_with_pymupdf(pdf_path)
        
        return '\n\n'.join(markdown_parts)

    def _process_page_pdfplumber(self, page, page_num: int) -> str:
        """
        Process a single page using pdfplumber.
        
        Key fix: Extract tables first, then extract text EXCLUDING table regions
        to avoid duplicate content.
        """
        parts = []
        
        # Add page marker
        parts.append(f'<!-- page {page_num} -->')
        
        # Extract tables and their bounding boxes
        tables = page.find_tables()
        table_bboxes = []
        
        if tables:
            for table in tables:
                # Record the bounding box of each table
                table_bboxes.append(table.bbox)
                # Extract and format the table
                table_data = table.extract()
                if table_data:
                    table_md = self._format_table(table_data)
                    if table_md:
                        parts.append(table_md)
        
        # Extract text EXCLUDING table regions to avoid duplication
        text = self._extract_text_excluding_tables(page, table_bboxes)
        if text:
            text_md = self._process_text_block(text)
            if text_md:
                parts.append(text_md)
        
        # Extract images
        images = page.images
        for img_idx, img in enumerate(images):
            self.image_counter += 1
            parts.append(f'<!-- IMAGE_PLACEHOLDER: [image {self.image_counter}] -->')
        
        return '\n'.join(parts)

    def _extract_text_excluding_tables(self, page, table_bboxes: List[tuple]) -> str:
        """
        Extract text from page while excluding regions covered by tables.
        This prevents duplicate content where table data appears both as 
        a GFM table and as raw text.
        
        Args:
            page: pdfplumber page object
            table_bboxes: List of (x0, y0, x1, y1) bounding boxes for tables
            
        Returns:
            Text content with table regions excluded
        """
        if not table_bboxes:
            # No tables on this page, extract all text normally
            return page.extract_text() or ''
        
        # Get all words on the page with their positions
        words = page.extract_words(keep_blank_chars=False, extra_attrs=['top', 'bottom'])
        if not words:
            return ''
        
        # Filter out words that fall within any table bounding box
        filtered_words = []
        for word in words:
            word_in_table = False
            for bbox in table_bboxes:
                tx0, ty0, tx1, ty1 = bbox
                # Check if the word's vertical center falls within the table bbox
                word_center_y = (word['top'] + word['bottom']) / 2
                word_center_x = (word['x0'] + word['x1']) / 2
                if (ty0 - 2 <= word_center_y <= ty1 + 2 and 
                    tx0 - 2 <= word_center_x <= tx1 + 2):
                    word_in_table = True
                    break
            if not word_in_table:
                filtered_words.append(word)
        
        if not filtered_words:
            return ''
        
        # Reconstruct text from filtered words, grouping by line (similar y-position)
        lines = []
        current_line_words = [filtered_words[0]]
        
        for word in filtered_words[1:]:
            # If the word is on a different line (y position differs by > 3 points)
            if abs(word['top'] - current_line_words[-1]['top']) > 3:
                # Finish current line
                line_text = ' '.join(w['text'] for w in current_line_words)
                lines.append(line_text)
                current_line_words = [word]
            else:
                current_line_words.append(word)
        
        # Don't forget the last line
        if current_line_words:
            line_text = ' '.join(w['text'] for w in current_line_words)
            lines.append(line_text)
        
        return '\n'.join(lines)

    def _convert_with_pymupdf(self, pdf_path: str) -> List[str]:
        """Fallback conversion using pymupdf."""
        parts = []
        doc = pymupdf.open(pdf_path)
        
        for page_num, page in enumerate(doc, 1):
            page_parts = []
            page_parts.append(f'<!-- page {page_num} -->')
            
            # Extract text
            text = page.get_text()
            if text:
                text_md = self._process_text_block(text)
                if text_md:
                    page_parts.append(text_md)
            
            # Extract images
            image_list = page.get_images()
            for img_idx, img in enumerate(image_list):
                self.image_counter += 1
                page_parts.append(f'<!-- IMAGE_PLACEHOLDER: [image {self.image_counter}] -->')
            
            parts.append('\n'.join(page_parts))
        
        doc.close()
        return parts

    def _process_text_block(self, text: str) -> str:
        """Process text block and identify heading candidates."""
        lines = []
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Clean artifacts
            line = self.artifact_cleanup_regex.sub('', line)
            
            # Detect heading candidates (with much stricter rules)
            if self._is_heading_candidate(line):
                lines.append(f'<!-- HEADING_CANDIDATE: {line} -->')
            else:
                lines.append(line)
        
        return '\n'.join(lines)

    def _is_heading_candidate(self, line: str) -> bool:
        """
        Check if line should be marked as heading candidate.
        
        Strict rules to avoid promoting table cell fragments, IP addresses,
        CVE/CWE IDs, and other non-heading content.
        """
        # Must be under 80 chars
        if len(line) > 80:
            return False
        
        # Must be at least 3 characters
        if len(line) < 3:
            return False
        
        # Check against all non-heading patterns
        for pattern in self._non_heading_patterns:
            if pattern.match(line):
                return False
        
        # ALL CAPS detection (strongest heading signal)
        if line.isupper() and len(line) > 5 and len(line.split()) >= 2:
            # Must have at least 2 words and > 5 chars to be a real heading
            return True
        
        # Bold-style markers from PDF (text that appears in a larger font)
        # Only promote if it looks like a genuine section title:
        # - Starts with a letter
        # - At least 2 words  
        # - Does not contain colons with values (like "Key: Value")
        # - Does not end with punctuation that suggests a sentence
        if (len(line.split()) >= 2 and 
            len(line.split()) <= 8 and
            line[0].isalpha() and
            not line.endswith(('.', '?', '!', ',', ';')) and
            ':' not in line and
            not any(c.isdigit() for c in line[:3])):
            # Additional checks: must not look like a data row
            words = line.split()
            # If most "words" are single chars or numbers, it's data not a heading
            non_word_count = sum(1 for w in words if len(w) <= 1 or w.replace('.', '').isdigit())
            if non_word_count < len(words) / 2:
                return True
        
        return False

    def _format_table(self, table: List[List[str]]) -> str:
        """Format extracted table as GFM markdown."""
        if not table or len(table) == 0:
            return ''
        
        # Clean table cells
        cleaned_table = []
        for row in table:
            cleaned_row = []
            for cell in row:
                if cell is None:
                    cell_text = ''
                else:
                    cell_text = str(cell).strip()
                    # Clean artifacts
                    cell_text = self.artifact_cleanup_regex.sub('', cell_text)
                    # Collapse internal newlines to spaces (multi-line cells)
                    cell_text = re.sub(r'\s*\n\s*', ' ', cell_text)
                cleaned_row.append(cell_text)
            cleaned_table.append(cleaned_row)
        
        # Skip if all cells empty
        if all(all(not cell for cell in row) for row in cleaned_table):
            return ''
        
        # Check if should be key-value format (2 columns, short left cells)
        if len(cleaned_table[0]) == 2 and self._is_kv_table(cleaned_table):
            return self._format_as_kv_block(cleaned_table)
        
        # Format as GFM table
        return self._format_as_gfm_table(cleaned_table)

    def _is_kv_table(self, table: List[List[str]]) -> bool:
        """Check if table looks like key-value format."""
        if not table or len(table) < 2:
            return False
        
        short_count = 0
        for row in table[1:]:  # Skip header
            if row and len(row[0]) < 40 and len(row[0].split()) <= 3:
                short_count += 1
        
        return short_count >= (len(table) - 1) * 0.6

    def _format_as_kv_block(self, table: List[List[str]]) -> str:
        """Format as key-value block."""
        lines = []
        for row in table[1:]:  # Skip header
            if len(row) >= 2:
                key = row[0].strip()
                value = row[1].strip()
                if key:
                    lines.append(f'**{key}**: {value}')
        
        return '\n'.join(lines)

    def _format_as_gfm_table(self, table: List[List[str]]) -> str:
        """Format as GFM markdown table."""
        if not table:
            return ''
        
        lines = []
        
        # Header row
        headers = table[0]
        lines.append('| ' + ' | '.join(headers) + ' |')
        
        # Separator
        separator = '|' + '|'.join([' --- '] * len(headers)) + '|'
        lines.append(separator)
        
        # Data rows
        for row in table[1:]:
            # Pad if needed
            while len(row) < len(headers):
                row.append('')
            lines.append('| ' + ' | '.join(row[:len(headers)]) + ' |')
        
        return '\n'.join(lines)
