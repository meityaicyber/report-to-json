import json
import os
import torch
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer

def run_stage3():
    # Load the intermediate markdown
    md_path = "output_new_intermediate.md"
    if not os.path.exists(md_path):
        print(f"Error: {md_path} not found.")
        return
        
    print(f"Loading {md_path}...")
    with open(md_path, 'r', encoding='utf-8') as f:
        markdown_doc = f.read()

    schema_path = Path("schemas/base.schema.json")
    schema_text = schema_path.read_text() if schema_path.exists() else ""

    print(f"\n[Stage 3] Loading Dedicated Text LLM (Qwen/Qwen2.5-7B-Instruct)...")
    from transformers import BitsAndBytesConfig
    model_id = "Qwen/Qwen2.5-7B-Instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    quant_config = BitsAndBytesConfig(load_in_8bit=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map="auto",
        quantization_config=quant_config
    )
    
    prompt = f"""You are a strict data structuring assistant. I will provide you with a full Markdown document that may contain JSON blocks representing tables.
Your task is to extract ALL of the information from this document into a single, cohesive JSON object according to the provided schema.

TARGET SCHEMA:
{schema_text}

DOCUMENT TEXT:
{markdown_doc}

INSTRUCTIONS:
1. Extract ALL information from the document without summarization. Do NOT drop any paragraphs or omit details.
2. You MUST use the EXACT keys specified in the TARGET SCHEMA. Do not invent your own keys. For example, use "vulnerability_title", "description", "impact", "recommendation" instead of "Vulnerability" or "Severity".
3. For the detailed_observations array, you MUST populate every single required field (vulnerability_title, description, impact, recommendation).
4. Output ONLY a valid JSON object starting with {{ and ending with }}. Do NOT wrap it in markdown fences. Do NOT explain your output.
"""
    messages = [{"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text], return_tensors="pt").to(model.device)

    print(f"[Stage 3] Structuring Markdown to JSON via LLM...")
    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=8192,
            do_sample=False,
            repetition_penalty=1.05
        )
    
    generated_ids_trimmed = [
        out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    output_text = tokenizer.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0].strip()

    # Clean json formatting
    if output_text.startswith("```json"):
        output_text = output_text[7:]
    if output_text.startswith("```"):
        output_text = output_text[3:]
    if output_text.endswith("```"):
        output_text = output_text[:-3]
    output_text = output_text.strip()

    extracted_data = {}
    try:
        extracted_data = json.loads(output_text)
    except Exception as e:
        print("JSON Decode Error:", str(e))
        extracted_data = {"error": "Failed to parse JSON", "raw_output": output_text}

    # Prepare metadata
    if '_meta' not in extracted_data:
        extracted_data['_meta'] = {}
    extracted_data['_meta'].update({
        'pipeline_version': '3.0.0',
        'source_file': '1-Audit Report.pdf',
        'extraction_mode': 'decoupled_text_llm',
        'llm_model': model_id
    })
    
    # Save output
    out_path = "output_new.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, indent=2)
    print(f"    ✓ Saved JSON: {out_path}")
    
if __name__ == "__main__":
    run_stage3()
