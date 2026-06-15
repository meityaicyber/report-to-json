import argparse
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pdfplumber
from PIL import Image, ImageDraw, ImageFont
import torch
from tqdm import tqdm
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
import fitz  # PyMuPDF


def stitch_images(images: list[Image.Image]) -> Image.Image:
    """Stitch multiple table crop images vertically into one tall image."""
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
    """
    Extracts tables from PDFs using geometric detection (pdfplumber) and
    VLM-based parsing (Qwen2.5-VL). Handles multi-page table stitching.
    
    Can be used standalone or as part of the pipeline's first-pass flow:
    - extract_table_groups_only(): Detect table bounding boxes without VLM
    - parse_table_group(): Parse a single table group through VLM → JSON
    - render_cleaned_pages(): Render PDF pages with tables/images replaced by placeholders
    """

    def __init__(self, model_id: str = "Qwen/Qwen2.5-VL-7B-Instruct",
                 model=None, processor=None):
        """
        Initialize HybridExtractor.
        
        Args:
            model_id: HuggingFace model ID for VLM
            model: Pre-loaded model instance (for sharing across extractors)
            processor: Pre-loaded processor instance (for sharing across extractors)
        """
        self.model_id = model_id
        self.model = model
        self.processor = processor

    def _load_model(self):
        """Lazy load the model in 8-bit precision (fits comfortably in 16GB VRAM)."""
        if self.model is None:
            print(f"[Hybrid VLM] Loading model {self.model_id} in 8-bit precision...")
            from transformers import BitsAndBytesConfig
            quant_config = BitsAndBytesConfig(load_in_8bit=True)
            self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                self.model_id,
                torch_dtype=torch.float16,
                device_map="auto",
                quantization_config=quant_config
            )
            self.processor = AutoProcessor.from_pretrained(self.model_id)
            print("[Hybrid VLM] Model loaded successfully.")

    def extract_table_groups_only(self, pdf_path: str) -> List[Dict]:
        """
        Detect and group tables geometrically using pdfplumber.
        Does NOT run VLM — just returns table groups with bounding boxes,
        page images, and raw table data.
        
        Each group contains:
        - id: Unique identifier (e.g. "page3_table1")
        - images: List of cropped PIL images of the table region
        - pages: List of page numbers where this table appears
        - raw_tables: List of raw table data from pdfplumber
        - bboxes: List of (page_num, x0, top, x1, bottom) bounding boxes
        
        Returns:
            List of table group dicts
        """
        print("[HybridExtractor] Geometrically detecting and linking tables...")
        table_groups = []
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                tables = page.find_tables()
                for t_idx, table in enumerate(tables):
                    # Crop the page using the table's bbox with padding
                    x0, top, x1, bottom = table.bbox
                    x0 = max(0, x0 - 5)
                    top = max(0, top - 5)
                    x1 = min(page.width, x1 + 5)
                    bottom = min(page.height, bottom + 5)
                    cropped_page = page.crop((x0, top, x1, bottom))
                    # Render at 200 DPI for good clarity
                    img = cropped_page.to_image(resolution=200).original

                    # Geometric continuity check: if this table is at the top of a
                    # page and the previous table was at the bottom of the prior page,
                    # and column counts match, treat as continuation
                    is_continuation = False
                    if table_groups:
                        prev_group = table_groups[-1]
                        if prev_group["pages"][-1] == page_num - 1 and t_idx == 0:
                            prev_table_raw = prev_group["raw_tables"][-1]
                            curr_table_raw = table.extract()
                            if (prev_table_raw and curr_table_raw and
                                    len(prev_table_raw[0]) == len(curr_table_raw[0])):
                                is_continuation = True

                    if is_continuation:
                        prev_group = table_groups[-1]
                        prev_group["images"].append(img)
                        prev_group["pages"].append(page_num)
                        prev_group["raw_tables"].append(table.extract())
                        prev_group["bboxes"].append((page_num, x0, top, x1, bottom))
                    else:
                        table_groups.append({
                            "id": f"page{page_num}_table{t_idx + 1}",
                            "images": [img],
                            "pages": [page_num],
                            "raw_tables": [table.extract()],
                            "bboxes": [(page_num, x0, top, x1, bottom)]
                        })

        print(f"[HybridExtractor] Detected {len(table_groups)} logical tables.")
        return table_groups

    def parse_table_group(self, group: Dict) -> Dict:
        """
        Parse a single table group through VLM to get structured JSON.
        Stitches multi-page table images before sending to VLM.
        
        Args:
            group: Table group dict from extract_table_groups_only()
            
        Returns:
            Dict with table_id, pages, and parsed data
        """
        self._load_model()

        # Stitch images if multi-page
        if len(group["images"]) > 1:
            stitched_img = stitch_images(group["images"])
        else:
            # Create a copy so we don't mutate the original image
            stitched_img = group["images"][0].copy()
            
        # Resize to prevent VRAM OOM on very tall/large tables
        stitched_img.thumbnail((1280, 1280))

        prompt_text = (
            "Extract the structured data from this table into a perfectly formatted "
            "JSON array of objects. Use the header row for keys. Only output valid JSON "
            "without any markdown formatting."
        )
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": stitched_img},
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
            return_tensors="pt"
        ).to(self.model.device)

        with torch.no_grad():
            generated_ids = self.model.generate(**inputs, max_new_tokens=8192)

        generated_ids_trimmed = [
            out_ids[len(in_ids):]
            for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        output_text = self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True,
            clean_up_tokenization_spaces=False
        )[0]

        # Clean JSON formatting
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
            print(f"[HybridExtractor] Warning: Failed to parse JSON for {group['id']}: {e}")
            table_json = {"raw_text_fallback": clean_text}

        result = {
            "table_id": group["id"],
            "pages": group["pages"],
            "data": table_json
        }

        # Cleanup
        del inputs
        del generated_ids
        torch.cuda.empty_cache()

        return result

    def render_cleaned_pages(self, pdf_path: str, table_groups: List[Dict],
                             image_regions: Optional[Dict[int, List[Tuple]]] = None,
                             zoom: float = 1.0) -> List[Dict]:
        """
        Render PDF pages as images with table and image regions replaced by
        placeholder text overlays. This produces the "cleaned" pages for VLM
        Route 2.
        
        Args:
            pdf_path: Path to the PDF file
            table_groups: Table groups from extract_table_groups_only()
            image_regions: Dict mapping page_num -> list of (x0, y0, x1, y1) bboxes
                          for images. If None, images are auto-detected via PyMuPDF.
            zoom: Zoom factor for page rendering (1.0 = 72 DPI)
            
        Returns:
            List of dicts with:
            - page_num: 0-indexed page number
            - image: PIL Image of the cleaned page
            - placeholders: list of placeholder strings on this page
        """
        print(f"[HybridExtractor] Rendering cleaned pages with placeholders...")

        # Build a lookup: page_num -> list of (bbox, placeholder_text) for tables
        table_placeholder_map: Dict[int, List[Tuple]] = {}
        global_table_idx = 0
        for group in table_groups:
            global_table_idx += 1
            placeholder_text = f"[TABLE_PLACEHOLDER_{global_table_idx}]"
            for page_num, x0, top, x1, bottom in group["bboxes"]:
                if page_num not in table_placeholder_map:
                    table_placeholder_map[page_num] = []
                table_placeholder_map[page_num].append(
                    ((x0, top, x1, bottom), placeholder_text)
                )

        # Auto-detect image regions if not provided
        if image_regions is None:
            image_regions = {}
            doc_detect = fitz.open(pdf_path)
            for page_num in range(len(doc_detect)):
                page = doc_detect.load_page(page_num)
                images_on_page = page.get_images(full=True)
                page_imgs = []
                for img_info in images_on_page:
                    xref = img_info[0]
                    base_image = doc_detect.extract_image(xref)
                    w, h = base_image["width"], base_image["height"]
                    if w > 50 and h > 50:
                        # Get image position on page
                        rects = page.get_image_rects(xref)
                        for rect in rects:
                            page_imgs.append((rect.x0, rect.y0, rect.x1, rect.y1))
                if page_imgs:
                    image_regions[page_num] = page_imgs
            doc_detect.close()

        # Build image placeholder map
        image_placeholder_map: Dict[int, List[Tuple]] = {}
        global_img_idx = 0
        for page_num in sorted(image_regions.keys()):
            for bbox in image_regions[page_num]:
                global_img_idx += 1
                placeholder_text = f"[IMAGE_PAGE_{page_num}_FIG_{global_img_idx}]"
                if page_num not in image_placeholder_map:
                    image_placeholder_map[page_num] = []
                image_placeholder_map[page_num].append(
                    (bbox, placeholder_text)
                )

        # Render pages and overlay placeholders
        doc = fitz.open(pdf_path)
        mat = fitz.Matrix(zoom, zoom)
        cleaned_pages = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            draw = ImageDraw.Draw(img)
            placeholders_on_page = []

            # White out and label table regions
            for bbox, placeholder_text in table_placeholder_map.get(page_num, []):
                x0, top, x1, bottom = bbox
                # Scale coordinates by zoom factor
                sx0, sy0 = int(x0 * zoom), int(top * zoom)
                sx1, sy1 = int(x1 * zoom), int(bottom * zoom)
                # White out the region
                draw.rectangle([sx0, sy0, sx1, sy1], fill=(255, 255, 255))
                # Draw placeholder text centered in the region
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
                except (IOError, OSError):
                    font = ImageFont.load_default()
                text_bbox = draw.textbbox((0, 0), placeholder_text, font=font)
                tw = text_bbox[2] - text_bbox[0]
                th = text_bbox[3] - text_bbox[1]
                tx = sx0 + (sx1 - sx0 - tw) // 2
                ty = sy0 + (sy1 - sy0 - th) // 2
                draw.text((tx, ty), placeholder_text, fill=(100, 100, 100), font=font)
                placeholders_on_page.append(placeholder_text)

            # White out and label image regions
            for bbox, placeholder_text in image_placeholder_map.get(page_num, []):
                x0, y0, x1, y1 = bbox
                sx0, sy0 = int(x0 * zoom), int(y0 * zoom)
                sx1, sy1 = int(x1 * zoom), int(y1 * zoom)
                draw.rectangle([sx0, sy0, sx1, sy1], fill=(240, 240, 240))
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
                except (IOError, OSError):
                    font = ImageFont.load_default()
                text_bbox = draw.textbbox((0, 0), placeholder_text, font=font)
                tw = text_bbox[2] - text_bbox[0]
                th = text_bbox[3] - text_bbox[1]
                tx = sx0 + (sx1 - sx0 - tw) // 2
                ty = sy0 + (sy1 - sy0 - th) // 2
                draw.text((tx, ty), placeholder_text, fill=(100, 100, 100), font=font)
                placeholders_on_page.append(placeholder_text)

            cleaned_pages.append({
                "page_num": page_num,
                "image": img,
                "placeholders": placeholders_on_page
            })

        doc.close()
        print(f"[HybridExtractor] Rendered {len(cleaned_pages)} cleaned pages "
              f"({sum(len(p['placeholders']) for p in cleaned_pages)} placeholders total).")
        return cleaned_pages

    def extract(self, pdf_path: str, output_path: str):
        """
        Standalone extraction: detect tables, parse via VLM, save JSON.
        This is the original CLI entrypoint.
        """
        table_groups = self.extract_table_groups_only(pdf_path)

        self._load_model()
        print("[2/3] Processing stitched table images through Qwen2.5-VL...")

        final_json = []
        for idx, group in enumerate(tqdm(table_groups, desc="Extracting Tables")):
            result = self.parse_table_group(group)
            final_json.append(result)

        print("\n[3/3] Saving final polished JSON...")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(final_json, f, indent=2, ensure_ascii=False)
        print(f"      Saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Hybrid PDF Table Extractor")
    parser.add_argument("--pdf", required=True, help="Path to PDF")
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    extractor = HybridExtractor()
    extractor.extract(args.pdf, args.output)


if __name__ == "__main__":
    main()
