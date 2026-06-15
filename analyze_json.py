import json

path = r'batch_output\Best - FINAL_Optimized.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Recursively count vulnerabilities
def count_vulns(obj, counter):
    if isinstance(obj, dict):
        # Often the VLM extracts "Observation/ Vulnerability Title" or "CVE/CWE"
        keys_lower = [k.lower().strip() for k in obj.keys()]
        if any('vulnerability title' in k or 'cve' in k for k in keys_lower):
            counter[0] += 1
        for k, v in obj.items():
            count_vulns(v, counter)
    elif isinstance(obj, list):
        for item in obj:
            count_vulns(item, counter)

vuln_count = [0]
count_vulns(data, vuln_count)

print(f"Total structured vulnerabilities found: {vuln_count[0]}")
