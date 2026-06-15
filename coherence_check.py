import json

path = r'batch_output\Best - FINAL_Optimized_Clean.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

vulns = []

def extract_vulns(obj):
    if isinstance(obj, dict):
        keys_lower = [k.lower() for k in obj.keys()]
        if any('cve' in k for k in keys_lower) and any('severity' in k for k in keys_lower):
            vulns.append(obj)
        else:
            for v in obj.values():
                extract_vulns(v)
    elif isinstance(obj, list):
        for item in obj:
            extract_vulns(item)

extract_vulns(data)

coherence_stats = {
    'perfectly_coherent_all_fields': 0,
    'highly_coherent_missing_1_field': 0,
    'fragmented_missing_multiple': 0,
    'contains_nested_hallucinations': 0
}

for v in vulns:
    keys_lower = [k.lower() for k in v.keys()]
    
    found_fields = 0
    if any('title' in k for k in keys_lower): found_fields += 1
    if any('severity' in k for k in keys_lower): found_fields += 1
    if any('cve' in k for k in keys_lower): found_fields += 1
    if any('observation' in k and 'detailed' in k for k in keys_lower): found_fields += 1
    if any('recommendation' in k for k in keys_lower): found_fields += 1
    
    if found_fields == 5:
        coherence_stats['perfectly_coherent_all_fields'] += 1
    elif found_fields == 4:
        coherence_stats['highly_coherent_missing_1_field'] += 1
    else:
        coherence_stats['fragmented_missing_multiple'] += 1
        
    has_hallucination = False
    for val in v.values():
        if isinstance(val, dict):
            has_hallucination = True
            break
        elif isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
            has_hallucination = True
            break
            
    if has_hallucination:
        coherence_stats['contains_nested_hallucinations'] += 1

print(f'Total Vulns Evaluated: {len(vulns)}')
print(f'Perfectly Coherent (All 5 Core Fields): {coherence_stats["perfectly_coherent_all_fields"]}')
print(f'Highly Coherent (Missing 1 Field): {coherence_stats["highly_coherent_missing_1_field"]}')
print(f'Fragmented (Missing 2+ Fields): {coherence_stats["fragmented_missing_multiple"]}')
print(f'Contains Nested Hallucinations (Bad Structure): {coherence_stats["contains_nested_hallucinations"]}')
