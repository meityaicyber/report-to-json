"""
vl_extractor.py
===============
Vision-Language Model (VLM) based extractor using HuggingFace Transformers.
Uses Qwen 3.6 VL (Qwen/Qwen3.6-VL) to extract structured JSON directly from PDF images,
preserving layout context, tables, and vulnerability hierarchies.
Loaded in 4-bit / 8-bit precision to fit within 8GB VRAM (e.g. RTX 4060).
"""

import json
import os
import re
import io
import gc
from pathlib import Path
from typing import List, Dict, Any, Optional

import fitz  # PyMuPDF
import pdfplumber
from PIL import Image
from tqdm import tqdm

try:
    import torch
    from transformers import (
        AutoModelForVision2Seq,
        AutoProcessor,
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
    BitsAndBytesConfig = None
    Qwen2_5_VLForConditionalGeneration = None
    Qwen2VLForConditionalGeneration = None

try:
    from qwen_vl_utils import process_vision_info
except ImportError:
    def process_vision_info(messages):
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

try:
    from image_describer import ImageDescriber
except ImportError:
    ImageDescriber = None

# Resolve master schema relative to this file's location (../master_schema.json)
_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "master_schema.json"
DEFAULT_VLM_MODEL = os.environ.get("VLM_MODEL", "Qwen/Qwen3.6-VL")


def _load_master_schema() -> dict:
    """Load the master schema from disk. Returns empty dict if not found."""
    try:
        with open(_SCHEMA_PATH, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[VLM] WARNING: master_schema.json not found at {_SCHEMA_PATH}. Output will not be schema-constrained.")
        return {}
    except Exception as e:
        print(f"[VLM] WARNING: Failed to load master_schema.json: {e}")
        return {}


class VLExtractor:
    def __init__(
        self,
        model_id: str = DEFAULT_VLM_MODEL,
        max_pages_per_batch: int = 1,
        schema_path: Optional[str] = None,
        load_in_4bit: bool = True
    ):
        """
        Initialize the Qwen 3.6 VL Direct Extractor.

        Parameters
        ----------
        model_id           : HuggingFace model ID for the VLM (e.g. Qwen/Qwen3.6-VL).
        max_pages_per_batch: Pages processed per VLM call. 1 is recommended for 8GB GPUs.
        schema_path        : Optional override path to master_schema.json.
        load_in_4bit       : Quantize to 4-bit NF4 to fit in 8GB VRAM.
        """
        self.model_id = model_id
        self.max_pages_per_batch = max_pages_per_batch
        self.load_in_4bit = load_in_4bit
        self.model = None
        self.processor = None
        self.image_descriptions = {}

        # Load the master schema once at construction time
        if schema_path:
            try:
                with open(schema_path, "r", encoding="utf-8-sig") as f:
                    self.master_schema = json.load(f)
            except Exception as e:
                print(f"[VLM] WARNING: Could not load schema from {schema_path}: {e}")
                self.master_schema = _load_master_schema()
        else:
            self.master_schema = _load_master_schema()

        if self.master_schema:
            print(f"[VLM] Master schema loaded ({len(self.master_schema)} keys)")
        else:
            print("[VLM] No master schema loaded. Inferred schema mode.")

    def _load_model(self):
        """Lazy load Qwen 3.6 VL with 4-bit NF4 quantization for 8GB VRAM."""
        if self.model is not None:
            return

        if torch is None:
            raise ImportError("PyTorch and Transformers are required to run VLExtractor.")

        candidate_models = list(dict.fromkeys([
            self.model_id,
            "Qwen/Qwen2-VL-7B-Instruct",
            "Qwen/Qwen2.5-VL-7B-Instruct",
            "Qwen/Qwen2.5-VL-3B-Instruct"
        ]))

        device_map = "auto" if torch.cuda.is_available() else "cpu"
        quant_config = None
        if torch.cuda.is_available() and BitsAndBytesConfig is not None and self.load_in_4bit:
            quant_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
                bnb_4bit_use_double_quant=True
            )

        dtype = torch.bfloat16 if (torch.cuda.is_available() and torch.cuda.is_bf16_supported()) else torch.float32

        loaded_model = None
        loaded_proc = None
        active_id = self.model_id

        for candidate in candidate_models:
            print(f"[VLM] Loading Vision Model {candidate} (4-bit NF4 for 8GB VRAM)...")
            try:
                proc = AutoProcessor.from_pretrained(candidate, trust_remote_code=True)
            except Exception:
                continue

            model_kwargs = {
                "trust_remote_code": True,
                "device_map": device_map
            }
            if quant_config:
                model_kwargs["quantization_config"] = quant_config
            else:
                model_kwargs["torch_dtype"] = dtype

            if AutoModelForVision2Seq is not None:
                try:
                    loaded_model = AutoModelForVision2Seq.from_pretrained(candidate, **model_kwargs)
                    loaded_proc = proc
                    active_id = candidate
                    break
                except Exception:
                    pass

            if loaded_model is None and Qwen2_5_VLForConditionalGeneration is not None:
                try:
                    loaded_model = Qwen2_5_VLForConditionalGeneration.from_pretrained(candidate, **model_kwargs)
                    loaded_proc = proc
                    active_id = candidate
                    break
                except Exception:
                    pass

            if loaded_model is None and Qwen2VLForConditionalGeneration is not None:
                try:
                    loaded_model = Qwen2VLForConditionalGeneration.from_pretrained(candidate, **model_kwargs)
                    loaded_proc = proc
                    active_id = candidate
                    break
                except Exception:
                    pass

        if loaded_model is None:
            raise RuntimeError(f"Could not load Vision Model from candidates {candidate_models}")

        self.model = loaded_model
        self.processor = loaded_proc
        self.model_id = active_id
        print(f"[VLM] Model {self.model_id} loaded successfully.")

    def _clean_and_format_table(self, raw_table: List[List]) -> str:
        """Clean and format a raw table extracted by pdfplumber into Markdown."""
        cleaned = []
        for row in raw_table:
            clean_row = []
            for cell in row:
                if cell is None:
                    clean_row.append("")
                else:
                    cell_text = str(cell).replace("\n", " ").strip()
                    clean_row.append(cell_text)
            if any(cell for cell in clean_row):
                cleaned.append(clean_row)

        if not cleaned:
            return ""

        headers = cleaned[0]
        md_lines = []
        md_lines.append("| " + " | ".join(headers) + " |")
        md_lines.append("|" + "|".join(["---"] * len(headers)) + "|")
        for row in cleaned[1:]:
            padded_row = row + [""] * (len(headers) - len(row))
            md_lines.append("| " + " | ".join(padded_row[:len(headers)]) + " |")

        return "\n".join(md_lines)

    def pdf_to_pages(self, pdf_path: str, zoom_x: float = 1.5, zoom_y: float = 1.5) -> List[dict]:
        """Convert PDF pages to PIL images and raw text at 150 DPI."""
        print(f"[VLM] Extracting images and layout from {pdf_path}...")
        pages = []
        try:
            doc = fitz.open(pdf_path)
            mat = fitz.Matrix(zoom_x, zoom_y)
            with pdfplumber.open(pdf_path) as pdf_plumb:
                for page_num in tqdm(range(len(doc)), desc="Rendering pages"):
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    text = page.get_text("text")

                    # Extract tables with pdfplumber
                    plumb_page = pdf_plumb.pages[page_num]
                    tables = plumb_page.extract_tables()
                    formatted_tables = []
                    for t_idx, raw_table in enumerate(tables):
                        if raw_table and len(raw_table) >= 2:
                            md_table = self._clean_and_format_table(raw_table)
                            if md_table:
                                formatted_tables.append(f"Table {t_idx + 1}:\n{md_table}")

                    tables_text = "\n\n".join(formatted_tables) if formatted_tables else ""
                    pages.append({"page_num": page_num, "image": img, "text": text, "tables": tables_text})
            doc.close()
            print(f"[VLM] Rendered {len(pages)} pages.")
        except Exception as e:
            print(f"[VLM] Error converting PDF: {e}")
        return pages

    def _deep_merge(self, dict1: dict, dict2: dict) -> dict:
        """Recursively merge dict2 into dict1."""
        for key, val2 in dict2.items():
            if key in dict1:
                val1 = dict1[key]
                if isinstance(val1, dict) and isinstance(val2, dict):
                    self._deep_merge(val1, val2)
                elif isinstance(val1, list) and isinstance(val2, list):
                    val1.extend(val2)
                elif isinstance(val1, str) and isinstance(val2, str):
                    dict1[key] = val1 + "\n" + val2
                else:
                    if not isinstance(val1, list):
                        dict1[key] = [val1]
                    if isinstance(val2, list):
                        dict1[key].extend(val2)
                    else:
                        dict1[key].append(val2)
            else:
                dict1[key] = val2
        return dict1

    def _post_process_json(self, data: Any) -> Any:
        """Recursively cleans and normalizes VLM structured JSON output."""
        if isinstance(data, dict):
            new_dict = {}
            for k, v in data.items():
                norm_v = self._post_process_json(v)
                if isinstance(norm_v, list) and len(norm_v) == 1:
                    v0 = norm_v[0]
                    if isinstance(v0, dict) and len(v0) == 1:
                        nested_k = list(v0.keys())[0]
                        nested_v = list(v0.values())[0]
                        new_dict[k] = nested_k
                        if isinstance(nested_v, dict) and nested_v:
                            for nk, nv in nested_v.items():
                                new_dict[nk] = nv
                    elif isinstance(v0, str):
                        new_dict[k] = v0
                    else:
                        new_dict[k] = norm_v
                elif isinstance(norm_v, dict) and len(norm_v) == 1:
                    nested_k = list(norm_v.keys())[0]
                    nested_v = list(norm_v.values())[0]
                    if nested_v == {}:
                        new_dict[k] = nested_k
                    else:
                        new_dict[k] = norm_v
                else:
                    new_dict[k] = norm_v
            return new_dict
        elif isinstance(data, list):
            new_list = []
            for item in data:
                norm_item = self._post_process_json(item)
                if isinstance(norm_item, dict) and len(norm_item) == 1 and list(norm_item.values())[0] == {}:
                    new_list.append(list(norm_item.keys())[0])
                else:
                    new_list.append(norm_item)
            return new_list
        else:
            return data

    def extract_from_pdf(self, pdf_path: str, checkpoint_path: Optional[str] = None) -> dict:
        """
        Main entry point: render PDF pages, send to Qwen 3.6 VL, and structure master JSON.
        """
        pages_data = self.pdf_to_pages(pdf_path)
        if not pages_data:
            return {"_extraction_status": "failed", "_error": "No pages extracted from PDF"}

        self._load_model()
        schema_prompt = self._get_schema_prompt()

        extracted_data = {}
        total_batches = (len(pages_data) + self.max_pages_per_batch - 1) // self.max_pages_per_batch

        for i in tqdm(
            range(0, len(pages_data), self.max_pages_per_batch),
            desc=f"Extracting with {self.model_id}",
            total=total_batches,
        ):
            batch_pages = pages_data[i : i + self.max_pages_per_batch]
            result = self._process_page_batch(batch_pages, schema_prompt)

            if result and isinstance(result, dict):
                extracted_data = self._deep_merge(extracted_data, result)

            if torch is not None and torch.cuda.is_available():
                torch.cuda.empty_cache()
                gc.collect()

        extracted_data = self._post_process_json(extracted_data)
        if "_meta" not in extracted_data:
            extracted_data["_meta"] = {}
        extracted_data["_meta"].update({
            "pipeline_version": "3.1.0-qwen3.6-vl",
            "source_file": Path(pdf_path).name,
            "structuring_backend": "qwen3.6_vl_direct",
            "engine": f"{self.model_id} (Qwen 3.6 VL Direct Extractor)"
        })

        return extracted_data

    def _process_page_batch(self, pages: List[dict], prompt_template: str) -> dict:
        """Process a batch of pages through Qwen 3.6 VL."""
        images = [p["image"] for p in pages]
        raw_text = "\n\n".join([f"--- Page {p['page_num'] + 1} Text ---\n{p['text']}" for p in pages])
        tables_text = "\n\n".join([f"--- Page {p['page_num'] + 1} Tables ---\n{p.get('tables', '')}" for p in pages if p.get('tables')])

        prompt_text = prompt_template.replace("{RAW_TEXT}", raw_text).replace("{CLEAN_TABLES}", tables_text)

        messages = [
            {
                "role": "user",
                "content": [
                    *[{"type": "image", "image": img} for img in images],
                    {"type": "text", "text": prompt_text},
                ],
            }
        ]

        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        image_inputs, video_inputs = process_vision_info(messages)
        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        ).to(self.model.device)

        with torch.no_grad():
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=4096,
                do_sample=False,
                temperature=0.0,
                repetition_penalty=1.05,
            )

        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]

        output_text = self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]

        return self._parse_json_response(output_text)

    def _parse_json_response(self, response: str) -> dict:
        """Parse JSON from VLM response."""
        response = re.sub(r'^```(?:json)?\n?', '', response, flags=re.MULTILINE)
        response = re.sub(r'\n?```$', '', response, flags=re.MULTILINE)
        response_stripped = response.strip()

        try:
            return json.loads(response_stripped)
        except Exception:
            pass

        first_brace = response_stripped.find('{')
        last_brace = response_stripped.rfind('}')
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            try:
                return json.loads(response_stripped[first_brace:last_brace + 1])
            except Exception:
                pass

        return {}

    def _get_schema_prompt(self) -> str:
        """Build the master schema prompt for Qwen 3.6 VL."""
        if self.master_schema:
            schema_block = (
                "MASTER OUTPUT SCHEMA (you MUST structure findings into this exact JSON schema):\n"
                + json.dumps(self.master_schema, indent=2)
            )
        else:
            schema_block = "Structure output into canonical VAPT JSON format."

        return f'''You are a cybersecurity audit report data structuring engine (Qwen 3.6 VL).
Look at the PAGE IMAGE and extract all findings, assets, scope tables, and auditor information into the schema.

RAW TEXT STREAM:
{{RAW_TEXT}}

EXTRACTED TABLES:
{{CLEAN_TABLES}}

{schema_block}

INSTRUCTIONS:
1. Use the PAGE IMAGE to preserve visual layout and document sections.
2. Extract all findings into `detailed_observations` with finding_id, title, severity, description, impact, and recommendation.
3. Output ONLY a valid JSON object matching the schema. Begin with {{ and end with }}. No markdown fences.'''
