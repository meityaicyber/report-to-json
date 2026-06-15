import json

path = 'batch_output/Best - FINAL_Optimized_Clean.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

vuln_objects = []

def find_vulns(obj):
    if isinstance(obj, dict):
        keys_lower = [k.lower().strip() for k in obj.keys()]
        # A vulnerability is an object that contains AT LEAST 'severity' and 'cve'
        if any('severity' in k for k in keys_lower) and any('cve' in k for k in keys_lower):
            vuln_objects.append(obj)
        else:
            for v in obj.values():
                find_vulns(v)
    elif isinstance(obj, list):
        for item in obj:
            find_vulns(item)

find_vulns(data)

print(f"Total Vulnerabilities Found: {len(vuln_objects)}")

missing_fields = {
    "S No.": 0,
    "Severity": 0,
    "CVE/CWE": 0,
    "Affected Asset": 0,
    "Vulnerable Parameter": 0,
    "Observation/ Vulnerability title": 0,
    "Detailed observation": 0,
    "Recommendation": 0,
    "Reference": 0,
    "References to evidences / Proof of Concept": 0
}

for v in vuln_objects:
    for field in missing_fields.keys():
        found = False
        for k in v.keys():
            if field.split()[0].lower() in k.lower() or field.replace(" ", "").lower() in k.replace(" ", "").lower():
                found = True
                break
        if not found:
            missing_fields[field] += 1

print("\nMissing Fields Count:")
for k, v in missing_fields.items():
    print(f"  {k}: {v} missing ({round((v/len(vuln_objects))*100, 1)}%)")
