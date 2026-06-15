# Document Standardization Pipeline

End-to-end document processing pipeline for converting DOCX/PDF reports into structured JSON using local LLM (Ollama).

## Quick Start

### 1. Setup

```bash
cd doc-pipeline

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Copy .env configuration
cp .env.example .env
```

### 2. Start Ollama

```bash
# Terminal 1: Start Ollama service
ollama serve

# Terminal 2: Pull model
ollama pull qwen:7b
```

### 3. Test the Pipeline

```bash
# Phase 1: Test extraction & normalization only
python test_phase1.py

# Phase 2: Test LLM integration (requires Ollama running)
python test_phase2.py

# Phase 3: Run full pipeline on a single file
python -m src.pipeline --input ../Network\ Report/1-Audit\ Report.pdf --output output.json

# Batch process all PDFs in a directory
python -m src.pipeline --input-dir ../Network\ Report/ --output-dir ./outputs/
```

## Architecture

```
Stage 1: DOCX/PDF → Markdown (Deterministic)
  ├── Extract text, tables, images, headings
  ├── Mark heading candidates and image positions
  └── Output: Raw, unstructured Markdown

Stage 1c: Normalize Markdown
  ├── Unicode normalization
  ├── Heading level standardization
  ├── Header/footer removal
  └── Output: Clean, consistent Markdown

Stage 2 Pass 1: Infer Schema (LLM-driven)
  ├── LLM reads full document
  ├── Proposes JSON schema structure
  └── Output: Valid JSON Schema with "sections" key

Stage 2 Pass 2: Extract Data (LLM-driven)
  ├── LLM fills schema with extracted values
  ├── Concurrent section extraction for large documents
  └── Output: JSON conforming to schema

Stage 3: Validate & Output
  ├── Check base schema compliance
  ├── Detect hallucinations and anomalies
  └── Output: Final JSON + metadata + schema
```

## Core Modules

| Module | Purpose |
|--------|---------|
| `src/pdf_to_markdown.py` | Extract PDF → raw Markdown |
| `src/docx_to_markdown.py` | Extract DOCX → raw Markdown |
| `src/markdown_normalizer.py` | Normalize Markdown format |
| `src/llm_extractor.py` | Schema inference + LLM extraction |
| `src/schema_validator.py` | Validate output structure |
| `src/pipeline.py` | CLI orchestrator |
| `schemas/base.schema.json` | Base schema (required fields) |
| `prompts/schema_inference.txt` | LLM prompt for Pass 1 |
| `prompts/extraction.txt` | LLM prompt for Pass 2 |

## CLI Usage

### Single File Processing

```bash
python -m src.pipeline --input report.pdf --output report.json
```

Options:
- `--doc-type audit_report` — Optional hint to LLM about document type
- `--dry-run` — Run Stage 1 only (extraction & normalization, no LLM)
- `--keep-markdown` — Save intermediate normalized Markdown
- `--verbose` — Log LLM prompts and responses
- `--model qwen:7b` — Override LLM model (default: from .env)
- `--llm-workers 4` — Number of concurrent extraction workers (default: 4)

### Batch Processing

```bash
python -m src.pipeline --input-dir ./documents/ --output-dir ./json_output/
```

All options from single file apply to batch as well.

### Dry-Run (No LLM Required)

```bash
# Extract and normalize without LLM inference/extraction
python -m src.pipeline --input report.pdf --output report.md --dry-run
```

## Output Format

### JSON Output (`report.json`)

```json
{
  "_meta": {
    "pipeline_version": "1.0.0",
    "source_file": "report.pdf",
    "document_type": "audit_report",
    "extraction_timestamp": "2024-01-15T14:30:00",
    "image_placeholder_count": 5,
    "llm_model": "qwen:7b",
    "inferred_schema_version": "1.0"
  },
  "sections": {
    "executive_summary": { /* extracted content */ },
    "findings": [ /* list of findings */ ],
    "recommendations": { /* extracted content */ }
  }
}
```

### Schema Output (`report.schema.json`)

Saved alongside JSON for reproducibility. Contains the inferred JSON Schema used for extraction.

### Markdown Output (`report.md`) — When `--keep-markdown`

Intermediate normalized Markdown for inspection and debugging.

## Configuration

Edit `.env` to configure:

```bash
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_MODEL=qwen:7b
MAX_WORKERS=4
```

## Testing

### Phase 1: Extraction & Normalization (No LLM required)

```bash
python test_phase1.py
```

Outputs samples to `test_outputs/1-Audit Report_normalized.md` and `test_outputs/1-report_normalized.md`.

### Phase 2: LLM Integration (Requires Ollama)

```bash
python test_phase2.py
```

Tests schema inference and data extraction. Requires Ollama running with qwen:7b model.

## Performance

- **Typical extraction time:** 2-5 minutes per document section
- **Chunking:** Documents > 6000 tokens split by `##` sections
- **Concurrency:** Up to 4 workers extracting sections simultaneously

## Troubleshooting

### Ollama Connection Error

```
❌ Cannot connect to Ollama: [Errno 61] Connection refused
```

**Solution:**
```bash
# Make sure Ollama is running in another terminal
ollama serve

# Or check if it's listening
curl http://localhost:11434/api/tags
```

### Model Not Found

```
⚠️  qwen:7b not in model list
```

**Solution:**
```bash
ollama pull qwen:7b
```

### LLM Timeout

```
❌ Ollama API timeout (>60s)
```

**Solutions:**
- Check Ollama is not overloaded
- Increase `timeout` in config
- Try smaller document chunks
- Reduce `--llm-workers` value

### Hallucination Warnings

LLM sometimes generates content not in the source document. These are detected during validation:

```
HALLUCINATION_SUSPECT: Found pattern '[insert' (2 times)
```

Check extracted data and review LLM response with `--verbose` flag.

## Features

✅ **Stage 1: Extraction & Normalization**
- PDF extraction (pdfplumber + pymupdf fallback)
- DOCX extraction (python-docx)
- Table detection and GFM formatting
- Image position tracking
- Unicode normalization
- Heading level standardization

✅ **Stage 2: LLM Integration** 
- Schema inference from full document
- Concurrent data extraction
- Token budget estimation and chunking
- Retry logic on LLM failure
- Fallback handling

✅ **Stage 3: Validation & Output**
- Base schema validation
- Hallucination detection
- Image placeholder count verification
- JSON output with metadata
- Schema reproducibility

## Next Steps

1. **Run test_phase1.py** → Verify extraction works
2. **Set up Ollama** → `ollama serve` + `ollama pull qwen:7b`
3. **Run test_phase2.py** → Verify LLM integration
4. **Process documents** → `python -m src.pipeline --input-dir ./docs/ --output-dir ./json/`
5. **Review outputs** → Check `json/` directory and validation warnings

## References

- Full specification: See `AGENT_INSTRUCTIONS.md`
- LLM Prompts: `prompts/` directory
- Base schema: `schemas/base.schema.json`
