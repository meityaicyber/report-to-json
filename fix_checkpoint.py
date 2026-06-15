import json

path = "batch_output/Best - FINAL_Optimized_partial.json"
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

data['_resume_batch_index'] = 87

with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

print("Injected resume batch index!")
