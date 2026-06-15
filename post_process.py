import json
from pathlib import Path

def normalize(data):
    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            norm_v = normalize(v)
            
            # Flatten 1-element lists
            if isinstance(norm_v, list) and len(norm_v) == 1:
                v0 = norm_v[0]
                if isinstance(v0, dict) and len(v0) == 1:
                    nested_k = list(v0.keys())[0]
                    nested_v = list(v0.values())[0]
                    new_dict[k] = nested_k
                    if isinstance(nested_v, dict) and nested_v:
                        for nk, nv in nested_v.items():
                            new_dict[nk] = nv
                elif isinstance(v0, str):
                    new_dict[k] = v0
                else:
                    new_dict[k] = norm_v
            
            # Flatten hallucinated dicts {"Value": {}} or {"Value": {nested...}}
            elif isinstance(norm_v, dict) and len(norm_v) == 1:
                nested_k = list(norm_v.keys())[0]
                nested_v = list(norm_v.values())[0]
                if nested_v == {}:
                    new_dict[k] = nested_k
                elif isinstance(nested_v, dict):
                    new_dict[k] = nested_k
                    for nk, nv in nested_v.items():
                        new_dict[nk] = nv
                else:
                    new_dict[k] = norm_v
            else:
                new_dict[k] = norm_v
        return new_dict

    elif isinstance(data, list):
        new_list = []
        for item in data:
            norm_item = normalize(item)
            if isinstance(norm_item, dict) and len(norm_item) == 1 and list(norm_item.values())[0] == {}:
                new_list.append(list(norm_item.keys())[0])
            else:
                new_list.append(norm_item)
        return new_list

    else:
        return data

input_file = Path('batch_output/Best - FINAL_Optimized.json')
output_file = Path('batch_output/Best - FINAL_Optimized_Clean.json')

with open(input_file, 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

clean_data = normalize(raw_data)

# Because we hoisted nested dicts, we should run it one more time to ensure deep nested flattening is complete
clean_data = normalize(clean_data)

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(clean_data, f, indent=2)

print(f"Successfully cleaned and formatted JSON!")
print(f"Saved to: {output_file}")
