"""
pipeline.py
===========
CLI orchestrator for the Document Standardization Pipeline using Qwen 3.6 VL.
Handles single-file and batch processing across decoupled stages:
  - Stage 1: Image & Diagram Deep Storage Offloader
  - Stage 2: Qwen 3.6 VL Multimodal Visual Transcriber (Intermediate Markdown)
  - Stage 3: Qwen 3.6 VL Master Schema Structurer (Canonical Master Schema JSON)
"""

import json
import os
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

# Add src and repo root to sys.path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from image_offloader import ImageOffloader
from lossless_transcriber import LosslessTranscriber
from schema_structurer import SchemaStructurer

try:
    from unified_vlm_engine import UnifiedVLMEngine
except ImportError:
    UnifiedVLMEngine = None

try:
    from vl_extractor import VLExtractor
except ImportError:
    VLExtractor = None

try:
    from pipeline_integration import malware_gate, MalwareDetectedError
except ImportError:
    malware_gate = None
    MalwareDetectedError = Exception

DEFAULT_PIPELINE_MODEL = os.environ.get("VLM_MODEL", "Qwen/Qwen3.6-VL")


class DocumentPipeline:
    """Document Standardization Pipeline Orchestrator powered by Qwen 3.6 VL."""

    VERSION = "3.1.0-qwen3.6-vl"

    def __init__(
        self,
        backend: str = "vlm_unified",
        model: str = DEFAULT_PIPELINE_MODEL,
        ollama_host: str = "localhost",
        ollama_port: int = 11434,
        schema_path: str = None,
        load_in_4bit: bool = True,
        load_in_8bit: bool = False,
        enable_security_gate: bool = True,
        verbose: bool = False
    ):
        self.backend = backend
        self.model = model
        self.ollama_host = ollama_host
        self.ollama_port = ollama_port
        self.enable_security_gate = enable_security_gate
        self.verbose = verbose
        self.schema_path = schema_path
        self.load_in_4bit = load_in_4bit
        self.load_in_8bit = load_in_8bit

        self.image_offloader = ImageOffloader()
        self.transcriber = LosslessTranscriber()
        self.structurer = SchemaStructurer(
            schema_path=schema_path,
            backend="transformers" if backend == "transformers" else ("ollama" if backend == "ollama" else "rule_based"),
            model_id=model,
            ollama_host=ollama_host,
            ollama_port=ollama_port,
            load_in_8bit=load_in_8bit,
            load_in_4bit=load_in_4bit
        )

        if backend in ("vlm_unified", "ollama") and UnifiedVLMEngine is not None:
            self.unified_engine = UnifiedVLMEngine(
                model_id=model,
                backend=backend,
                schema_path=schema_path,
                load_in_4bit=load_in_4bit,
                load_in_8bit=load_in_8bit,
                ollama_host=ollama_host,
                ollama_port=ollama_port,
                fallback_transcriber=self.transcriber
            )
        else:
            self.unified_engine = None

        if backend == "vlm_direct" and VLExtractor is not None:
            self.direct_extractor = VLExtractor(
                model_id=model,
                schema_path=schema_path,
                load_in_4bit=load_in_4bit
            )
        else:
            self.direct_extractor = None

    def run_security_gate(self, input_file: str) -> dict:
        """Scan input file for active threats before any parsing."""
        if not self.enable_security_gate or malware_gate is None:
            return {"verdict": "SKIPPED", "reason": "Security gate disabled or not available"}

        print(f"[Security Pre-Gate] Scanning {Path(input_file).name}...")
        try:
            res = malware_gate(input_file)
            print(f"  ✓ Pre-Gate Verdict: {res.get('verdict', 'CLEAN')}")
            return res
        except MalwareDetectedError as e:
            print(f"  ✗ BLOCKED by Pre-Gate: {e}")
            raise

    def process_file(
        self,
        input_file: str,
        output_file: str = None,
        stage: str = "all",
        image_storage_dir: str = None,
        keep_markdown: bool = True,
        dry_run: bool = False
    ) -> dict:
        """
        Execute the document processing pipeline using Qwen 3.6 VL.
        """
        input_path = Path(input_file)
        if not input_path.exists():
            return {"status": "error", "error": f"File not found: {input_file}"}

        stem = input_path.stem
        if not output_file:
            output_path = input_path.with_suffix(".json")
        else:
            output_path = Path(output_file)

        output_dir = output_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        if image_storage_dir is None:
            image_storage_dir = str(output_dir / f"images_{stem}")

        intermediate_md_path = str(output_dir / f"{stem}_intermediate.md")

        print(f"\n{'='*75}")
        print(f"Qwen 3.6 VL Document Pipeline v{self.VERSION}: {input_path.name}")
        print(f"Engine Backend: {self.backend.upper()} | Model: {self.model}")
        print(f"Stage Selection: {stage.upper()} | Output: {output_path.name}")
        print(f"{'='*75}")

        start_time = datetime.now()
        image_map = {}
        markdown_transcript = ""

        # --- Security Pre-Gate ---
        if input_path.suffix.lower() in ('.pdf', '.docx'):
            try:
                self.run_security_gate(str(input_path))
            except Exception as e:
                return {"status": "blocked", "error": str(e)}

        # Direct VLM Extractor Mode (Single Pass)
        if self.backend == "vlm_direct" and self.direct_extractor and input_path.suffix.lower() == '.pdf' and stage in ('all', '3'):
            print(f"\n[Direct VLM] Extracting master schema directly from visual renders with {self.model}...")
            result = self.direct_extractor.extract_from_pdf(str(input_path))
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            total_elapsed = (datetime.now() - start_time).total_seconds()
            print(f"✓ Direct VLM completed in {total_elapsed:.2f}s -> {output_path}")
            return {
                "status": "success",
                "output_json": str(output_path),
                "elapsed_seconds": total_elapsed,
                "data": result
            }

        # --- STAGE 1: Image & Diagram Deep Offloader ---
        if stage in ("1", "all") and input_path.suffix.lower() in ('.pdf', '.docx'):
            print(f"\n[Stage 1] Offloading embedded images & diagrams to deep storage...")
            if input_path.suffix.lower() == '.pdf':
                image_map = self.image_offloader.extract_from_pdf(str(input_path), image_storage_dir)
            elif input_path.suffix.lower() == '.docx':
                docx_images = self.image_offloader.extract_from_docx(str(input_path), image_storage_dir)
                image_map = {0: docx_images}

            if stage == "1":
                return {
                    "status": "success",
                    "stage": "1",
                    "images_extracted": sum(len(v) for v in image_map.values()) if isinstance(image_map, dict) else len(image_map),
                    "storage_dir": image_storage_dir,
                    "elapsed_seconds": (datetime.now() - start_time).total_seconds()
                }

        # --- STAGE 2: Multimodal Visual Transcription (Pass 1) ---
        if stage in ("2", "all") and input_path.suffix.lower() in ('.pdf', '.docx'):
            print(f"\n[Stage 2] Performing visual transcription with Qwen 3 VL ({self.model})...")
            if self.backend in ("vlm_unified", "ollama") and self.unified_engine and input_path.suffix.lower() == '.pdf':
                markdown_transcript = self.unified_engine.pass1_visual_transcribe(
                    pdf_path=str(input_path),
                    image_map=image_map,
                    output_md_path=intermediate_md_path if keep_markdown else None
                )
            else:
                if input_path.suffix.lower() == '.pdf':
                    res_transcribe = self.transcriber.transcribe_pdf(
                        str(input_path),
                        image_map=image_map,
                        output_md_path=intermediate_md_path if keep_markdown else None
                    )
                else:
                    res_transcribe = self.transcriber.transcribe_docx(
                        str(input_path),
                        image_list=image_map.get(0, []),
                        output_md_path=intermediate_md_path if keep_markdown else None
                    )
                markdown_transcript = res_transcribe.get("markdown_content", "")

            print(f"  ✓ Transcript generated ({len(markdown_transcript):,} chars)")

            if stage == "2" or dry_run:
                return {
                    "status": "success",
                    "stage": "2" if stage == "2" else "dry-run",
                    "intermediate_md": intermediate_md_path,
                    "total_characters": len(markdown_transcript),
                    "elapsed_seconds": (datetime.now() - start_time).total_seconds()
                }

        # If user is running Stage 3 on an already-existing Markdown file
        if stage == "3" and input_path.suffix.lower() == '.md':
            with open(input_path, "r", encoding="utf-8") as f:
                markdown_transcript = f.read()

        # --- STAGE 3: Master Schema Structuring (Pass 2) ---
        if stage in ("3", "all") and not dry_run:
            if not markdown_transcript and Path(intermediate_md_path).exists():
                with open(intermediate_md_path, "r", encoding="utf-8") as f:
                    markdown_transcript = f.read()

            if not markdown_transcript:
                return {"status": "error", "error": "No intermediate markdown available for Stage 3"}

            print(f"\n[Stage 3] Structuring markdown into Master Schema JSON with Qwen 3 VL ({self.model})...")
            if self.backend in ("vlm_unified", "ollama") and self.unified_engine:
                structured_data = self.unified_engine.pass2_structure_json(
                    markdown_text=markdown_transcript,
                    output_json_path=str(output_path),
                    source_file_name=input_path.name
                )
            else:
                structured_data = self.structurer.structure_transcript(
                    markdown_text=markdown_transcript,
                    output_json_path=str(output_path),
                    source_file_name=input_path.name
                )

            total_elapsed = (datetime.now() - start_time).total_seconds()
            print(f"\n{'='*75}")
            print(f"✓ Pipeline Completed Successfully in {total_elapsed:.2f}s")
            print(f"  JSON Output: {output_path}")
            print(f"  Intermediate Transcript: {intermediate_md_path}")
            print(f"  Offloaded Images: {image_storage_dir}")
            print(f"{'='*75}\n")

            return {
                "status": "success",
                "stage": "all" if stage == "all" else "3",
                "output_json": str(output_path),
                "intermediate_md": intermediate_md_path,
                "image_dir": image_storage_dir,
                "total_findings": len(structured_data.get("detailed_observations", [])),
                "elapsed_seconds": total_elapsed,
                "data": structured_data
            }

        return {"status": "success", "elapsed_seconds": (datetime.now() - start_time).total_seconds()}

    def batch_process(
        self,
        input_dir: str,
        output_dir: str,
        stage: str = "all",
        keep_markdown: bool = True,
        dry_run: bool = False
    ) -> list:
        """Batch process all PDF and DOCX documents in a folder."""
        in_path = Path(input_dir)
        files = list(in_path.glob("*.pdf")) + list(in_path.glob("*.docx"))
        if stage == "3":
            files += list(in_path.glob("*.md"))

        print(f"\n[Batch Mode] Found {len(files)} document(s) in {input_dir} using {self.model}")
        results = []

        for idx, doc_file in enumerate(files, 1):
            print(f"\n[{idx}/{len(files)}] Processing: {doc_file.name}")
            res = self.process_file(
                input_file=str(doc_file),
                output_file=str(Path(output_dir) / f"{doc_file.stem}.json"),
                stage=stage,
                keep_markdown=keep_markdown,
                dry_run=dry_run
            )
            results.append(res)

        return results


@click.command()
@click.option('--input', 'input_file', help='Input DOCX, PDF, or MD file path')
@click.option('--input-dir', help='Input directory for batch processing')
@click.option('--output', 'output_file', help='Output JSON file path')
@click.option('--output-dir', help='Output directory for batch mode')
@click.option('--stage', type=click.Choice(['1', '2', '3', 'all']), default='all', help='Pipeline stage to run (1=Images, 2=Markdown, 3=JSON Structuring, all=End-to-End)')
@click.option('--backend', type=click.Choice(['vlm_unified', 'vlm_direct', 'transformers', 'ollama', 'rule_based']), default='vlm_unified', help='Processing engine backend (default: vlm_unified)')
@click.option('--model', default=DEFAULT_PIPELINE_MODEL, help=f'Model identifier (default: {DEFAULT_PIPELINE_MODEL})')
@click.option('--ollama-host', default='localhost', help='Ollama server host')
@click.option('--ollama-port', type=int, default=11434, help='Ollama server port')
@click.option('--image-storage-dir', help='Custom directory for offloaded images')
@click.option('--dry-run', is_flag=True, help='Run Stages 1 and 2 only (generates intermediate markdown without LLM call)')
@click.option('--keep-markdown/--no-keep-markdown', default=True, help='Persist intermediate Markdown transcript')
def main(
    input_file,
    input_dir,
    output_file,
    output_dir,
    stage,
    backend,
    model,
    ollama_host,
    ollama_port,
    image_storage_dir,
    dry_run,
    keep_markdown
):
    """
    Qwen 3.6 VL Document Standardization Pipeline CLI.
    """
    load_dotenv()

    pipeline = DocumentPipeline(
        backend=backend,
        model=model,
        ollama_host=ollama_host,
        ollama_port=ollama_port
    )

    if input_file and input_dir:
        click.echo("Error: Specify either --input or --input-dir, not both")
        sys.exit(1)

    if input_file:
        res = pipeline.process_file(
            input_file=input_file,
            output_file=output_file,
            stage=stage,
            image_storage_dir=image_storage_dir,
            keep_markdown=keep_markdown,
            dry_run=dry_run
        )
        if res.get("status") in ("error", "blocked"):
            click.echo(f"Process ended with status: {res.get('status')} ({res.get('error')})")
            sys.exit(1)

    elif input_dir:
        out_dir = output_dir or "./output/"
        pipeline.batch_process(
            input_dir=input_dir,
            output_dir=out_dir,
            stage=stage,
            keep_markdown=keep_markdown,
            dry_run=dry_run
        )
    else:
        click.echo("Error: Please provide --input <file> or --input-dir <directory>")
        sys.exit(1)


if __name__ == "__main__":
    main()
