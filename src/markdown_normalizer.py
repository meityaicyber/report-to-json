"""
Markdown normalizer.
Cleans and standardizes extracted Markdown for LLM ingestion.
"""

import re
import unicodedata
from typing import List, Tuple


class MarkdownNormalizer:
    """Normalize raw extracted Markdown to clean, consistent format."""

    def __init__(self):
        # Patterns that should NOT be headings even if marked as ##
        self._non_heading_patterns = [
            re.compile(r'^#+\s+\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'),   # IP addresses
            re.compile(r'^#+\s+\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+'), # IP:port
            re.compile(r'^#+\s+CVE-', re.IGNORECASE),                     # CVE IDs  
            re.compile(r'^#+\s+CWE-', re.IGNORECASE),                     # CWE IDs
            re.compile(r'^#+\s+https?://'),                                # URLs
            re.compile(r'^#+\s+\w+@\w+'),                                 # Emails
            re.compile(r'^#+\s*(Yes|No|Open|Closed|New|Repeat)\s*$', re.IGNORECASE),  # Status values
            re.compile(r'^#+\s+N/?A\s*$', re.IGNORECASE),                  # NA / N/A
            re.compile(r'^#+\s+(Low|Medium|High|Critical)\s*$', re.IGNORECASE),  # Severity
            re.compile(r'^#+\s+\d+\s+\w'),                                # Numbered data rows
            re.compile(r'^#+\s+•\s'),                                      # Bullet points misformatted as headings
            re.compile(r'^#+\s+\d+\s*$'),                                  # Pure numbers
            re.compile(r'^#+\s+PF\s+GGC', re.IGNORECASE),                  # Device names (common artifact)
            re.compile(r'^#+\s+Device\s*$', re.IGNORECASE),                # "Device" alone
        ]

    def normalize(self, raw_markdown: str) -> str:
        """
        Normalize raw markdown extracted from DOCX/PDF.
        
        Args:
            raw_markdown: Raw markdown from extractor
            
        Returns:
            Clean, normalized markdown ready for LLM
        """
        # Step 1: Strip page headers/footers
        text = self._strip_headers_footers(raw_markdown)
        
        # Step 2: Normalize Unicode
        text = self._normalize_unicode(text)
        
        # Step 3: Resolve HEADING_CANDIDATE markers
        text = self._resolve_heading_candidates(text)
        
        # Step 4: Demote false headings (IPs, CVEs, status values, etc.)
        text = self._demote_false_headings(text)
        
        # Step 5: Normalize heading levels
        text = self._normalize_heading_levels(text)
        
        # Step 6: Fix bullet points that got broken
        text = self._fix_bullet_points(text)
        
        # Step 7: Collapse excessive blank lines
        text = self._collapse_blank_lines(text)
        
        return text

    def _strip_headers_footers(self, text: str) -> str:
        """Remove header/footer markers and patterns."""
        lines = []
        
        for line in text.split('\n'):
            # Skip HEADER_FOOTER markers
            if '<!-- HEADER_FOOTER:' in line:
                continue
            
            # Skip page number patterns
            if re.match(r'^\s*Page\s+\d+\s+of\s+\d+\s*$', line, re.IGNORECASE):
                continue
            
            # Skip long dashes
            if re.match(r'^\s*-{10,}\s*$', line):
                continue
            
            # Skip repetitive separator lines
            if re.match(r'^\s*[=]{10,}\s*$', line):
                continue
            
            lines.append(line)
        
        return '\n'.join(lines)

    def _normalize_unicode(self, text: str) -> str:
        """Normalize Unicode characters."""
        # Em dash and en dash -> space-dash-space
        text = text.replace('\u2013', ' - ')  # en dash
        text = text.replace('\u2014', ' - ')  # em dash
        text = text.replace('\u2212', ' - ')  # minus sign
        
        # Smart quotes -> straight quotes
        text = text.replace('\u201c', '"')  # Left double
        text = text.replace('\u201d', '"')  # Right double
        text = text.replace('\u2018', "'")  # Left single
        text = text.replace('\u2019', "'")  # Right single
        text = text.replace('\u201a', "'")  # Single low
        text = text.replace('\u201e', '"')  # Double low
        
        # Non-breaking spaces -> regular spaces
        text = text.replace('\u00a0', ' ')
        text = text.replace('\u2000', ' ')  # En quad
        text = text.replace('\u2001', ' ')  # Em quad
        text = text.replace('\u2002', ' ')  # En space
        text = text.replace('\u2003', ' ')  # Em space
        text = text.replace('\u2004', ' ')  # Three-per-em space
        text = text.replace('\u2005', ' ')  # Four-per-em space
        text = text.replace('\u2006', ' ')  # Six-per-em space
        text = text.replace('\u2007', ' ')  # Figure space
        text = text.replace('\u2008', ' ')  # Punctuation space
        text = text.replace('\u2009', ' ')  # Thin space
        text = text.replace('\u200a', ' ')  # Hair space
        text = text.replace('\u202f', ' ')  # Narrow no-break space
        
        return text

    def _resolve_heading_candidates(self, text: str) -> str:
        """Resolve HEADING_CANDIDATE markers to ## headings."""
        lines = []
        
        for line in text.split('\n'):
            # Match HEADING_CANDIDATE markers
            match = re.match(r'^<!--\s*HEADING_CANDIDATE:\s*(.+?)\s*-->$', line)
            if match:
                heading_text = match.group(1).strip()
                
                # Check if this line is inside a table row (preceded by |)
                # Look back through previous lines to check context
                in_table = False
                for prev_line in reversed(lines[-5:]):  # Check last 5 lines
                    if prev_line.startswith('|'):
                        in_table = True
                        break
                    if prev_line.strip() == '':
                        break
                
                if in_table:
                    # Demote to bold text instead of heading
                    lines.append(f'**{heading_text}**')
                else:
                    # Convert to heading
                    lines.append(f'## {heading_text}')
            else:
                lines.append(line)
        
        return '\n'.join(lines)

    def _demote_false_headings(self, text: str) -> str:
        """
        Demote lines that have ## markers but are clearly not headings.
        For example: IP addresses, CVE/CWE IDs, status values, etc.
        """
        lines = []
        
        for line in text.split('\n'):
            demoted = False
            for pattern in self._non_heading_patterns:
                if pattern.match(line):
                    # Remove heading markers, keep the text
                    cleaned = re.sub(r'^#+\s+', '', line)
                    # If it looks like a bullet point, format it properly
                    if cleaned.startswith('•'):
                        lines.append(cleaned)
                    else:
                        lines.append(f'  {cleaned}')
                    demoted = True
                    break
            
            if not demoted:
                lines.append(line)
        
        return '\n'.join(lines)

    def _normalize_heading_levels(self, text: str) -> str:
        """Normalize heading levels to consistent structure."""
        # Count heading level occurrences (only genuine headings after demotion)
        level_counts = {}
        for line in text.split('\n'):
            match = re.match(r'^(#+)\s', line)
            if match:
                level = len(match.group(1))
                level_counts[level] = level_counts.get(level, 0) + 1
        
        if not level_counts:
            return text
        
        # Find most frequent level (assume it's the main level)
        most_frequent_level = max(level_counts, key=level_counts.get)
        
        # Calculate shift to map most frequent level to ##
        shift = 2 - most_frequent_level
        
        # Apply mapping
        lines = []
        for line in text.split('\n'):
            match = re.match(r'^(#+)\s(.+)$', line)
            if match:
                old_level = len(match.group(1))
                heading_text = match.group(2)
                
                # Apply shift
                new_level = old_level + shift
                # Clamp to valid range [1, 3]
                new_level = max(1, min(new_level, 3))
                
                new_marker = '#' * new_level
                lines.append(f'{new_marker} {heading_text}')
            else:
                lines.append(line)
        
        return '\n'.join(lines)

    def _fix_bullet_points(self, text: str) -> str:
        """Fix bullet points that may have been broken during extraction."""
        lines = []
        for line in text.split('\n'):
            # Convert • to - for consistency
            if line.strip().startswith('•'):
                line = line.replace('•', '-', 1)
            lines.append(line)
        return '\n'.join(lines)

    def _collapse_blank_lines(self, text: str) -> str:
        """Collapse excessive consecutive blank lines (max 2)."""
        lines = text.split('\n')
        result = []
        blank_count = 0
        
        for line in lines:
            if line.strip() == '':
                blank_count += 1
                if blank_count <= 2:
                    result.append(line)
            else:
                blank_count = 0
                result.append(line)
        
        return '\n'.join(result)
