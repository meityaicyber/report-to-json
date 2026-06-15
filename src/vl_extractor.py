"""
Vision-Language Model (VLM) based extractor using HuggingFace Transformers.
Uses Qwen2.5-VL-7B-Instruct to extract JSON directly from PDF images, preserving layout context.
Loaded in 4-bit precision to fit within 8GB VRAM limits.
"""

import json
import re
import torch
import fitz  # PyMuPDF
from PIL import Image
from typing import List, Dict, Any, Optional
import io
import gc
import pdfplumber

from tqdm import tqdm
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info

try:
    from image_describer import ImageDescriber
except ImportError:
    ImageDescriber = None

class VLExtractor:
    def __init__(self, model_id: str = "Qwen/Qwen2-VL-7B-Instruct", max_pages_per_batch: int = 1):
        """
        Initialize the VLM Extractor.
        """
        self.model_id = model_id
        self.max_pages_per_batch = max_pages_per_batch
        self.model = None
        self.processor = None
        
    def _load_model(self):
        """Lazy load the model in 4-bit precision."""
        if self.model is None:
            print(f"[VLM] Loading model {self.model_id} in 4-bit precision... (This will take a moment)")
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                self.model_id,
                torch_dtype=torch.float16,
                device_map="auto",
                load_in_4bit=True
            )
            self.processor = AutoProcessor.from_pretrained(self.model_id)
            print(f"[VLM] Model loaded successfully.")

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
            # Skip rows where every cell is blank
            if any(cell for cell in clean_row):
                cleaned.append(clean_row)
        
        if not cleaned:
            return ""
            
        # Format as Markdown table
        headers = cleaned[0]
        md_lines = []
        md_lines.append("| " + " | ".join(headers) + " |")
        md_lines.append("|" + "|".join(["---"] * len(headers)) + "|")
        for row in cleaned[1:]:
            padded_row = row + [""] * (len(headers) - len(row))
            md_lines.append("| " + " | ".join(padded_row[:len(headers)]) + " |")
            
        return "\n".join(md_lines)

    def pdf_to_pages(self, pdf_path: str, zoom_x: float = 1.0, zoom_y: float = 1.0) -> List[dict]:
        """Convert PDF pages to PIL images and raw text."""
        print(f"[VLM] Extracting images and text from {pdf_path}...")
        pages = []
        try:
            doc = fitz.open(pdf_path)
            mat = fitz.Matrix(zoom_x, zoom_y)  # ~72 DPI
            with pdfplumber.open(pdf_path) as pdf_plumb:
                for page_num in tqdm(range(len(doc)), desc="Converting pages"):
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
            print(f"[VLM] Extracted {len(pages)} pages.")
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

    def _post_process_json(self, data):
        """Recursively flattens VLM-hallucinated nested structures like [{'Value': {}}] into 'Value'."""
        if isinstance(data, dict):
            new_dict = {}
            for k, v in data.items():
                norm_v = self._post_process_json(v)
                
                # Flatten 1-element lists
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
                
                # Flatten hallucinated dicts
                elif isinstance(norm_v, dict) and len(norm_v) == 1:
                    nested_k = list(norm_v.keys())[0]
                    nested_v = list(norm_v.values())[0]
                    if nested_v == {}:
                        new_dict[k] = nested_k
                    elif isinstance(nested_v, dict):
                        new_dict[k] = nested_k
                        for nk, nv in nested_v.items():
                            new_dict[nk] = nv
                    else:
                        new_dict[k] = norm_v
                else:
                    new_dict[k] = norm_v
                        
                # --- PLACEHOLDER SUBSTITUTION LOGIC ---
                if isinstance(new_dict[k], str):
                    import re
                    match = re.search(r'\[IMAGE_PAGE_(\d+)_FIG_(\d+)\]', new_dict[k])
                    if match and getattr(self, 'image_descriptions', None):
                        page_idx = int(match.group(1))
                        fig_idx = int(match.group(2)) - 1 # FIG_1 -> index 0
                        
                        page_descs = self.image_descriptions.get(page_idx, [])
                        if 0 <= fig_idx < len(page_descs):
                            new_dict[k] = new_dict[k].replace(match.group(0), f"[Image Description: {page_descs[fig_idx]}]")
                # --------------------------------------
                
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

    def extract_from_pdf(self, pdf_path: str, checkpoint_path: str = "checkpoint.json") -> dict:
        """
        Main entry point: convert PDF to images, batch them, and extract data.
        """
        pages_data = self.pdf_to_pages(pdf_path)
        
        if not pages_data:
            return {"_extraction_status": "failed", "_error": "No pages extracted from PDF"}

        # 1. Image Pre-Extraction and Batched Description
        self.image_descriptions = {}
        if ImageDescriber:
            describer = ImageDescriber(model_id=self.model_id)
            self.image_descriptions = describer.generate_descriptions(pdf_path)
        else:
            print("[VLM] Warning: image_describer module not found, placeholder substitution will not happen.")

        self._load_model()
        schema_prompt = self._get_schema_prompt()
        
        extracted_data = {}
        start_index = 0
        
        import os
        if os.path.exists(checkpoint_path):
            try:
                with open(checkpoint_path, 'r', encoding='utf-8') as f:
                    extracted_data = json.load(f)
                start_index = extracted_data.pop('_resume_batch_index', 0)
                print(f"[VLM] Resuming extraction from batch index {start_index}...")
            except Exception as e:
                print(f"[VLM] WARNING: Failed to load checkpoint: {e}")
                start_index = 0
                extracted_data = {}
        
        # Process in batches with tqdm
        total_batches = (len(pages_data) + self.max_pages_per_batch - 1) // self.max_pages_per_batch
        initial_batch = start_index // self.max_pages_per_batch
        
        for i in tqdm(range(start_index, len(pages_data), self.max_pages_per_batch), desc="Processing pages via VLM", initial=initial_batch, total=total_batches):
            batch_pages = pages_data[i:i + self.max_pages_per_batch]
            
            result = self._process_page_batch(batch_pages, schema_prompt)
            
            # Merge results recursively
            if result and isinstance(result, dict):
                extracted_data = self._deep_merge(extracted_data, result)
                
            # Write checkpoint
            extracted_data['_resume_batch_index'] = i + self.max_pages_per_batch
            try:
                with open(checkpoint_path, 'w', encoding='utf-8') as f:
                    json.dump(extracted_data, f, indent=2)
            except Exception as e:
                print(f"[VLM] WARNING: Failed to write checkpoint: {e}")
                
            # Clear CUDA cache after each batch
            torch.cuda.empty_cache()
            gc.collect()
            
        extracted_data.pop('_resume_batch_index', None)
        
        # Post-process the JSON to flatten VLM hallucinated nested structures
        print("[VLM] Post-processing JSON to clean irregularities...")
        extracted_data = self._post_process_json(extracted_data)
        extracted_data = self._post_process_json(extracted_data)  # Double pass for deep nesting
        
        return extracted_data

    def _process_page_batch(self, pages: List[dict], prompt_template: str) -> dict:
        """Process a batch of pages through the VLM."""
        images = [p["image"] for p in pages]
        raw_text = "\n\n".join([f"--- Page {p['page_num']} Text ---\n{p['text']}" for p in pages])
        tables_text = "\n\n".join([f"--- Page {p['page_num']} Tables ---\n{p.get('tables', '')}" for p in pages if p.get('tables')])
        
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
                repetition_penalty=1.05
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
                
        print("  [VLM] WARNING Failed to parse JSON. Raw output:")
        print(response_stripped[:500] + "...")
        return {}
    def _get_schema_prompt(self) -> str:
        """Get the prompt with the JSON schema instructions."""
        return '''You are a strict data formatting assistant. I will provide you with the RAW TEXT extracted from a PDF page, cleanly extracted TABLES from the page, and the IMAGE of the page.

RAW TEXT FROM PDF:
{RAW_TEXT}

CLEANLY EXTRACTED TABLES:
{CLEAN_TABLES}

INSTRUCTIONS:
1. Use the IMAGE to understand the layout and hierarchy.
2. Use the CLEANLY EXTRACTED TABLES for exact alignment, headers, and values of tabular data. This guarantees you do not miss any rows.
3. Use the RAW TEXT for the exact spelling of words, IPs, and CVEs outside of tables.
4. Reconstruct the page's information into a structured JSON format. Use the document's own headings as keys, and the content as values.
5. If there is a table, represent it as an array of JSON objects.
6. If you identify a complex diagram, chart, or photo on a page, do NOT attempt to describe it in the JSON. Instead, output a placeholder string in the format `[IMAGE_PAGE_X_FIG_Y]` as the value for that key. Replace X with the page number and Y with the figure number on that page (e.g. `[IMAGE_PAGE_0_FIG_1]`). I will substitute the description later.
7. If there is no meaningful text on the page, output exactly: {}

Return ONLY a valid JSON object. Start with { and end with }. No markdown fences, no explanations.
'''
