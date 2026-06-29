#!/bin/bash
set -e

source venv/bin/activate

echo "==========================================="
echo "PHASE 0: Preprocessing DOCX to PDF"
echo "==========================================="
python3 preprocess_docx.py

echo "==========================================="
echo "PHASE 1: VLM Extraction (Dry Run)"
echo "==========================================="
for dir in "iot" "Network Report" "Mobile application" "VAPT-API" "best"; do
    echo "Processing $dir..."
    python3 src/pipeline.py --input-dir "$dir" --output-dir "output/$dir" --dry-run
done

echo "==========================================="
echo "PHASE 2: LLM Structuring"
echo "==========================================="
python3 run_stage3_batch.py

echo "Batch processing complete."
