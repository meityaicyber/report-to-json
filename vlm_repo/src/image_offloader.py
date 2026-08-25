"""
image_offloader.py
==================
Stage 1 of Decoupled Pipeline:
Extracts embedded images, figures, and diagrams from documents (PDF / DOCX),
saves them to deep storage on disk, and generates deterministic placeholder
tokens for document flow integration.
"""

import io
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from PIL import Image

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import docx
    import zipfile
except ImportError:
    docx = None


class ImageOffloader:
    """Extracts images from documents and saves them to disk storage."""

    def __init__(self, min_width: int = 50, min_height: int = 50):
        self.min_width = min_width
        self.min_height = min_height

    def extract_from_pdf(self, pdf_path: str, storage_dir: str) -> Dict[int, List[Dict[str, Any]]]:
        """
        Extract embedded images from a PDF file.

        Parameters
        ----------
        pdf_path : str
            Path to input PDF document.
        storage_dir : str
            Directory where extracted images will be persisted.

        Returns
        -------
        Dict[int, List[Dict[str, Any]]]
            Mapping of page_index -> list of image metadata dicts:
            {
                0: [
                    {
                        "fig_idx": 1,
                        "placeholder": "[IMAGE_PAGE_0_FIG_1]",
                        "filename": "page_0_fig_1.png",
                        "path": "/abs/path/to/page_0_fig_1.png",
                        "width": 800,
                        "height": 600,
                        "format": "png"
                    }
                ]
            }
        """
        if fitz is None:
            raise ImportError("PyMuPDF (fitz) is required for PDF image extraction. Run `pip install pymupdf`.")

        storage_path = Path(storage_dir)
        storage_path.mkdir(parents=True, exist_ok=True)

        extracted_map: Dict[int, List[Dict[str, Any]]] = {}
        total_images = 0

        doc = fitz.open(pdf_path)
        try:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                images_on_page = page.get_images(full=True)
                page_entries: List[Dict[str, Any]] = []
                fig_counter = 1

                for img_info in images_on_page:
                    xref = img_info[0]
                    base_image = doc.extract_image(xref)
                    if not base_image:
                        continue

                    width = base_image.get("width", 0)
                    height = base_image.get("height", 0)
                    img_bytes = base_image.get("image")
                    ext = base_image.get("ext", "png")

                    # Filter out tiny decorative icons/spacers
                    if width < self.min_width or height < self.min_height:
                        continue

                    page_display_num = page_num + 1
                    filename = f"page_{page_display_num}_fig_{fig_counter}.{ext}"
                    dest_file = storage_path / filename

                    try:
                        with open(dest_file, "wb") as f:
                            f.write(img_bytes)

                        placeholder = f"[IMAGE_PAGE_{page_display_num}_FIG_{fig_counter}]"
                        page_entries.append({
                            "fig_idx": fig_counter,
                            "page_num": page_display_num,
                            "placeholder": placeholder,
                            "filename": filename,
                            "path": str(dest_file.resolve()),
                            "width": width,
                            "height": height,
                            "format": ext
                        })
                        fig_counter += 1
                        total_images += 1
                    except Exception as err:
                        print(f"[Stage 1 - ImageOffloader] Error saving image {filename}: {err}")

                if page_entries:
                    extracted_map[page_num] = page_entries
        finally:
            doc.close()

        print(f"[Stage 1] Offloaded {total_images} images from {len(extracted_map)} pages into: {storage_path}")
        return extracted_map

    def extract_from_docx(self, docx_path: str, storage_dir: str) -> List[Dict[str, Any]]:
        """
        Extract embedded images from a DOCX (OOXML) file.
        """
        storage_path = Path(storage_dir)
        storage_path.mkdir(parents=True, exist_ok=True)

        extracted_entries: List[Dict[str, Any]] = []
        fig_counter = 1

        try:
            with zipfile.ZipFile(docx_path, 'r') as z:
                media_files = [n for n in z.namelist() if n.startswith('word/media/')]
                for media_name in media_files:
                    data = z.read(media_name)
                    try:
                        img = Image.open(io.BytesIO(data))
                        w, h = img.size
                        if w < self.min_width or h < self.min_height:
                            continue
                        
                        ext = os.path.splitext(media_name)[1].lstrip('.').lower() or "png"
                        filename = f"docx_fig_{fig_counter}.{ext}"
                        dest_file = storage_path / filename

                        with open(dest_file, "wb") as f:
                            f.write(data)

                        placeholder = f"[IMAGE_DOCX_FIG_{fig_counter}]"
                        extracted_entries.append({
                            "fig_idx": fig_counter,
                            "placeholder": placeholder,
                            "filename": filename,
                            "path": str(dest_file.resolve()),
                            "width": w,
                            "height": h,
                            "format": ext
                        })
                        fig_counter += 1
                    except Exception:
                        continue
        except Exception as err:
            print(f"[Stage 1 - ImageOffloader] Error extracting docx images: {err}")

        print(f"[Stage 1] Offloaded {len(extracted_entries)} images from DOCX into: {storage_path}")
        return extracted_entries
