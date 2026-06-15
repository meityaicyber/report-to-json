"""
Phase 1 verification script.
Test PDF extraction and normalization on real documents.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pdf_to_markdown import PDFToMarkdownConverter
from markdown_normalizer import MarkdownNormalizer


def main():
    """Test Phase 1 on sample PDFs."""
    
    # Test PDFs
    test_pdfs = [
        r'../Network Report/1-Audit Report.pdf',
        r'../VAPT-API/1-report.pdf',
    ]
    
    pdf_converter = PDFToMarkdownConverter()
    normalizer = MarkdownNormalizer()
    
    for pdf_path in test_pdfs:
        full_path = os.path.join(os.path.dirname(__file__), pdf_path)
        
        if not os.path.exists(full_path):
            print(f"⚠️  Skipping (not found): {full_path}")
            continue
        
        print(f"\n{'='*70}")
        print(f"Processing: {pdf_path}")
        print(f"{'='*70}")
        
        try:
            # Stage 1a: Extract
            print("  [1] Extracting PDF to raw Markdown...")
            raw_md = pdf_converter.convert(full_path)
            print(f"      ✓ Extracted {len(raw_md)} characters")
            print(f"      ✓ Found {pdf_converter.image_counter} images")
            
            # Stage 1c: Normalize
            print("  [2] Normalizing Markdown...")
            normalized_md = normalizer.normalize(raw_md)
            print(f"      ✓ Normalized to {len(normalized_md)} characters")
            
            # Verify output quality
            print("  [3] Quality checks...")
            
            # Check for ## headings
            heading_count = normalized_md.count('\n##')
            print(f"      ✓ Contains {heading_count} ## headings")
            
            # Check for ### headings
            subheading_count = normalized_md.count('\n###')
            print(f"      ✓ Contains {subheading_count} ### sub-headings")
            
            # Check for IMAGE_PLACEHOLDERs (should be preserved)
            image_placeholders = normalized_md.count('<!-- IMAGE_PLACEHOLDER:')
            print(f"      ✓ Preserved {image_placeholders} image placeholders")
            
            # Check for excessive blank lines
            excessive_blanks = len([m.group() for m in __import__('re').finditer(r'\n\n\n+', normalized_md)])
            if excessive_blanks == 0:
                print(f"      ✓ No excessive blank lines")
            else:
                print(f"      ⚠️  Found {excessive_blanks} excessive blank line groups")
            
            # Save sample output
            output_dir = os.path.join(os.path.dirname(__file__), 'test_outputs')
            os.makedirs(output_dir, exist_ok=True)
            
            basename = Path(pdf_path).stem
            output_file = os.path.join(output_dir, f'{basename}_normalized.md')
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(normalized_md)
            
            print(f"      ✓ Saved to: {output_file}")
            
            # Show first 500 chars
            print(f"\n  First 500 characters:")
            print(f"  {'-'*68}")
            preview = normalized_md[:500].replace('\n', '\n  ')
            print(f"  {preview}...")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*70}")
    print("Phase 1 verification complete!")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
