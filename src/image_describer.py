"""
Image extraction and description module.

Extracts significant embedded images from PDFs (skipping tiny logos/icons),
then runs batched VLM inference to generate text descriptions.

In the first-pass pipeline flow:
- Images are extracted and saved to disk (deep storage)
- Placeholder strings [IMAGE_PAGE_X_FIG_Y] are placed in the cleaned pages
- Image descriptions are NOT substituted during Pass 1 (kept for later)

This module can also be used standalone to generate descriptions for
substitution into the final JSON (used in the legacy VLM path).
"""

import fitz
import torch
from PIL import Image
from typing import Dict, List, Tuple, Optional
from tqdm import tqdm
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
import io
import os
from pathlib import Path


class ImageDescriber:
    def __init__(self, model_id: str = "Qwen/Qwen2.5-VL-7B-Instruct",
                 model=None, processor=None):
        """
        Initialize ImageDescriber.
        
        Args:
            model_id: HuggingFace model ID for VLM
            model: Pre-loaded model instance (for sharing across extractors)
            processor: Pre-loaded processor instance (for sharing across extractors)
        """
        self.model_id = model_id
        self.model = model
        self.processor = processor

    def _load_model(self):
        """Lazy load the model in 8-bit precision (fits in 16GB VRAM)."""
        if self.model is None:
            print(f"[ImageDescriber] Loading {self.model_id} in 8-bit precision...")
            from transformers import BitsAndBytesConfig
            quant_config = BitsAndBytesConfig(load_in_8bit=True)
            self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                self.model_id,
                torch_dtype=torch.float16,
                device_map="auto",
                quantization_config=quant_config
            )
            self.processor = AutoProcessor.from_pretrained(self.model_id)

    def extract_images_from_pdf(self, pdf_path: str) -> Dict[int, List[Image.Image]]:
        """Extracts significant embedded images from the PDF, grouped by page number."""
        print(f"[ImageDescriber] Extracting images from {pdf_path}...")
        doc = fitz.open(pdf_path)
        page_images = {}
        total_images = 0

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            images_on_page = page.get_images(full=True)
            valid_images = []

            for img_idx, img_info in enumerate(images_on_page):
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]

                # Check dimensions to skip tiny logos/icons
                width = base_image["width"]
                height = base_image["height"]
                if width > 50 and height > 50:
                    try:
                        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
                        valid_images.append(pil_img)
                        total_images += 1
                    except Exception:
                        pass

            if valid_images:
                page_images[page_num] = valid_images

        doc.close()
        print(f"[ImageDescriber] Found {total_images} significant images across {len(page_images)} pages.")
        return page_images

    def extract_image_regions(self, pdf_path: str) -> Dict[int, List[Tuple[float, float, float, float]]]:
        """
        Extract bounding box regions of significant images on each page.
        Used by the pipeline to know where to place image placeholders.
        
        Returns:
            Dict mapping page_num -> list of (x0, y0, x1, y1) bounding boxes
        """
        doc = fitz.open(pdf_path)
        image_regions = {}

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            images_on_page = page.get_images(full=True)
            page_rects = []

            for img_info in images_on_page:
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                w, h = base_image["width"], base_image["height"]
                if w > 50 and h > 50:
                    rects = page.get_image_rects(xref)
                    for rect in rects:
                        page_rects.append((rect.x0, rect.y0, rect.x1, rect.y1))

            if page_rects:
                image_regions[page_num] = page_rects

        doc.close()
        return image_regions

    def save_images_to_disk(self, pdf_path: str, output_dir: str) -> Dict[int, List[str]]:
        """
        Extract images from PDF and save them to disk (deep storage).
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save extracted images
            
        Returns:
            Dict mapping page_num -> list of saved file paths
        """
        os.makedirs(output_dir, exist_ok=True)
        page_images = self.extract_images_from_pdf(pdf_path)
        saved_paths = {}

        for page_num, images in page_images.items():
            saved_paths[page_num] = []
            for img_idx, img in enumerate(images):
                filename = f"page_{page_num}_fig_{img_idx + 1}.png"
                filepath = os.path.join(output_dir, filename)
                img.save(filepath, "PNG")
                saved_paths[page_num].append(filepath)

        total_saved = sum(len(v) for v in saved_paths.values())
        print(f"[ImageDescriber] Saved {total_saved} images to {output_dir}")
        return saved_paths

    def generate_descriptions(self, pdf_path: str, batch_size: int = 4) -> Dict[int, List[str]]:
        """Extracts images and runs batched VLM inference to generate descriptions."""
        page_images = self.extract_images_from_pdf(pdf_path)
        if not page_images:
            return {}

        self._load_model()

        # Flatten for batching
        flat_images = []
        mapping_info = []  # To map back to (page_num, list_idx)

        for page_num, images in page_images.items():
            for idx, img in enumerate(images):
                flat_images.append(img)
                mapping_info.append((page_num, idx))

        descriptions = []
        prompt_text = ("Describe this image in detail. Extract any relevant text, "
                       "data points, workflows, or key insights. Output only the description.")

        print(f"[ImageDescriber] Generating descriptions for {len(flat_images)} images...")
        for i in tqdm(range(0, len(flat_images), batch_size), desc="Describing Images"):
            batch_imgs = flat_images[i:i + batch_size]
            messages_batch = [
                [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image", "image": img},
                            {"type": "text", "text": prompt_text},
                        ],
                    }
                ]
                for img in batch_imgs
            ]

            texts = [
                self.processor.apply_chat_template(msg, tokenize=False, add_generation_prompt=True)
                for msg in messages_batch
            ]

            # process_vision_info for a batch
            image_inputs, video_inputs = process_vision_info(messages_batch)

            inputs = self.processor(
                text=texts,
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt",
            ).to(self.model.device)

            with torch.no_grad():
                generated_ids = self.model.generate(**inputs, max_new_tokens=1024)

            generated_ids_trimmed = [
                out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]

            batch_outputs = self.processor.batch_decode(
                generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )
            descriptions.extend([out.strip() for out in batch_outputs])

            torch.cuda.empty_cache()

        # Reconstruct mapping
        final_descriptions = {}
        for (page_num, idx), desc in zip(mapping_info, descriptions):
            if page_num not in final_descriptions:
                final_descriptions[page_num] = []
            final_descriptions[page_num].append(desc)

        return final_descriptions
