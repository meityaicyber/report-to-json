#!/usr/bin/env python3
"""
pdf_page_locator.py
====================
Best-effort localization of WHICH PAGE of a PDF a YARA match occurred on.

Why this is non-trivial:
1. YARA reports a byte offset into the RAW file. For a compressed PDF
   that offset points into Flate-compressed bytes and is meaningless
   to a human.
2. Even after decompressing a page's content stream, PDF text is
   stored as escaped string literals - "(" "\" become "\\(" "\\\\" -
   so a literal byte-for-byte match against the *logical* string (the
   pattern in our .yar rules) can silently fail even though the text
   is right there on the page.

This module therefore uses two complementary techniques per page:
  (a) Re-run the compiled YARA ruleset against the page's raw decoded
      content-stream bytes via rules.match(data=...) - catches
      non-text / binary patterns (hex byte signatures, raw operators)
      exactly as YARA would see them.
  (b) Search the page's pypdf-extracted *logical* text for any
      printable-ASCII string defined in the ruleset's `strings:`
      sections - catches human-readable text matches regardless of
      PDF string-escaping, since extract_text() already un-escapes it.

Matches that live in document-level structures (the /Names catalog
tree, an /EmbeddedFile stream, /OpenAction in the catalog) are not
part of any single page's content and are reported as "document-level"
rather than a fabricated page number.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Set

import yara
from pypdf import PdfReader


def _extract_ascii_string_patterns(rules_dir: Path) -> Dict[str, List[str]]:
    """
    Parses each .yar file's `strings:` section for plain double-quoted
    ASCII literals (e.g. $eicar = "...") so they can be searched for in
    pypdf's decoded page text. Hex patterns ({ 4D 5A ... }) and regexes
    are intentionally skipped here - those are handled by the raw
    content-stream YARA re-scan instead.

    Returns {rule_name: [literal_string, ...]}.
    """
    pattern = re.compile(r'rule\s+(\w+)|^\s*\$\w+\s*=\s*"((?:[^"\\]|\\.)*)"', re.MULTILINE)
    rule_strings: Dict[str, List[str]] = {}
    current_rule = None

    for yar_file in list(rules_dir.glob("*.yar")) + list(rules_dir.glob("*.yara")):
        text = yar_file.read_text(errors="ignore")
        for match in pattern.finditer(text):
            rule_name, literal = match.groups()
            if rule_name:
                current_rule = rule_name
                rule_strings.setdefault(current_rule, [])
            elif literal and current_rule:
                decoded = literal.encode().decode("unicode_escape", errors="ignore")
                if len(decoded) >= 6:  # skip trivially short/noisy fragments
                    rule_strings[current_rule].append(decoded)

    return rule_strings


def locate_matches_by_page(
    rules: "yara.Rules", pdf_path: str, rules_dir: Path
) -> Dict[int, List[str]]:
    """
    Returns {page_number (1-indexed): [rule_name, ...]} for every page
    where a match is genuinely attributable to that page's content,
    via either raw-stream YARA re-scan or decoded-text search.
    """
    page_hits: Dict[int, Set[str]] = {}
    ascii_patterns = _extract_ascii_string_patterns(rules_dir)

    try:
        reader = PdfReader(pdf_path)
    except Exception:
        return {}

    for page_num, page in enumerate(reader.pages, start=1):
        hits: Set[str] = set()

        # Strategy (a): raw decoded content-stream bytes vs full ruleset
        try:
            contents = page.get_contents()
            data = contents.get_data() if contents is not None else None
        except Exception:
            data = None

        if data:
            try:
                for m in rules.match(data=data):
                    hits.add(m.rule)
            except yara.Error:
                pass

        # Strategy (b): decoded logical text vs ASCII string literals
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""

        if text:
            for rule_name, literals in ascii_patterns.items():
                if any(lit in text for lit in literals):
                    hits.add(rule_name)

        if hits:
            page_hits[page_num] = hits

    return {p: sorted(r) for p, r in page_hits.items()}


def describe_locations(page_hits: Dict[int, List[str]], all_matched_rule_names: List[str]) -> str:
    """Human-readable summary distinguishing page-localized vs document-level hits."""
    located_rules = {r for rule_list in page_hits.values() for r in rule_list}
    doc_level = sorted(set(all_matched_rule_names) - located_rules)

    parts = [f"page {p} ({', '.join(rule_list)})" for p, rule_list in sorted(page_hits.items())]
    if doc_level:
        parts.append(f"document-level/not page-specific ({', '.join(doc_level)})")

    return "; ".join(parts) if parts else "no location data"


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from yara_scanner import compile_rules, DEFAULT_RULES_DIR

    if len(sys.argv) != 2:
        print("Usage: python pdf_page_locator.py <file.pdf>")
        sys.exit(1)

    compiled = compile_rules(DEFAULT_RULES_DIR)
    all_matches = compiled.match(filepath=sys.argv[1])
    all_names = [m.rule for m in all_matches]
    hits = locate_matches_by_page(compiled, sys.argv[1], DEFAULT_RULES_DIR)

    print(f"All rule matches: {all_names}")
    print(f"Per-page breakdown: {hits}")
    print(f"Summary: {describe_locations(hits, all_names)}")
