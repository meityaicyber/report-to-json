The Document Standardization Pipeline is an automated system designed to convert complex, unstructured documents—specifically PDFs and Word documents—into cleanly structured, machine-readable JSON.

At its core, the pipeline acts as an intelligent reader. It examines a document, understands its layout and contents, and organizes that information into a strict taxonomy, ensuring that the final output is highly consistent and predictable.

The pipeline uses a Vision-First approach with a two-pass architecture. The first pass, described here, focuses on ensuring that ALL information from the source document is captured in the JSON output with correct hierarchical structure.

## First Pass — Parallel Route Architecture

The first pass operates through two parallel routes that converge in a merge step.

### Route 1: Table & Image Pre-Extraction

Before the main VLM reads the document, the pipeline sweeps through the PDF and pre-extracts two categories of content that are problematic for Vision-Language Models:

**Tables:** Tables that span multiple pages are frequently misread by VLMs because each page is processed independently. The pipeline uses pdfplumber to geometrically detect table bounding boxes on every page. When a table on page N+1 has the same column count as the last table on page N, the pipeline recognizes this as a continuation and stitches the cropped table images vertically into a single tall image. Each stitched table is then sent to the VLM for structured JSON extraction, producing accurate tabular data regardless of how many pages it spans.

**Images:** Embedded images, diagrams, and charts are computationally expensive for VLMs and disrupt text comprehension. The pipeline extracts these images and saves them to deep storage on disk. Their positions are recorded but their content is not analyzed during the first pass.

After extraction, the pipeline renders "cleaned" page images. In these cleaned images, every table region and image region has been whited out and replaced with a visible placeholder label — for example, `[TABLE_PLACEHOLDER_1]` or `[IMAGE_PAGE_3_FIG_2]`. These placeholders are clearly legible in the rendered image so the main VLM can see and preserve them.

### Route 2: VLM Page Extraction

The cleaned page images are fed one-by-one into the Vision-Language Model (Qwen2.5-VL-7B-Instruct). The VLM reads the visual layout of each page — headings, paragraphs, lists, structure — and produces a hierarchical JSON representation. When it encounters a placeholder string, it outputs that string verbatim into the JSON, marking exactly where the table or image belongs in the document structure.

### Merge Step

After both routes complete, the pipeline walks the VLM's JSON output and finds every `[TABLE_PLACEHOLDER_N]` string. Each is replaced with the corresponding structured table JSON that was parsed during Route 1. Image placeholders remain as-is for now — they point to the files saved in deep storage and can be resolved in a future pass.

The end result is a single, complete JSON file that preserves all textual content, all tabular data (even multi-page tables), and the structural hierarchy of the original document.

## Shared Model Architecture

A single instance of the Qwen2.5-VL-7B-Instruct model is loaded once in 8-bit precision and shared across all three VLM-dependent components (table parser, page extractor, and image describer). This keeps VRAM usage to approximately 9-10GB on a 16GB GPU, with room for KV cache during inference. The GPU work is serialized — Route 1 table parsing runs first, then Route 2 page extraction — but the logical architecture remains parallel in design.
