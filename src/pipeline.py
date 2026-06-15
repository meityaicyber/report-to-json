"""
CLI orchestrator for the document standardization pipeline.
Handles single-file and batch processing.

First-Pass Flow (Vision Path):
    PDF Input
      ├── [Route 1] Extract tables & images, place placeholders
      │   ├── Tables → geometric detection + VLM parsing → JSON
      │   └── Images → saved to deep storage
      │
      └── [Route 2] Cleaned page images (with placeholders) → VLM → JSON
      
    Merge: Table JSON substituted at [TABLE_PLACEHOLDER_N] positions
           Image placeholders remain as [IMAGE_PAGE_X_FIG_Y]
    
    → Final JSON: All information preserved with proper hierarchy
"""

import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime
import click
from dotenv import load_dotenv

# Fix for Windows console unicode output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from docx_to_markdown import DOCXToMarkdownConverter
from pdf_to_markdown import PDFToMarkdownConverter
from markdown_normalizer import MarkdownNormalizer
from llm_extractor import LLMExtractor
from schema_validator import SchemaValidator

try:
    from vl_extractor import VLExtractor
except ImportError:
    VLExtractor = None

try:
    from hybrid_extractor import HybridExtractor
except ImportError:
    HybridExtractor = None

try:
    from image_describer import ImageDescriber
except ImportError:
    ImageDescriber = None


class DocumentPipeline:
    """Main pipeline orchestrator."""

    VERSION = "3.0.0"

    def __init__(self, model: str = "qwen2.5:7b", backend: str = "ollama",
                 vlm_model_id: str = "Qwen/Qwen2.5-VL-7B-Instruct",
                 ollama_host: str = "localhost", ollama_port: int = 11434,
                 llm_workers: int = 2, verbose: bool = False, skip_images: bool = False,
                 use_vision: bool = True, image_storage_dir: str = None):
        """Initialize pipeline with configuration."""
        self.model = model
        self.backend = backend
        self.vlm_model_id = vlm_model_id
        self.ollama_host = ollama_host
        self.ollama_port = ollama_port
        self.llm_workers = llm_workers
        self.verbose = verbose
        self.skip_images = skip_images
        self.image_storage_dir = image_storage_dir

        self.docx_converter = DOCXToMarkdownConverter()
        self.pdf_converter = PDFToMarkdownConverter()
        self.normalizer = MarkdownNormalizer()
        self.llm_extractor = LLMExtractor(
            model=model,
            backend=backend,
            host=ollama_host,
            port=ollama_port
        )
        self.validator = SchemaValidator()
        self.use_vision = use_vision

        # VLM components are lazy-loaded to share a single model instance
        self._vlm_model = None
        self._vlm_processor = None

    def _get_shared_vlm_model(self):
        """
        Load the shared VLM model instance (used by VLExtractor, HybridExtractor,
        and ImageDescriber to avoid loading the same model 3x).
        """
        if self._vlm_model is None:
            import torch
            from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig

            print(f"\n[Pipeline] Loading shared VLM: {self.vlm_model_id} (8-bit)...")
            quant_config = BitsAndBytesConfig(load_in_8bit=True)
            self._vlm_model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                self.vlm_model_id,
                torch_dtype=torch.float16,
                device_map="auto",
                quantization_config=quant_config
            )
            self._vlm_processor = AutoProcessor.from_pretrained(self.vlm_model_id)
            print(f"[Pipeline] VLM loaded successfully.\n")

        return self._vlm_model, self._vlm_processor

    def _substitute_table_placeholders(self, markdown_doc: str, table_json_map: dict) -> str:
        """Replace table placeholders in the markdown string with serialized JSON table data."""
        if not isinstance(markdown_doc, str):
            return markdown_doc
        for placeholder, table_data in table_json_map.items():
            markdown_doc = markdown_doc.replace(placeholder, f"\n```json\n{json.dumps(table_data, indent=2)}\n```\n")
        return markdown_doc

    def _structure_markdown_to_json(self, markdown_text: str) -> dict:
        """
        Pass the complete markdown document to the shared Qwen2.5-VL model
        acting as a pure text LLM to extract the final structured JSON.
        """
        schema_path = Path("schemas/base.schema.json")
        schema_text = schema_path.read_text() if schema_path.exists() else ""

        prompt = f"""You are a strict data structuring assistant. I will provide you with a full Markdown document that may contain JSON blocks representing tables.
Your task is to extract ALL of the information from this document into a single, cohesive JSON object according to the provided schema.

TARGET SCHEMA:
{schema_text}

DOCUMENT TEXT:
{markdown_text}

INSTRUCTIONS:
1. Extract ALL information from the document without summarization. Do NOT drop any paragraphs or omit details.
2. You MUST use the EXACT keys specified in the TARGET SCHEMA. Do not invent your own keys. For example, use "vulnerability_title", "description", "impact", "recommendation" instead of "Vulnerability" or "Severity".
3. For the detailed_observations array, you MUST populate every single required field (vulnerability_title, description, impact, recommendation).
4. If there is tabular data represented as JSON blocks, preserve it as an array of JSON objects in the final output.
5. Preserve all placeholders like [IMAGE_PAGE_X_FIG_Y] exactly.
6. Output ONLY a valid JSON object starting with {{ and ending with }}. Do NOT wrap it in markdown fences. Do NOT explain your output.

EXAMPLE OUTPUT STRUCTURE:
{{
  "document_control": {{ "Document_Title": "..." }},
  "executive_summary": {{ "Key Audit Findings": [...] }},
  "detailed_observations": [
    {{
      "id": "1",
      "vulnerability_title": "...",
      "affected_assets": "...",
      "description": "...",
      "impact": "...",
      "recommendation": "...",
      "risk_rating": "...",
      "cve_cwe": "...",
      "status": "..."
    }}
  ]
}}
"""
        messages = [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}]
            }
        ]

        text = self._vlm_processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        inputs = self._vlm_processor(
            text=[text],
            padding=True,
            return_tensors="pt",
        ).to(self._vlm_model.device)

        import torch
        with torch.no_grad():
            generated_ids = self._vlm_model.generate(
                **inputs,
                max_new_tokens=8192,
                do_sample=False,
                repetition_penalty=1.05
            )

        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]

        output_text = self._vlm_processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]

        import re
        output_text = re.sub(r'^```(?:json)?\n?', '', output_text, flags=re.MULTILINE)
        output_text = re.sub(r'\n?```$', '', output_text, flags=re.MULTILINE)

        try:
            return json.loads(output_text.strip())
        except Exception as e:
            first_brace = output_text.find('{')
            last_brace = output_text.rfind('}')
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                try:
                    return json.loads(output_text[first_brace:last_brace + 1])
                except Exception:
                    pass
            print(f"  [Pipeline] WARNING Failed to parse final JSON: {e}")
            return {"_extraction_status": "failed", "raw_text_fallback": output_text}

    def process_file(self, input_file: str, output_file: str = None,
                     keep_markdown: bool = False, dry_run: bool = False,
                     doc_type_hint: str = None) -> dict:
        """
        Process a single document file.
        
        Args:
            input_file: Input DOCX or PDF file path
            output_file: Output JSON file path (auto-generated if None)
            keep_markdown: Save intermediate normalized Markdown
            dry_run: Run Stage 1 only, output Markdown
            doc_type_hint: Optional document type hint for LLM
            
        Returns:
            Extraction result dict with status and metadata
        """
        input_path = Path(input_file)

        if not input_path.exists():
            return {'status': 'error', 'error': f'File not found: {input_file}'}

        if not output_file:
            output_file = input_path.with_suffix('.json').name

        output_path = Path(output_file)

        print(f"\n{'=' * 70}")
        print(f"Processing: {input_path.name}")
        print(f"{'=' * 70}")

        start_time = datetime.now()

        try:
            file_type = input_path.suffix.lower()
            image_count = 0
            normalized_md = ""
            inferred_schema = {}

            # ============================================================
            # VISION PATH — First-Pass Parallel Route Architecture
            # ============================================================
            if self.use_vision and file_type == '.pdf':
                if VLExtractor is None or HybridExtractor is None:
                    raise ImportError(
                        "VLExtractor or HybridExtractor could not be loaded. "
                        "Please ensure required packages are installed."
                    )

                checkpoint_path = str(output_path).replace('.json', '_partial.json')

                # --- Load shared model ---
                vlm_model, vlm_processor = self._get_shared_vlm_model()

                # ========================================
                # ROUTE 1: Table & Image Pre-Extraction
                # ========================================
                print(f"\n[Route 1] Extracting tables and images from PDF...")

                # 1a. Detect table groups (geometric detection, no VLM yet)
                hybrid = HybridExtractor(
                    model_id=self.vlm_model_id,
                    model=vlm_model,
                    processor=vlm_processor
                )
                table_groups = hybrid.extract_table_groups_only(str(input_path))
                print(f"    ✓ Found {len(table_groups)} logical table groups")

                # 1b. Extract and save images to deep storage
                image_regions = None
                if not self.skip_images and ImageDescriber is not None:
                    img_describer = ImageDescriber(
                        model_id=self.vlm_model_id,
                        model=vlm_model,
                        processor=vlm_processor
                    )
                    image_regions = img_describer.extract_image_regions(str(input_path))

                    # Determine image storage directory
                    if self.image_storage_dir:
                        img_dir = self.image_storage_dir
                    else:
                        img_dir = str(output_path.parent / (output_path.stem + "_images"))

                    saved_images = img_describer.save_images_to_disk(str(input_path), img_dir)
                    image_count = sum(len(v) for v in saved_images.values())
                    print(f"    ✓ Saved {image_count} images to {img_dir}")
                else:
                    print(f"    ℹ️  Image extraction skipped")

                # 1c. Render cleaned pages (tables & images → placeholders)
                print(f"\n[Route 1] Rendering cleaned pages with placeholders...")
                cleaned_pages = hybrid.render_cleaned_pages(
                    str(input_path),
                    table_groups,
                    image_regions=image_regions
                )

                # 1d. Parse each table group through VLM → JSON
                print(f"\n[Route 1] Parsing {len(table_groups)} table groups through VLM...")
                parsed_tables = []
                for idx, group in enumerate(table_groups):
                    print(f"    Parsing table {idx + 1}/{len(table_groups)}: {group['id']}...")
                    parsed = hybrid.parse_table_group(group)
                    parsed_tables.append(parsed)
                    if self.verbose:
                        print(f"      Result keys: {list(parsed.get('data', {}).keys()) if isinstance(parsed.get('data'), dict) else type(parsed.get('data'))}")
                print(f"    ✓ All tables parsed")

                # Build table placeholder -> JSON map
                table_json_map = {}
                for idx, parsed in enumerate(parsed_tables):
                    placeholder = f"[TABLE_PLACEHOLDER_{idx + 1}]"
                    table_json_map[placeholder] = parsed["data"]

                # ========================================
                # ROUTE 2: VLM Page Extraction
                # ========================================
                print(f"\n[Route 2] Extracting document structure via VLM...")
                vl_extractor = VLExtractor(
                    model_id=self.vlm_model_id,
                    model=vlm_model,
                    processor=vlm_processor
                )
                markdown_doc = vl_extractor.extract_from_cleaned_pages(
                    cleaned_pages,
                    checkpoint_path=checkpoint_path
                )

                if not markdown_doc:
                    raise RuntimeError("VLM markdown extraction failed or returned empty.")
                print(f"    ✓ VLM extraction complete")

                # ========================================
                # MERGE: Substitute table placeholders
                # ========================================
                print(f"\n[Merge] Substituting {len(table_json_map)} table placeholders into markdown...")
                markdown_doc = self._substitute_table_placeholders(
                    markdown_doc, table_json_map
                )
                print(f"    ✓ Table data merged into markdown document")

                # Save intermediate markdown to disk
                md_out_path = str(output_path).replace('.json', '_intermediate.md')
                with open(md_out_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_doc)
                print(f"    ✓ Saved intermediate markdown to {md_out_path}")

                # ========================================
                # STAGE 3: Text LLM Structuring
                # ========================================
                print(f"\n[Stage 3] Structuring Markdown to JSON via LLM...")
                extracted_data = self._structure_markdown_to_json(markdown_doc)
                if extracted_data.get('_extraction_status') == 'failed':
                    print("    ⚠️  Warning: Final LLM structuring failed, outputting raw fallback")
                else:
                    print(f"    ✓ LLM Structuring complete")

                # Add metadata
                if '_meta' not in extracted_data:
                    extracted_data['_meta'] = {}
                extracted_data['_meta'].update({
                    'pipeline_version': self.VERSION,
                    'source_file': input_path.name,
                    'extraction_timestamp': datetime.now().isoformat(),
                    'llm_model': self.vlm_model_id,
                    'extraction_mode': 'vision_to_markdown_to_json',
                    'tables_extracted': len(parsed_tables),
                    'images_extracted': image_count,
                })

                # For validation compatibility
                raw_md = ""
                normalized_md = ""
                inferred_schema = {}

            # ============================================================
            # TEXT PATH — Legacy Ollama-based extraction
            # ============================================================
            else:
                print(f"[Stage 1a] Extracting to Markdown...")

                if file_type == '.docx':
                    raw_md = self.docx_converter.convert(str(input_path))
                    image_count = self.docx_converter.image_counter
                elif file_type == '.pdf':
                    raw_md = self.pdf_converter.convert(str(input_path))
                    image_count = self.pdf_converter.image_counter
                else:
                    return {'status': 'error', 'error': f'Unsupported file type: {file_type}'}

                print(f"    ✓ Extracted {len(raw_md)} characters, {image_count} images")

                # Stage 1c: Normalize
                print(f"[Stage 1c] Normalizing Markdown...")
                normalized_md = self.normalizer.normalize(raw_md)
                print(f"    ✓ Normalized to {len(normalized_md)} characters")

                # Save intermediate markdown if requested
                if keep_markdown:
                    md_file = output_path.with_suffix('.md')
                    with open(md_file, 'w', encoding='utf-8') as f:
                        f.write(normalized_md)
                    print(f"    ✓ Saved intermediate: {md_file}")

                # Early exit for dry-run
                if dry_run:
                    print(f"\n✓ Dry-run complete (Stage 1 only)")
                    print(f"  Output: {output_path}")
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(normalized_md)
                    return {
                        'status': 'success',
                        'stage': 'dry-run',
                        'elapsed_seconds': (datetime.now() - start_time).total_seconds()
                    }

                # Stage 2 Pass 1: Schema inference
                print(f"\n[Stage 2 Pass 1] Inferring schema...")

                # Check if this is an audit report
                is_audit = self.llm_extractor.is_audit_report(normalized_md)
                if is_audit:
                    print(f"    ℹ️  Detected audit report - using audit-specific extraction")

                    # Direct audit extraction (bypass schema inference)
                    print(f"\n[Stage 2 Pass 2] Extracting audit data...")

                    inferred_schema = {
                        'sections': {
                            'metadata': {'type': 'object'},
                            'scope': {'type': 'object'},
                            'executive_summary': {'type': 'object'},
                            'vulnerabilities': {'type': 'array'},
                            'audit_team': {'type': 'array'},
                            'tools_used': {'type': 'array'},
                            'risk_rating_criteria': {'type': 'object'},
                            'methodology': {'type': 'string'}
                        }
                    }

                    extracted_data = self.llm_extractor.extract_audit_report(normalized_md)

                    if (extracted_data.get('_extraction_status') == 'failed' or
                            len(extracted_data.get('vulnerabilities', [])) == 0):
                        print(f"    ⚠️  Full-document extraction yielded no vulnerabilities, trying chunked extraction...")

                        findings = self.llm_extractor._extract_findings_section(normalized_md)
                        if findings and len(findings) > 100:
                            print(f"    ℹ️  Extracted findings section ({len(findings)} chars), re-extracting...")
                            extracted_data_retry = self.llm_extractor.extract_audit_report(findings)

                            if len(extracted_data_retry.get('vulnerabilities', [])) > len(
                                    extracted_data.get('vulnerabilities', [])):
                                for key in ['vulnerabilities']:
                                    if key in extracted_data_retry and extracted_data_retry[key]:
                                        extracted_data[key] = extracted_data_retry[key]
                else:
                    inferred_schema = self.llm_extractor.infer_schema(normalized_md, doc_type_hint)

                    if '_error' in inferred_schema:
                        print(f"    ⚠️  Schema inference error: {inferred_schema['_error']}")
                    else:
                        print(f"    ✓ Schema inferred")

                    # Stage 2 Pass 2: Extraction
                    print(f"\n[Stage 2 Pass 2] Extracting data...")

                    chunks = self.llm_extractor.chunk_if_needed(normalized_md)

                    if len(chunks) == 1:
                        extracted_data = self.llm_extractor.extract(
                            chunks[0],
                            inferred_schema,
                            section_hint=None
                        )
                    else:
                        print(f"    ℹ️  Chunked into {len(chunks)} sections for concurrent extraction")
                        section_pairs = [
                            (chunk, f"Section {i + 1}/{len(chunks)}")
                            for i, chunk in enumerate(chunks)
                        ]
                        section_results = self.llm_extractor.extract_concurrent(
                            section_pairs,
                            inferred_schema,
                            workers=self.llm_workers
                        )

                        extracted_data = {'sections': {}}
                        for i, result in enumerate(section_results):
                            if isinstance(result, dict):
                                extracted_data['sections'].update(result.get('sections', {}))
                                for key, val in result.items():
                                    if key != 'sections' and key not in extracted_data:
                                        extracted_data[key] = val

            print(f"    ✓ Extraction complete")

            # Stage 3: Prepare output
            print(f"\n[Stage 3] Preparing output...")

            output_data = self._prepare_output(
                extracted_data,
                inferred_schema,
                normalized_md,
                image_count,
                input_path.name,
                doc_type_hint
            )

            # Validate
            print(f"[Stage 4] Validating output...")
            validation_warnings = self.validator.validate(
                output_data,
                inferred_schema
            )

            if validation_warnings:
                print(f"    ⚠️  {len(validation_warnings)} validation warnings:")
                for warning in validation_warnings[:5]:
                    print(f"      - {warning}")
                if len(validation_warnings) > 5:
                    print(f"      ... and {len(validation_warnings) - 5} more")
            else:
                print(f"    ✓ Validation passed")

            # Save output
            print(f"\n[Output] Saving results...")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2)
            print(f"    ✓ Saved JSON: {output_path}")

            schema_path = output_path.with_suffix('.schema.json')
            with open(schema_path, 'w', encoding='utf-8') as f:
                json.dump(inferred_schema, f, indent=2)
            print(f"    ✓ Saved schema: {schema_path}")

            # Clean up checkpoint if it exists
            checkpoint_path_str = str(output_path).replace('.json', '_partial.json')
            if os.path.exists(checkpoint_path_str):
                os.remove(checkpoint_path_str)

            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"\n✓ Processing complete in {elapsed:.1f}s")
            print(f"{'=' * 70}\n")

            return {
                'status': 'success',
                'input': str(input_path),
                'output': str(output_path),
                'elapsed_seconds': elapsed,
                'sections_count': len(output_data.get('sections', {})),
                'validation_warnings': len(validation_warnings)
            }

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'error': str(e),
                'elapsed_seconds': (datetime.now() - start_time).total_seconds()
            }

    def _prepare_output(self, extracted_data: dict, inferred_schema: dict,
                        normalized_md: str, image_count: int,
                        source_file: str, doc_type_hint: str = None) -> dict:
        """Prepare final output with metadata."""
        image_placeholders = normalized_md.count('<!-- IMAGE_PLACEHOLDER:') if normalized_md else 0

        output = {
            '_meta': extracted_data.get('_meta', {
                'pipeline_version': self.VERSION,
                'source_file': source_file,
                'document_type': doc_type_hint,
                'extraction_timestamp': datetime.now().isoformat(),
                'image_placeholder_count': image_placeholders,
                'llm_model': self.model,
                'inferred_schema_version': '1.0'
            }),
            'sections': extracted_data.get('sections', {})
        }

        for key, value in extracted_data.items():
            if key != 'sections' and key != '_meta':
                output[key] = value

        return output

    def batch_process(self, input_dir: str, output_dir: str, **kwargs) -> list:
        """
        Batch process all documents in a directory.
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)

        if not input_path.exists():
            print(f"Error: Input directory not found: {input_dir}")
            return []

        output_path.mkdir(parents=True, exist_ok=True)

        files = list(input_path.glob('*.docx')) + list(input_path.glob('*.pdf'))

        if not files:
            print(f"No DOCX or PDF files found in {input_dir}")
            return []

        print(f"\nBatch processing {len(files)} files from {input_dir}\n")

        results = []
        for file_path in sorted(files):
            output_file = output_path / file_path.with_suffix('.json').name
            result = self.process_file(str(file_path), str(output_file), **kwargs)
            results.append(result)

        print(f"\n{'=' * 70}")
        print(f"Batch processing summary:")
        print(f"{'=' * 70}")
        successful = sum(1 for r in results if r.get('status') == 'success')
        failed = sum(1 for r in results if r.get('status') == 'error')
        print(f"  ✓ Successful: {successful}")
        print(f"  ❌ Failed: {failed}")
        total_time = sum(r.get('elapsed_seconds', 0) for r in results)
        print(f"  ⏱️  Total time: {total_time:.1f}s")
        print(f"{'=' * 70}\n")

        return results


@click.command()
@click.option('--input', 'input_file', help='Input DOCX or PDF file')
@click.option('--input-dir', help='Input directory with DOCX/PDF files (batch mode)')
@click.option('--output', 'output_file', help='Output JSON file')
@click.option('--output-dir', help='Output directory for batch processing')
@click.option('--model', default='qwen2.5:7b', help='Text LLM model name for Ollama (default: qwen2.5:7b)')
@click.option('--vlm-model', default='Qwen/Qwen2.5-VL-7B-Instruct',
              help='Vision-Language Model ID from HuggingFace (default: Qwen/Qwen2.5-VL-7B-Instruct)')
@click.option('--ollama-host', default='localhost', help='Ollama server host')
@click.option('--ollama-port', type=int, default=11434, help='Ollama server port')
@click.option('--llm-workers', type=int, default=2, help='Concurrent LLM workers (default: 2)')
@click.option('--doc-type', help='Optional document type hint for LLM')
@click.option('--dry-run', is_flag=True, help='Run Stage 1 only (extraction & normalization)')
@click.option('--keep-markdown', is_flag=True, help='Save intermediate normalized Markdown')
@click.option('--skip-images', is_flag=True, help='Skip image extraction and storage')
@click.option('--image-storage-dir', default=None, help='Directory for extracted image deep storage')
@click.option('--use-vision/--no-vision', default=True,
              help='Use Vision-Language Model directly on PDFs (default: True)')
@click.option('--verbose', is_flag=True, help='Verbose logging')
def main(input_file, input_dir, output_file, output_dir, model, vlm_model,
         ollama_host, ollama_port, llm_workers, doc_type, dry_run, keep_markdown,
         skip_images, image_storage_dir, use_vision, verbose):
    """
    Document Standardization Pipeline - Convert DOCX/PDF to structured JSON.
    
    First-Pass: Ensures all information from the report is captured in JSON
    with proper hierarchical structure. Tables and images are extracted in
    parallel and reinserted at their correct positions.
    """

    # Load .env
    load_dotenv()

    # Override with env vars if set
    model = os.getenv('OLLAMA_MODEL', model)
    vlm_model = os.getenv('VLM_MODEL', vlm_model)
    ollama_host = os.getenv('OLLAMA_HOST', ollama_host)
    ollama_port = int(os.getenv('OLLAMA_PORT', ollama_port))
    llm_workers = int(os.getenv('MAX_WORKERS', llm_workers))

    # Initialize pipeline
    pipeline = DocumentPipeline(
        model=model,
        backend='ollama',
        vlm_model_id=vlm_model,
        ollama_host=ollama_host,
        ollama_port=ollama_port,
        llm_workers=llm_workers,
        verbose=verbose,
        skip_images=skip_images,
        use_vision=use_vision,
        image_storage_dir=image_storage_dir
    )

    # Process files
    if input_file and input_dir:
        click.echo("Error: Specify either --input (single file) or --input-dir (batch), not both")
        sys.exit(1)

    if input_file:
        # Single file
        if not output_file:
            output_file = Path(input_file).with_suffix('.json').name

        result = pipeline.process_file(
            input_file,
            output_file,
            keep_markdown=keep_markdown,
            dry_run=dry_run,
            doc_type_hint=doc_type
        )

        if result.get('status') == 'error':
            click.echo(f"Error: {result.get('error')}")
            sys.exit(1)

    elif input_dir:
        # Batch
        if not output_dir:
            output_dir = './output/'

        results = pipeline.batch_process(
            input_dir,
            output_dir,
            keep_markdown=keep_markdown,
            dry_run=dry_run,
            doc_type_hint=doc_type
        )

        failed = sum(1 for r in results if r.get('status') == 'error')
        if failed > 0:
            sys.exit(1)

    else:
        click.echo("Error: Specify either --input (single file) or --input-dir (batch)")
        sys.exit(1)


if __name__ == '__main__':
    main()
