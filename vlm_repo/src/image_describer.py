import fitz
import torch
from PIL import Image
from typing import Dict, List
from tqdm import tqdm
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
import io

import os

DEFAULT_VLM_MODEL = os.environ.get("VLM_MODEL", "Qwen/Qwen3.6-VL")

class ImageDescriber:
    def __init__(self, model_id: str = DEFAULT_VLM_MODEL, load_in_4bit: bool = True):
        self.model_id = model_id
        self.load_in_4bit = load_in_4bit
        self.model = None
        self.processor = None

    def _load_model(self):
        if self.model is None:
            print(f"[ImageDescriber] Loading {self.model_id} (4-bit NF4 quantized for 8GB VRAM)...")
            from transformers import AutoModelForVision2Seq, BitsAndBytesConfig
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
            print("[ImageDescriber] Model loaded successfully.")

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

    def generate_descriptions(self, pdf_path: str, batch_size: int = 16) -> Dict[int, List[str]]:
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
        prompt_text = "Describe this image in detail. Extract any relevant text, data points, workflows, or key insights. Output only the description."

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
                generated_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=2048,
                    do_sample=False,
                    temperature=0,
                    repetition_penalty=1.05,
                )
                
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
