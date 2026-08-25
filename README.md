# Document Standardization Pipeline

End-to-end document processing pipeline for converting DOCX/PDF reports into structured JSON using a Vision-Language Model (**Qwen 3.6 VL** / `Qwen/Qwen3.6-VL`).

## Quick Start

### 1. Setup

```bash
cd doc-pipeline

# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy .env configuration
cp .env.example .env
```

### 2. GPU Requirements

- **Minimum:** NVIDIA GPU with 8GB VRAM (RTX 4060 Laptop, RTX 3060, etc.)
- **Model:** `Qwen/Qwen3.6-VL` loaded in 4-bit NF4 precision (~4.8GB VRAM) or 8-bit precision (~9-10GB VRAM)
- **CUDA:** 12.0+ recommended

### 3. Test the Pipeline

```bash
# Phase 1: Test extraction & normalization only (no GPU needed)
python test_phase1.py

# Run full pipeline on a single file (requires GPU)
python -m src.pipeline --input ../Network\ Report/1-Audit\ Report.pdf --output output.json

# Batch process all PDFs in a directory
python -m src.pipeline --input-dir ../Network\ Report/ --output-dir ./outputs/

# Dry-run (extraction only, no VLM)
python -m src.pipeline --input report.pdf --output report.md --dry-run
```

## Architecture — First-Pass Flow

The pipeline uses a **Vision-First** approach with parallel routes to ensure all information from the source document is preserved in the output JSON.

```
PDF Input
  │
  ├─[Route 1: Table & Image Pre-Extraction]─────────────────────────┐
  │  1a. Detect table bounding boxes (pdfplumber geometric detection) │
  │  1b. Stitch multi-page tables into single images                  │
  │  1c. Extract embedded images → save to deep storage               │
  │  1d. Render "cleaned" page images:                                │
  │      - Table regions → whited out, overlaid with                  │
  │        [TABLE_PLACEHOLDER_1], [TABLE_PLACEHOLDER_2], etc.         │
  │      - Image regions → whited out, overlaid with                  │
  │        [IMAGE_PAGE_X_FIG_Y] placeholders                         │
  │  1e. Parse each stitched table image through VLM → JSON           │
  │                                                                   │
  ├─[Route 2: VLM Page Extraction]──────────────────────────────────┤
  │  2a. Feed cleaned page images (with visible placeholders) to VLM  │
  │  2b. VLM outputs hierarchical JSON preserving document structure  │
  │  2c. Placeholder strings preserved verbatim in output             │
  │                                                                   │
  └─[Merge]─────────────────────────────────────────────────────────┘
     3a. Walk VLM JSON, find [TABLE_PLACEHOLDER_N] entries
     3b. Replace each with parsed table JSON from Route 1
     3c. Image placeholders remain as [IMAGE_PAGE_X_FIG_Y]
     
  → Final JSON: All information preserved with proper hierarchy
```

### Why This Design?

- **Tables that span multiple pages** are misread by VLMs when processed page-by-page. By extracting and stitching them first, we get accurate table data.
- **Images are computationally expensive** for VLMs. By extracting them separately and leaving placeholders, the VLM focuses on text and structure.
- **Parallel processing** means table parsing and page extraction can be optimized independently.

## Core Modules

| Module | Purpose |
|--------|---------|
| `src/pipeline.py` | CLI orchestrator — implements the first-pass flow |
| `src/hybrid_extractor.py` | Table detection, multi-page stitching, VLM table parsing |
| `src/vl_extractor.py` | VLM-based page extraction (Route 2) |
| `src/image_describer.py` | Image extraction, deep storage, optional description |
| `src/pdf_to_markdown.py` | PDF → raw Markdown (text path fallback) |
| `src/docx_to_markdown.py` | DOCX → raw Markdown (text path fallback) |
| `src/markdown_normalizer.py` | Normalize Markdown format |
| `src/llm_extractor.py` | Ollama-based schema inference + text extraction |
| `src/schema_validator.py` | Validate output structure |
| `schemas/base.schema.json` | Base schema (required fields) |
| `prompts/` | LLM prompt templates |

## CLI Usage

### Single File Processing

```bash
python -m src.pipeline --input report.pdf --output report.json
```

Options:
- `--vlm-model Qwen/Qwen2.5-VL-7B-Instruct` — VLM model for vision path (default)
- `--model qwen2.5:7b` — Text LLM model for Ollama (fallback path)
- `--doc-type audit_report` — Optional hint about document type
- `--dry-run` — Run extraction only (no VLM)
- `--keep-markdown` — Save intermediate normalized Markdown
- `--skip-images` — Skip image extraction and storage
- `--image-storage-dir ./images/` — Custom directory for extracted images
- `--use-vision / --no-vision` — Enable/disable vision path (default: enabled)
- `--verbose` — Log VLM prompts and responses
- `--llm-workers 4` — Number of concurrent extraction workers

### Batch Processing

```bash
python -m src.pipeline --input-dir ./documents/ --output-dir ./json_output/
```

All options from single file apply to batch as well.

## Output Format

### JSON Output (`report.json`)

```json
{
  "_meta": {
    "pipeline_version": "3.0.0",
    "source_file": "report.pdf",
    "extraction_timestamp": "2026-06-15T14:30:00",
    "llm_model": "Qwen/Qwen2.5-VL-7B-Instruct",
    "extraction_mode": "vision_first_pass",
    "tables_extracted": 5,
    "images_extracted": 3
  },
  "sections": {
    "executive_summary": { "...": "extracted content" },
    "findings": [
      {
        "title": "...",
        "severity": "High",
        "details": [ "...parsed table data replaces placeholder..." ]
      }
    ],
    "recommendations": { "...": "extracted content" }
  }
}
```

### Extracted Images (`report_images/`)

Images are saved to a subdirectory next to the output JSON (or a custom path via `--image-storage-dir`):
```
report_images/
  page_0_fig_1.png
  page_3_fig_2.png
  ...
```

## Configuration

Edit `.env` to configure:

```bash
# Text LLM (Ollama - used for fallback text path)
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_MODEL=qwen2.5:7b

# Vision-Language Model (loaded locally via HuggingFace)
VLM_MODEL=Qwen/Qwen2.5-VL-7B-Instruct

# Pipeline
MAX_WORKERS=4
```

## Performance

- **GPU Memory:** ~9-10GB VRAM (Qwen2.5-VL-7B at 8-bit quantization)
- **Shared Model:** VLExtractor, HybridExtractor, and ImageDescriber share a single loaded model instance
- **Typical extraction time:** 3-8 minutes per document (depends on page count and table complexity)
- **Multi-page tables:** Automatically detected and stitched before VLM parsing

## Troubleshooting

### CUDA Out of Memory

```
RuntimeError: CUDA out of memory
```

**Solutions:**
- Ensure no other processes are using GPU: `nvidia-smi`
- The pipeline requires ~10GB free VRAM
- Close other GPU-intensive applications

### Model Download Issues

The VLM model (~14GB) is downloaded automatically from HuggingFace on first run.

```bash
# Pre-download the model
python -c "from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor; Qwen2_5_VLForConditionalGeneration.from_pretrained('Qwen/Qwen2.5-VL-7B-Instruct'); AutoProcessor.from_pretrained('Qwen/Qwen2.5-VL-7B-Instruct')"
```

### Ollama Connection Error (Text Path Only)

```
❌ Cannot connect to Ollama: [Errno 61] Connection refused
```

**Solution:**
```bash
ollama serve
curl http://localhost:11434/api/tags
```

## Features

✅ **First-Pass Vision Flow**
- Parallel table & image extraction with placeholder substitution
- Multi-page table stitching and VLM-based parsing
- Cleaned page rendering with placeholder overlays
- Hierarchical JSON extraction preserving document structure
- Table JSON merge at placeholder positions

✅ **Table Handling**
- Geometric detection via pdfplumber
- Multi-page continuation detection (matching column counts)
- Stitched image rendering for VLM parsing
- Structured JSON output per table

✅ **Image Handling**
- Embedded image extraction (skips logos/icons < 50x50px)
- Deep storage to disk
- Placeholder preservation in output JSON

✅ **Validation & Quality**
- Base schema validation
- Hallucination detection
- Image placeholder count verification
- Checkpoint/resume on VLM failure

## References

- VLM: [Qwen2.5-VL-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct)
- LLM Prompts: `prompts/` directory
- Base schema: `schemas/base.schema.json`
