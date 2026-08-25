# Document Standardization Pipeline - Model Comparative Study

This report provides a comparative analysis of the various machine learning models utilized in the Document Standardization Pipeline, detailing their performance, strengths, limitations, and the strategic rationale behind selecting the current primary model.

## 1. The Models Evaluated

The repository reveals a clear evolutionary path from text-only Large Language Models (LLMs) to a Vision-Language Model (VLM). The following models have been used or tested:

### 1.1 Llama-3.1 (`llama3.1:latest`)
* **Role:** Initial primary LLM used during Phase 2 testing for schema inference and data extraction.
* **Architecture:** Text-only LLM run locally via Ollama.
* **Workflow:** Relied on a legacy workflow where PDFs were first extracted and normalized into plain Markdown before being passed to the model.

### 1.2 Qwen-2.5 7B (`qwen2.5:7b`)
* **Role:** The current fallback text LLM configured in the `.env` settings.
* **Architecture:** Text-only LLM run locally via Ollama.
* **Workflow:** Serves as the fallback text processing path if the vision pipeline is disabled (`--no-vision`).

### 1.3 Qwen 3.6 VL (`Qwen/Qwen3.6-VL`)
* **Role:** The **primary Vision-Language Model** driving the multimodal pipeline architecture.
* **Architecture:** Vision-Language Model (VLM) run in 4-bit NF4 precision (~4.8GB VRAM) or 8-bit precision via HuggingFace Transformers / vLLM / Ollama.
* **Workflow:** Processes rendered images of document pages directly, parsing tables, reading structural hierarchies, reading diagram placeholders, and understanding layout natively.

---

## 2. Performance & Capability Comparison

| Feature/Metric | Llama-3.1 (Text-Only) | Qwen-2.5-VL (Vision-First) |
| :--- | :--- | :--- |
| **Input Modality** | Plain text / Markdown | Rendered Page Images |
| **Data Output Depth** | ~1.2 KB JSON (shallow) | ~8-12 KB JSON (deep/comprehensive) |
| **Spatial Awareness** | None (relies on text parsers) | High (understands native document layout) |
| **Format Compliance** | Prone to returning plain text instead of JSON | Strict adherence to complex JSON schemas |
| **Table Handling** | Frequently mangled multi-page tables | Highly accurate (via visual stitching & parsing) |
| **Hardware Requirement** | Low (CPU/Low VRAM via Ollama) | High (~9-10GB VRAM required) |
| **Error Handling** | Required heavy retry logic (~20% retry rate) | Single-pass structural extraction |

---

## 3. Which Was the Best?

**Qwen-2.5-VL-7B-Instruct** is unequivocally the best model for this specific application. 

While the text-only models (`llama3.1` and `qwen2.5:7b`) were extremely lightweight and easy to run locally, they suffered from a fundamental flaw: **loss of spatial context**. When a complex PDF (like a security audit report) is stripped down to plain Markdown, the hierarchical structure, complex multi-page tables, and nested elements are often flattened or corrupted. 

As noted in the `AUDIT_EXTRACTION_IMPROVEMENTS.md` testing logs, the Llama-3.1 approach yielded an "extremely shallow" 1.2KB JSON file that mostly contained definitions and failed to extract actual technical vulnerabilities. Conversely, the Qwen-2.5-VL model natively understood the layout, recovering 100% of the vulnerability findings and resulting in a **10x larger, data-rich JSON output**.

---

## 4. Why Qwen-2.5-VL is the Current Standard

The pipeline was completely re-architected to a "Vision-First" approach specifically to leverage Qwen-2.5-VL-7B-Instruct. Here is why it is prioritized over the others:

1. **Native Layout Comprehension:** By "looking" at the document rather than just "reading" scraped text, Qwen-2.5-VL perfectly preserves the structural hierarchy of the original document.
2. **Advanced Multi-Page Table Resolution:** Traditional text LLMs fail on tables that span multiple pages. The current pipeline stitches these tables into a single image, feeds them to Qwen-2.5-VL, and seamlessly merges the accurate tabular data back into the document.
3. **Elimination of Formatting Hallucinations:** The testing reports explicitly highlight that `llama3.1` struggled to consistently output valid JSON schemas, resulting in a ~20% retry rate. The Qwen-2.5-VL model handles strict JSON schemas directly from the visual prompt without degrading into plain text.
4. **Optimized Hardware Utilization:** Even though VLMs are notoriously heavy, the repository intelligently mitigates this. A single instance of Qwen-2.5-VL is loaded once in 8-bit precision (using ~9-10GB on a 16GB GPU) and is shared across three different components: the table parser, the page extractor, and the image describer. 
5. **Efficiency Improvements:** Despite the heavy compute requirements of a VLM, offloading the cognitive load from error-prone chunking and retry loops actually resulted in the pipeline running **27% faster** while generating vastly superior data.

> [!TIP]
> **Summary:** The text models (`llama` and `qwen` fallback) proved too fragile for complex audit documents. The current model (`Qwen-2.5-VL`) was chosen because it trades higher VRAM requirements for absolute structural accuracy, achieving a 10x improvement in data extraction quality by treating documents visually.
