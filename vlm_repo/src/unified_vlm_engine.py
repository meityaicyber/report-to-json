"""
unified_vlm_engine.py
=====================
Unified 2-Pass VLM Processing Engine (Optimized for Qwen 3 VL / Qwen 3.6 VL on 8GB VRAM).
Executes both stages sequentially:
  - Pass 1: Visual-to-Markdown Transcriber (Multimodal Vision mode: page-by-page visual extraction)
  - Pass 2: Vision/Text-to-JSON Schema Structurer (Canonical master_schema.json mapping)

Supports:
  1. Ollama Vision-Language backend (qwen3-vl:8b, qwen2.5vl:latest) via http://localhost:11434
  2. Local HuggingFace Transformers (4-bit NF4 quantized on CUDA)
"""

import base64
import gc
import io
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
from PIL import Image

import fitz  # PyMuPDF

try:
    import torch
    from transformers import (
        AutoModelForVision2Seq,
        AutoProcessor,
        AutoTokenizer,
        BitsAndBytesConfig
    )
    try:
        from transformers import Qwen2_5_VLForConditionalGeneration
    except ImportError:
        Qwen2_5_VLForConditionalGeneration = None
    try:
        from transformers import Qwen2VLForConditionalGeneration
    except ImportError:
        Qwen2VLForConditionalGeneration = None
except ImportError:
    torch = None
    AutoModelForVision2Seq = None
    AutoProcessor = None
    AutoTokenizer = None
    BitsAndBytesConfig = None
    Qwen2_5_VLForConditionalGeneration = None
    Qwen2VLForConditionalGeneration = None

try:
    from qwen_vl_utils import process_vision_info
except ImportError:
    def process_vision_info(messages):
        """Fallback vision extractor if qwen_vl_utils is not installed."""
        images = []
        videos = []
        for msg in messages:
            content = msg.get("content", [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "image" and "image" in item:
                            img = item["image"]
                            if isinstance(img, str) and (img.startswith("http") or os.path.exists(img)):
                                img = Image.open(img).convert("RGB")
                            images.append(img)
                        elif item.get("type") == "video" and "video" in item:
                            videos.append(item["video"])
        return images if images else None, videos if videos else None

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from .image_offloader import ImageOffloader
    from .lossless_transcriber import LosslessTranscriber
except ImportError:
    from image_offloader import ImageOffloader
    from lossless_transcriber import LosslessTranscriber


DEFAULT_VLM_MODEL = os.environ.get("VLM_MODEL", "qwen3-vl:8b")


class UnifiedVLMEngine:
    """Single-model 2-pass engine for visual transcription and schema structuring using Qwen 3 VL."""

    def __init__(
        self,
        model_id: str = DEFAULT_VLM_MODEL,
        backend: str = "ollama",
        schema_path: Optional[str] = None,
        load_in_4bit: bool = True,
        load_in_8bit: bool = False,
        max_batch_pages: int = 1,
        fallback_transcriber: Optional[LosslessTranscriber] = None,
        ollama_host: str = "localhost",
        ollama_port: int = 11434,
        api_base_url: Optional[str] = None
    ):
        self.backend = backend
        self.model_id = model_id
        self.load_in_4bit = load_in_4bit
        self.load_in_8bit = load_in_8bit
        self.max_batch_pages = max_batch_pages
        self.ollama_host = ollama_host
        self.ollama_port = ollama_port
        self.api_base_url = api_base_url or os.environ.get("VLM_API_URL", "")

        # Determine if Ollama backend is active
        self.use_ollama = (
            backend == "ollama"
            or "qwen3" in model_id.lower()
            or "ollama" in model_id.lower()
            or "qwen2.5vl" in model_id.lower()
            or model_id.startswith("qwen3-vl")
        )
        if "qwen3" in model_id.lower() or model_id in ("qwen3-vl", "qwen3-vl:8b", "Qwen/Qwen3.6-VL"):
            self.ollama_model = "qwen3-vl:8b"
        elif ":" in model_id:
            self.ollama_model = model_id
        else:
            self.ollama_model = "qwen3-vl:8b"

        # Resolve master schema
        if schema_path and Path(schema_path).exists():
            self.schema_path = Path(schema_path)
        else:
            self.schema_path = Path(__file__).resolve().parent.parent / "master_schema.json"

        self.master_schema = self._load_schema()
        self.fallback_transcriber = fallback_transcriber or LosslessTranscriber()
        self.image_offloader = ImageOffloader()

        self.model = None
        self.processor = None
        self.tokenizer = None
        self._vlm_initialized = False

    def _load_schema(self) -> dict:
        if self.schema_path.exists():
            try:
                with open(self.schema_path, "r", encoding="utf-8-sig") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Unified VLM] WARNING: Could not parse schema at {self.schema_path}: {e}")
        return {}

    def _load_model(self):
        """Lazy initialization of VLM model (Ollama or local HF Transformers)."""
        if self._vlm_initialized:
            return

        if self.use_ollama:
            url = f"http://{self.ollama_host}:{self.ollama_port}/api/tags"
            try:
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    models = [m.get("name", "") for m in resp.json().get("models", [])]
                    print(f"[Unified VLM] Connected to Ollama server ({self.ollama_host}:{self.ollama_port}). Model: '{self.ollama_model}' (Available: {models})", flush=True)
                    self._vlm_initialized = True
                    return
            except Exception as e:
                print(f"[Unified VLM] WARNING: Could not reach Ollama ({e}). Falling back to local Transformers...", flush=True)
                self.use_ollama = False

        if torch is None or AutoProcessor is None:
            raise ImportError(
                "PyTorch and Transformers are required to run UnifiedVLMEngine locally. "
                "Install with: pip install torch torchvision transformers accelerate bitsandbytes"
            )

        candidate_models = list(dict.fromkeys([
            self.model_id,
            "Qwen/Qwen2-VL-7B-Instruct",
            "Qwen/Qwen2.5-VL-7B-Instruct",
            "Qwen/Qwen2.5-VL-3B-Instruct"
        ]))

        device_map = "auto" if torch.cuda.is_available() else "cpu"
        quant_config = None

        if torch.cuda.is_available() and BitsAndBytesConfig is not None:
            if self.load_in_4bit:
                print("[Unified VLM] Applying 4-bit NF4 Quantization (Optimized for 8GB VRAM)...", flush=True)
                quant_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
                    bnb_4bit_use_double_quant=True
                )
            elif self.load_in_8bit:
                print("[Unified VLM] Applying 8-bit Quantization...", flush=True)
                quant_config = BitsAndBytesConfig(load_in_8bit=True)

        dtype = torch.bfloat16 if (torch.cuda.is_available() and torch.cuda.is_bf16_supported()) else (torch.float16 if torch.cuda.is_available() else torch.float32)

        loaded_model = None
        loaded_processor = None
        active_model_id = self.model_id
        load_errors = []

        for candidate in candidate_models:
            print(f"\n[Unified VLM] Attempting to load Vision-Language Model: {candidate}...", flush=True)
            try:
                proc = AutoProcessor.from_pretrained(candidate, trust_remote_code=True)
            except Exception as e:
                load_errors.append(f"AutoProcessor ({candidate}): {e}")
                continue

            model_kwargs = {
                "trust_remote_code": True,
                "device_map": device_map,
            }
            if quant_config is not None:
                model_kwargs["quantization_config"] = quant_config
            else:
                model_kwargs["torch_dtype"] = dtype

            # Try loading via AutoModelForVision2Seq
            if AutoModelForVision2Seq is not None:
                try:
                    loaded_model = AutoModelForVision2Seq.from_pretrained(candidate, **model_kwargs)
                    loaded_processor = proc
                    active_model_id = candidate
                    break
                except Exception as e:
                    load_errors.append(f"AutoModelForVision2Seq ({candidate}): {e}")

            # Try loading via Qwen2_5_VLForConditionalGeneration
            if loaded_model is None and Qwen2_5_VLForConditionalGeneration is not None:
                try:
                    loaded_model = Qwen2_5_VLForConditionalGeneration.from_pretrained(candidate, **model_kwargs)
                    loaded_processor = proc
                    active_model_id = candidate
                    break
                except Exception as e:
                    load_errors.append(f"Qwen2_5_VLForConditionalGeneration ({candidate}): {e}")

            # Try loading via Qwen2VLForConditionalGeneration
            if loaded_model is None and Qwen2VLForConditionalGeneration is not None:
                try:
                    loaded_model = Qwen2VLForConditionalGeneration.from_pretrained(candidate, **model_kwargs)
                    loaded_processor = proc
                    active_model_id = candidate
                    break
                except Exception as e:
                    load_errors.append(f"Qwen2VLForConditionalGeneration ({candidate}): {e}")

        if loaded_model is None:
            raise RuntimeError(
                f"Failed to load VLM model. Errors encountered:\n" + "\n".join(load_errors)
            )

        self.model = loaded_model
        self.processor = loaded_processor
        self.model_id = active_model_id
        self._vlm_initialized = True
        
        gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
        print(f"[Unified VLM] Model '{self.model_id}' successfully loaded on {gpu_name}.", flush=True)

    # ──────────────────────────────────────────────────────────────────────────
    # PASS 1: Visual-to-Markdown Transcription (Multimodal Vision Mode)
    # ──────────────────────────────────────────────────────────────────────────

    def pass1_visual_transcribe(
        self,
        pdf_path: str,
        image_map: Optional[Dict[int, List[Dict[str, Any]]]] = None,
        output_md_path: Optional[str] = None
    ) -> str:
        """
        Pass 1: Renders pages and passes them through Qwen 3 VL to generate
        complete, lossless Markdown preserving all layout, tables, and visual structure.
        """
        if image_map is None:
            image_map = {}

        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        transcribed_pages = []
        vlm_success_count = 0

        engine_name = f"Ollama {self.ollama_model}" if self.use_ollama else f"Qwen 3 VL ({self.model_id})"
        print(f"\n[Pass 1/2: Visual Transcriber] Processing {total_pages} page(s) visually with {engine_name}...", flush=True)

        has_vlm = True
        try:
            self._load_model()
        except Exception as e:
            print(f"[Pass 1] VLM load notice ({e}). Falling back to layout transcriber...", flush=True)
            has_vlm = False

        if not has_vlm:
            res = self.fallback_transcriber.transcribe_pdf(pdf_path, image_map=image_map, output_md_path=output_md_path)
            return res.get("markdown_content", "")

        for page_num in range(total_pages):
            fitz_page = doc.load_page(page_num)
            # Render page at 150 DPI for optimal visual clarity & VRAM efficiency
            pix = fitz_page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
            pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Retrieve offloaded image tokens for this page
            page_images = image_map.get(page_num, [])
            image_tokens_str = ""
            if page_images:
                tokens = [f"{item['placeholder']} ({item['filename']})" for item in page_images]
                image_tokens_str = f"\nEmbedded image tokens to preserve on this page: {', '.join(tokens)}"

            prompt_text = f"""You are a precise cybersecurity audit report visual transcription engine (Qwen 3 VL).
Transcribe ALL content visible on this page into clean, exhaustive GitHub-flavored Markdown.

Rules:
1. Transcribe ALL paragraphs, headings, vulnerability findings, bullet lists, IPs, URLs, CVEs, CWEs, and cell data without summarizing or dropping anything.
2. Format all visual tables cleanly as Markdown tables with headers and rows. Do NOT fragment tables.
3. If an embedded image token is mentioned below, insert it at the exact location where that figure or screenshot appears on the page.
{image_tokens_str}

Output ONLY the Markdown transcript of this page. No commentary."""

            page_md = ""

            # --- OLLAMA PATH ---
            if self.use_ollama:
                try:
                    buf = io.BytesIO()
                    pil_img.save(buf, format="PNG")
                    b64_image = base64.b64encode(buf.getvalue()).decode("utf-8")
                    url = f"http://{self.ollama_host}:{self.ollama_port}/api/chat"
                    payload = {
                        "model": self.ollama_model,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt_text,
                                "images": [b64_image]
                            }
                        ],
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "num_ctx": 32768
                        }
                    }
                    resp = requests.post(url, json=payload, timeout=120)
                    if resp.status_code == 200:
                        page_md = resp.json().get("message", {}).get("content", "").strip()
                        vlm_success_count += 1
                    else:
                        raise RuntimeError(f"Ollama returned HTTP {resp.status_code}: {resp.text}")
                except Exception as e:
                    print(f"[Pass 1] Ollama inference notice on page {page_num + 1}: {e}. Extracting page text stream.", flush=True)
                    raw_text = fitz_page.get_text("text").strip()
                    page_md = raw_text

            # --- TRANSFORMERS PATH ---
            else:
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image", "image": pil_img},
                            {"type": "text", "text": prompt_text}
                        ]
                    }
                ]
                try:
                    if self.processor is not None:
                        text_input = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                        image_inputs, video_inputs = process_vision_info(messages)
                        inputs = self.processor(
                            text=[text_input],
                            images=image_inputs,
                            videos=video_inputs,
                            padding=True,
                            return_tensors="pt"
                        ).to(self.model.device)

                        with torch.no_grad():
                            generated_ids = self.model.generate(
                                **inputs,
                                max_new_tokens=1536,
                                do_sample=False,
                                repetition_penalty=1.05
                            )

                        trimmed_ids = [out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)]
                        page_md = self.processor.batch_decode(
                            trimmed_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False
                        )[0].strip()
                        vlm_success_count += 1
                    else:
                        raise RuntimeError("Processor not initialized")

                except Exception as e:
                    print(f"[Pass 1] VLM visual inference notice on page {page_num + 1}: {e}. Extracting page text stream.", flush=True)
                    raw_text = fitz_page.get_text("text").strip()
                    page_md = raw_text

            # Clean markdown formatting fences if returned
            page_md = re.sub(r"^```(?:markdown|md)?\s*", "", page_md, flags=re.IGNORECASE)
            page_md = re.sub(r"\s*```$", "", page_md)

            # Format page section
            page_block = f"<!-- PAGE_START: {page_num + 1} -->\n## Page {page_num + 1}\n\n{page_md}\n\n<!-- PAGE_END: {page_num + 1} -->"
            transcribed_pages.append(page_block)
            percent_done = int(((page_num + 1) / total_pages) * 100)
            tag = f"Ollama {self.ollama_model}" if self.use_ollama else ('Qwen 3 VL' if vlm_success_count > page_num else 'Layout Parser')
            print(f"  ✓ Transcribed Page {page_num + 1}/{total_pages} ({percent_done}% complete - {len(page_md):,} chars via {tag})", flush=True)

            # Free cache after each page to prevent VRAM accumulation
            if torch is not None and torch.cuda.is_available() and not self.use_ollama:
                torch.cuda.empty_cache()
                gc.collect()

        doc.close()

        engine_tag = f"Ollama {self.ollama_model}" if self.use_ollama else (f"Qwen 3 VL ({self.model_id})" if vlm_success_count > 0 else "Layout Parser")
        full_markdown = (
            f"# Document Transcript: {Path(pdf_path).name}\n\n"
            f"*Pages: {total_pages} | Generated via {engine_tag} (Pass 1)*\n\n"
            + "\n\n---\n\n".join(transcribed_pages)
        )

        if output_md_path:
            out_file = Path(output_md_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(full_markdown)
            print(f"[Pass 1] Saved intermediate Markdown ({len(full_markdown):,} chars) to: {out_file}", flush=True)

        return full_markdown

    # ──────────────────────────────────────────────────────────────────────────
    # PASS 2: Schema Structuring (Text/Vision-to-JSON Mode)
    # ──────────────────────────────────────────────────────────────────────────

    def pass2_structure_json(
        self,
        markdown_text: str,
        output_json_path: Optional[str] = None,
        source_file_name: str = ""
    ) -> Dict[str, Any]:
        """
        Pass 2: Uses Qwen 3 VL to structure the intermediate Markdown
        into canonical master_schema.json format.
        """
        engine_name = f"Ollama {self.ollama_model}" if self.use_ollama else f"Qwen 3 VL ({self.model_id})"
        print(f"\n[Pass 2/2: Schema Structurer] Structuring markdown into canonical Master JSON schema via {engine_name}...", flush=True)
        schema_json_str = json.dumps(self.master_schema, indent=2)

        prompt = f"""You are a cybersecurity audit report data structuring engine.
I will provide you with the COMPLETE MARKDOWN TRANSCRIPT of a technical VAPT audit report.

Your task is to structure 100% of this information into a single valid JSON document matching the EXACT TARGET MASTER SCHEMA.

========================
TARGET MASTER SCHEMA:
========================
{schema_json_str}

========================
DOCUMENT TRANSCRIPT:
========================
{markdown_text}

========================
STRICT INSTRUCTIONS:
========================
1. Extract ALL information without dropping or summarizing any details.
2. In `engagement_scope.assets`, extract every in-scope URL, IP address, and target system from scope tables.
3. In `auditing_team`, extract every auditor name, designation, email, and certification (CEH, CISA, etc.).
4. In `detailed_observations`, populate every finding with finding_id, title, status, severity, observation_description, preconditions, impact, likely_root_cause, recommendation, and reference.
5. In `proof_of_concept_steps`, retain all embedded image tokens (e.g. `[IMAGE_PAGE_X_FIG_Y]`) at the exact steps where they illustrate the vulnerability.
6. Output ONLY a valid JSON object starting with {{ and ending with }}. No markdown fences. No explanation.
"""

        structured_json = {}
        used_vlm = False

        # --- OLLAMA PATH ---
        if self.use_ollama:
            try:
                url = f"http://{self.ollama_host}:{self.ollama_port}/api/chat"
                payload = {
                    "model": self.ollama_model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "format": "json",
                    "stream": False,
                    "options": {
                        "temperature": 0.0,
                        "num_ctx": 65536
                    }
                }
                resp = requests.post(url, json=payload, timeout=300)
                if resp.status_code == 200:
                    output_text = resp.json().get("message", {}).get("content", "")
                    structured_json = self._parse_json(output_text)
                    if "_error" not in structured_json:
                        used_vlm = True
            except Exception as e:
                print(f"[Pass 2] Ollama JSON structuring notice ({e}). Using deterministic structurer...", flush=True)
                from schema_structurer import SchemaStructurer
                fallback = SchemaStructurer(schema_path=str(self.schema_path), backend="rule_based")
                structured_json = fallback._rule_based_structuring(markdown_text)

        # --- TRANSFORMERS PATH ---
        else:
            try:
                self._load_model()
                messages = [{"role": "user", "content": prompt}]
                
                if self.processor is not None:
                    chat_text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                    inputs = self.processor(text=[chat_text], images=None, return_tensors="pt").to(self.model.device)
                elif self.tokenizer is not None:
                    chat_text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                    inputs = self.tokenizer([chat_text], return_tensors="pt").to(self.model.device)
                else:
                    raise RuntimeError("No processor or tokenizer available")

                with torch.no_grad():
                    generated_ids = self.model.generate(
                        **inputs,
                        max_new_tokens=4096,
                        do_sample=False,
                        repetition_penalty=1.05
                    )

                trimmed_ids = [out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)]
                
                if self.processor is not None:
                    output_text = self.processor.batch_decode(
                        trimmed_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False
                    )[0]
                else:
                    output_text = self.tokenizer.batch_decode(
                        trimmed_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False
                    )[0]

                structured_json = self._parse_json(output_text)
                if "_error" not in structured_json:
                    used_vlm = True
            except Exception as e:
                print(f"[Pass 2] Qwen 3 VL execution notice ({e}). Using deterministic semantic structurer...", flush=True)
                from schema_structurer import SchemaStructurer
                fallback = SchemaStructurer(schema_path=str(self.schema_path), backend="rule_based")
                structured_json = fallback._rule_based_structuring(markdown_text)

        if "_meta" not in structured_json:
            structured_json["_meta"] = {}
        
        backend_tag = f"ollama_{self.ollama_model}" if self.use_ollama else ("qwen3_vl_pass2" if used_vlm else "rule_based_fallback")
        structured_json["_meta"]["pipeline_version"] = "3.1.0-qwen3-vl"
        structured_json["_meta"]["structuring_backend"] = backend_tag
        structured_json["_meta"]["model"] = self.ollama_model if self.use_ollama else self.model_id
        if source_file_name:
            structured_json["_meta"]["source_file"] = source_file_name

        if output_json_path:
            out_path = Path(output_json_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(structured_json, f, indent=2, ensure_ascii=False)
            print(f"[Pass 2] Successfully structured & saved JSON to: {out_path}", flush=True)

        return structured_json

    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Extract and parse JSON from model output."""
        cleaned = text.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except Exception:
            pass

        first_brace = cleaned.find("{")
        last_brace = cleaned.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            try:
                return json.loads(cleaned[first_brace:last_brace + 1])
            except Exception as e:
                print(f"[Unified VLM] JSON parse notice: {e}", flush=True)

        return {"_error": "Failed to parse model output as JSON", "raw_output": text[:2000]}
