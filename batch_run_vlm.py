"""
batch_run_vlm.py
================
Runs the Unified Qwen 3 VL pipeline across all reports in VAPT-API/
via Ollama (qwen3-vl:8b) keeping fast GGUF inference in GPU memory.
"""

import sys
import os
from pathlib import Path

# Fix for Windows console unicode output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent / "vlm_repo" / "src"))

from pipeline import DocumentPipeline

def main():
    input_dir = Path("VAPT-API")
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    print("===========================================================================", flush=True)
    print("      BATCH PROCESSING AUDIT REPORTS VIA QWEN 3 VL (OLLAMA)", flush=True)
    print(f"  Input: {input_dir.resolve()}", flush=True)
    print(f"  Output: {output_dir.resolve()}", flush=True)
    print(f"  Model: qwen3-vl:8b (Ollama Endpoint: http://localhost:11434)", flush=True)
    print("===========================================================================\n", flush=True)

    pipeline = DocumentPipeline(
        backend="ollama",
        model="qwen3-vl:8b"
    )

    pdf_files = sorted(list(input_dir.glob("*.pdf")))
    print(f"Found {len(pdf_files)} PDF reports to process:", flush=True)
    for f in pdf_files:
        print(f"  - {f.name}", flush=True)
    print(flush=True)

    for idx, pdf_path in enumerate(pdf_files, 1):
        out_json = output_dir / f"{pdf_path.stem}.json"
        print(f"\n[{idx}/{len(pdf_files)}] Processing {pdf_path.name} -> {out_json.name}...", flush=True)
        try:
            res = pipeline.process_file(
                input_file=str(pdf_path),
                output_file=str(out_json),
                stage="all",
                keep_markdown=True
            )
            print(f"  ✓ Finished {pdf_path.name}: {res.get('status')}", flush=True)
        except Exception as e:
            print(f"  ✗ Failed {pdf_path.name}: {e}", flush=True)

    print("\n===========================================================================", flush=True)
    print("✓ BATCH QWEN 3 VL RUN COMPLETE!", flush=True)
    print("===========================================================================", flush=True)

if __name__ == "__main__":
    main()
