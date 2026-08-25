import argparse
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import pdfplumber
from PIL import Image

try:
    import torch
    from transformers import AutoModelForVision2Seq, AutoProcessor, BitsAndBytesConfig
    try:
        from transformers import Qwen2_5_VLForConditionalGeneration
    except ImportError:
        Qwen2_5_VLForConditionalGeneration = None
except ImportError:
    torch = None
    AutoModelForVision2Seq = None
    AutoProcessor = None
    BitsAndBytesConfig = None
    Qwen2_5_VLForConditionalGeneration = None

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
                    if isinstance(item, dict) and item.get("type") == "image":
                        images.append(item["image"])
        return images if images else None, None

from tqdm import tqdm

DEFAULT_VLM_MODEL = os.environ.get("VLM_MODEL", "Qwen/Qwen3.6-VL")


def stitch_images(images: list[Image.Image]) -> Image.Image:
    total_height = sum(img.height for img in images)
    max_width = max(img.width for img in images)
    stitched = Image.new('RGB', (max_width, total_height), (255, 255, 255))
    y_offset = 0
    for img in images:
        stitched.paste(img, (0, y_offset))
        y_offset += img.height
    return stitched


def _post_process_json(data: Any) -> Any:
    """Recursively flattens {"Value": {}} hallucinations into clean key-value pairs."""
    if isinstance(data, dict):
        if len(data) == 1:
            k = list(data.keys())[0]
            v = data[k]
            if isinstance(v, dict) and not v:
                return k
        return {k: _post_process_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        if len(data) == 1 and isinstance(data[0], dict):
            single_dict = data[0]
            if len(single_dict) == 1:
                k = list(single_dict.keys())[0]
                v = single_dict[k]
                if isinstance(v, dict) and not v:
                    return k
        return [_post_process_json(item) for item in data]
    else:
        return data


class HybridExtractor:
    def __init__(self, model_id: str = DEFAULT_VLM_MODEL, load_in_4bit: bool = True):
        self.model_id = model_id
        self.load_in_4bit = load_in_4bit
        self.model = None
        self.processor = None

    def _load_model(self):
        if self.model is None:
            print(f"[Hybrid VLM] Loading {self.model_id} (4-bit NF4 quantized for 8GB VRAM)...")
            self.processor = AutoProcessor.from_pretrained(self.model_id, trust_remote_code=True)
            
            device_map = "auto" if (torch is not None and torch.cuda.is_available()) else "cpu"
            quant_config = None
            if torch is not None and torch.cuda.is_available() and BitsAndBytesConfig is not None and self.load_in_4bit:
                quant_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
                    bnb_4bit_use_double_quant=True
                )

            model_kwargs = {
                "trust_remote_code": True,
                "device_map": device_map
            }
            if quant_config:
                model_kwargs["quantization_config"] = quant_config
            elif torch is not None:
                model_kwargs["torch_dtype"] = torch.bfloat16 if torch.cuda.is_available() else torch.float32

            loaded = None
            if AutoModelForVision2Seq is not None:
                try:
                    loaded = AutoModelForVision2Seq.from_pretrained(self.model_id, **model_kwargs)
                except Exception:
                    pass
            if loaded is None and Qwen2_5_VLForConditionalGeneration is not None:
                loaded = Qwen2_5_VLForConditionalGeneration.from_pretrained(self.model_id, **model_kwargs)

            self.model = loaded
            print("[Hybrid VLM] Model loaded successfully.")

    def _extract_table_groups(self, pdf_path: str) -> List[Dict]:
        print("[1/3] Geometrically detecting and linking tables via pdfplumber...")
        table_groups = []
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                tables = page.find_tables()
                for t_idx, table in enumerate(tables):
                    x0, top, x1, bottom = table.bbox
                    x0 = max(0, x0 - 5)
                    top = max(0, top - 5)
                    x1 = min(page.width, x1 + 5)
                    bottom = min(page.height, bottom + 5)
                    cropped_page = page.crop((x0, top, x1, bottom))
                    img = cropped_page.to_image(resolution=200).original
                    
                    is_continuation = False
                    if table_groups:
                        prev_group = table_groups[-1]
                        if prev_group["pages"][-1] == page_num - 1 and t_idx == 0:
                            prev_table_raw = prev_group["raw_tables"][-1]
                            curr_table_raw = table.extract()
                            if prev_table_raw and curr_table_raw and len(prev_table_raw[0]) == len(curr_table_raw[0]):
                                is_continuation = True
                    
                    if is_continuation:
                        prev_group = table_groups[-1]
                        prev_group["images"].append(img)
                        prev_group["pages"].append(page_num)
                        prev_group["raw_tables"].append(table.extract())
                    else:
                        table_groups.append({
                            "id": f"page{page_num}_table{t_idx+1}",
                            "images": [img],
                            "pages": [page_num],
                            "raw_tables": [table.extract()]
                        })
        print(f"      Detected {len(table_groups)} logical tables across {len(pdf.pages)} pages.")
        return table_groups

    def extract(self, pdf_path: str, output_path: str):
        table_groups = self._extract_table_groups(pdf_path)
        
        self._load_model()
        print(f"[2/3] Processing stitched table images through {self.model_id}...")
        
        final_json = []
        for idx, group in enumerate(tqdm(table_groups, desc="Extracting Tables via VLM")):
            if len(group["images"]) > 1:
                stitched_img = stitch_images(group["images"])
            else:
                stitched_img = group["images"][0]
                
            prompt_text = "Extract the structured data from this table into a perfectly formatted JSON array of objects. Use the header row for keys. Only output valid JSON without any markdown formatting."
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "image": stitched_img,
                        },
                        {"type": "text", "text": prompt_text},
                    ],
                }
            ]
            
            text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            image_inputs, video_inputs = process_vision_info(messages)
            inputs = self.processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt"
            ).to(self.model.device)
            
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=4096,
                    do_sample=False,
                    temperature=0,
                    repetition_penalty=1.05,
                )
                
            generated_ids_trimmed = [
                out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            output_text = self.processor.batch_decode(
                generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )[0]
            
            clean_text = output_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
                
            try:
                table_json = json.loads(clean_text)
                table_json = _post_process_json(table_json)
            except Exception as e:
                print(f"Warning: Failed to parse JSON for {group['id']}: {e}")
                table_json = {"raw_text_fallback": clean_text}
                
            final_json.append({
                "table_id": group["id"],
                "pages": group["pages"],
                "data": table_json
            })
            
            del stitched_img
            del inputs
            del generated_ids
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
        print("\n[3/3] Saving final polished JSON...")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(final_json, f, indent=2, ensure_ascii=False)
        print(f"      Saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Hybrid PDF Table Extractor using Qwen 3.6 VL")
    parser.add_argument("--pdf", required=True, help="Path to PDF")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--model", default=DEFAULT_VLM_MODEL, help="Model ID")
    args = parser.parse_args()
    
    extractor = HybridExtractor(model_id=args.model)
    extractor.extract(args.pdf, args.output)


if __name__ == "__main__":
    main()
