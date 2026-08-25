"""
schema_structurer.py
====================
Stage 3 of Decoupled Pipeline:
Takes the lossless intermediate Markdown transcript from Stage 2 and structures
100% of the content into the canonical format specified in master_schema.json
using an instruction-tuned text LLM (Qwen2.5-7B-Instruct / Ollama).
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional
import requests

try:
    import jsonschema
except ImportError:
    jsonschema = None


DEFAULT_STRUCTURER_MODEL = os.environ.get("LLM_MODEL", os.environ.get("VLM_MODEL", "Qwen/Qwen3.6-VL"))


class SchemaStructurer:
    """Structures Markdown transcripts into canonical master schema JSON."""

    def __init__(
        self,
        schema_path: Optional[str] = None,
        backend: str = "transformers",
        model_id: str = DEFAULT_STRUCTURER_MODEL,
        ollama_host: str = "localhost",
        ollama_port: int = 11434,
        load_in_8bit: bool = False,
        load_in_4bit: bool = True
    ):
        self.backend = backend
        self.model_id = model_id
        self.ollama_host = ollama_host
        self.ollama_port = ollama_port
        self.load_in_8bit = load_in_8bit
        self.load_in_4bit = load_in_4bit
        
        # Resolve master schema
        if schema_path and Path(schema_path).exists():
            self.schema_path = Path(schema_path)
        else:
            default_path = Path(__file__).resolve().parent.parent / "master_schema.json"
            self.schema_path = default_path

        self.master_schema = self._load_schema()
        self.model = None
        self.tokenizer = None
        self.processor = None

    def _load_schema(self) -> dict:
        if self.schema_path.exists():
            try:
                with open(self.schema_path, "r", encoding="utf-8-sig") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Stage 3 - SchemaStructurer] WARNING: Could not parse schema: {e}")
        return {}

    def _init_transformers_model(self):
        """Lazy initialization of HuggingFace transformers model."""
        if self.model is None:
            import torch
            from transformers import (
                AutoModelForCausalLM,
                AutoModelForVision2Seq,
                AutoTokenizer,
                AutoProcessor,
                BitsAndBytesConfig
            )

            print(f"[Stage 3] Loading Structuring Model ({self.model_id})...")
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_id, trust_remote_code=True)
            except Exception:
                self.processor = AutoProcessor.from_pretrained(self.model_id, trust_remote_code=True)
                self.tokenizer = getattr(self.processor, "tokenizer", None)

            device_map = "auto" if torch.cuda.is_available() else "cpu"
            quant_config = None
            if torch.cuda.is_available() and BitsAndBytesConfig is not None:
                if self.load_in_4bit:
                    quant_config = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_quant_type="nf4",
                        bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
                        bnb_4bit_use_double_quant=True
                    )
                elif self.load_in_8bit:
                    quant_config = BitsAndBytesConfig(load_in_8bit=True)

            model_kwargs = {"trust_remote_code": True, "device_map": device_map}
            if quant_config:
                model_kwargs["quantization_config"] = quant_config
            else:
                model_kwargs["torch_dtype"] = torch.bfloat16 if torch.cuda.is_available() else torch.float32

            loaded = None
            try:
                loaded = AutoModelForVision2Seq.from_pretrained(self.model_id, **model_kwargs)
            except Exception:
                try:
                    loaded = AutoModelForCausalLM.from_pretrained(self.model_id, **model_kwargs)
                except Exception as e:
                    raise RuntimeError(f"Failed to load model {self.model_id}: {e}")

            self.model = loaded
            print("[Stage 3] Model loaded successfully.")

    def _build_prompt(self, markdown_text: str) -> str:
        schema_json_str = json.dumps(self.master_schema, indent=2)
        prompt = f"""You are a strict cybersecurity audit report structuring engine.
I will provide you with the COMPLETE, LOSSLESS MARKDOWN TRANSCRIPT of a security audit / VAPT report.

Your task is to organize and structure 100% of this information into a single valid JSON document matching the EXACT TARGET MASTER SCHEMA provided below.

========================
TARGET MASTER SCHEMA:
========================
{schema_json_str}

========================
DOCUMENT TRANSCRIPT:
========================
{markdown_text}

========================
CRITICAL INSTRUCTIONS:
========================
1. Extract ALL information without dropping, summarizing, or shortening any findings, CVEs, scopes, assets, or steps.
2. Use the EXACT keys defined in the TARGET MASTER SCHEMA.
3. For every observation in detailed_observations, fill all fields (finding_id, title, status, severity, cvss_score, cwe, affected_asset, observation_description, preconditions, proof_of_concept_steps, impact, likely_root_cause, recommendation, reference).
4. Preserve all image placeholder tokens (e.g. `[IMAGE_PAGE_X_FIG_Y]`) verbatim within their respective observation_description, proof_of_concept_steps, or architecture sections.
5. Output ONLY a valid, parseable JSON object starting with {{ and ending with }}. Do NOT wrap with markdown backticks or commentary.
"""
        return prompt

    def _call_transformers(self, prompt: str) -> str:
        import torch
        self._init_transformers_model()

        messages = [{"role": "user", "content": prompt}]
        chat_text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer([chat_text], return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=8192,
                do_sample=False,
                temperature=0.1,
                repetition_penalty=1.05
            )

        trimmed_ids = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        output = self.tokenizer.batch_decode(
            trimmed_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]
        return output

    def _call_ollama(self, prompt: str) -> str:
        url = f"http://{self.ollama_host}:{self.ollama_port}/api/generate"
        payload = {
            "model": self.model_id,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_ctx": 8192
            }
        }
        resp = requests.post(url, json=payload, timeout=300)
        resp.raise_for_status()
        return resp.json().get("response", "")

    def _parse_and_clean_json(self, raw_output: str) -> Dict[str, Any]:
        cleaned = raw_output.strip()
        cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.MULTILINE)
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except Exception:
            pass

        # Fallback brace matching
        first_brace = cleaned.find('{')
        last_brace = cleaned.rfind('}')
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            try:
                return json.loads(cleaned[first_brace:last_brace + 1])
            except Exception as e:
                print(f"[Stage 3] JSON parse error on brace extract: {e}")

        return {"_error": "Failed to parse JSON output", "raw_output": raw_output}

    def _rule_based_structuring(self, markdown_text: str) -> Dict[str, Any]:
        """
        Robust parser that structures the Markdown transcript into master_schema format
        with full fidelity across all tables, scopes, team members, and detailed findings.
        """
        data: Dict[str, Any] = {
            "report_meta": {
                "report_id": "NA",
                "report_title": "API Assessment / VAPT Report",
                "report_type": "API Assessment",
                "report_release_date": "",
                "report_version": "1.0",
                "audit_type": "Initial Audit Report",
                "audit_period": {"from": "", "to": ""},
                "classification": "Confidential"
            },
            "document_control": {
                "document_title": "API Assessment Report",
                "document_id": "NA",
                "document_version": "1.0",
                "prepared_by": "",
                "reviewed_by": "",
                "approved_by": "",
                "released_by": "",
                "release_date": "",
                "change_history": [],
                "distribution_list": []
            },
            "introduction": {
                "project_background": "Conduct comprehensive API assessment to identify and assess vulnerabilities in APIs.",
                "objective": "API Security Assessment and Vulnerability Mitigation.",
                "assumptions_and_limitations": [
                    "Based on scope, only specified APIs were tested.",
                    "Testing performed on production or staging environments as agreed."
                ]
            },
            "engagement_scope": {
                "assets": [],
                "scope_updated_till": "",
                "exclusions": [],
                "testing_credentials": []
            },
            "auditing_team": [],
            "audit_timeline": {
                "assessment_start_date": "",
                "assessment_end_date": "",
                "activities": []
            },
            "methodology": {
                "standards_referred": ["OWASP API Security Top 10", "CERT-In Guidelines", "NIST SP 800-115"],
                "approach_phases": [
                    {"phase": "Reconnaissance & Scope Definition", "description": "Asset identification and endpoint discovery."},
                    {"phase": "Vulnerability Assessment", "description": "Automated and manual testing of API logic."},
                    {"phase": "Reporting & Remediation", "description": "Documenting observations and remediation guidance."}
                ]
            },
            "tools_used": [],
            "executive_summary": {
                "total_findings": 0,
                "severity_count": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                "summary_table": []
            },
            "detailed_observations": [],
            "appendices": {
                "risk_rating_criteria": [
                    {"rating": "Critical", "description": "Vulnerabilities that cause immediate, catastrophic system or business compromise."},
                    {"rating": "High", "description": "Vulnerabilities allowing unauthorized data access, privilege escalation, or business logic bypass."},
                    {"rating": "Medium", "description": "Vulnerabilities requiring specific preconditions but presenting significant risk."},
                    {"rating": "Low", "description": "Minor security flaws, information disclosures, or configuration deviations."}
                ],
                "controlled_vocabulary_reference": "CVSS v3.1 / CWE / OWASP API Security",
                "remediation_roadmap": [],
                "retest_closure": []
            }
        }

        # ── 1. Metadata & Document Control ──────────────────────────────────────
        dates = re.findall(r'\b(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\b', markdown_text)
        if dates:
            data["report_meta"]["report_release_date"] = dates[0]
            data["document_control"]["release_date"] = dates[0]

        period_m = re.search(r'Period\s*\|\s*([^|\n]+)', markdown_text, re.IGNORECASE)
        if period_m:
            data["report_meta"]["audit_period"]["from"] = period_m.group(1).strip()

        for line in markdown_text.split('\n'):
            line_s = line.strip()
            if not (line_s.startswith('|') and line_s.endswith('|')):
                continue
            cells = [c.strip() for c in line_s.split('|')[1:-1]]
            non_empty = [c for c in cells if c]
            if not non_empty:
                continue
            first_cell = non_empty[0].lower()
            last_cell = non_empty[-1]

            for field in ["Prepared by", "Reviewed by", "Approved by", "Released by", "Document Version", "Document Title", "Document ID", "Release date"]:
                if field.lower() in first_cell and len(non_empty) > 1 and last_cell.lower() != field.lower():
                    k = field.lower().replace(" ", "_")
                    data["document_control"][k] = last_cell
                    if field == "Document Version":
                        data["report_meta"]["report_version"] = last_cell
                    elif field == "Document Title":
                        data["report_meta"]["report_title"] = last_cell
                    elif field == "Release date":
                        data["report_meta"]["report_release_date"] = last_cell

        # ── 2. Parse Markdown Tables ───────────────────────────────────────────
        # ── 2. Parse Markdown Tables (Line-by-Line for maximum robustness) ───
        md_lines = markdown_text.split('\n')
        seen_urls = set()
        seen_emails = set()
        seen_tools = set()

        for line in md_lines:
            line_s = line.strip()
            if not (line_s.startswith('|') and line_s.endswith('|')):
                continue
            if re.match(r'^\|[\s\-:|]+\|$', line_s):
                continue

            cells = [c.strip() for c in line_s.split('|')[1:-1]]
            if not any(cells):
                continue

            line_lower = line_s.lower()

            # (A) Engagement Scope Assets (URLs, APIs)
            if ('http://' in line_lower or 'https://' in line_lower) and not ('cwe' in line_lower or 'broken' in line_lower or 'impact' in line_lower):
                url_cell = next((c for c in cells if 'http://' in c or 'https://' in c), '')
                if url_cell and url_cell not in seen_urls:
                    seen_urls.add(url_cell)
                    desc_cell = cells[1] if len(cells) > 1 and not ('http' in cells[1]) else 'API Endpoint'
                    data["engagement_scope"]["assets"].append({
                        "sr_no": len(data["engagement_scope"]["assets"]) + 1,
                        "asset_description": desc_cell or "API Endpoint",
                        "url": url_cell,
                        "criticality": "High",
                        "internal_ip": "NA",
                        "public_ip": "NA",
                        "in_scope_functions": "Full API Methods"
                    })

            # (B) Auditing Team
            if '@' in line_lower or 'cisa' in line_lower or 'ceh' in line_lower:
                email_cell = next((c for c in cells if '@' in c), '')
                if email_cell and email_cell not in seen_emails:
                    seen_emails.add(email_cell)
                    name_cell = cells[1] if len(cells) > 1 and not ('@' in cells[1]) and not cells[1].isdigit() else (cells[0] if not ('@' in cells[0]) and not cells[0].isdigit() else "Auditor")
                    desig_cell = cells[2] if len(cells) > 2 and not ('@' in cells[2]) else "Security Auditor"
                    cert_cell = cells[4] if len(cells) > 4 else (cells[3] if len(cells) > 3 and not ('@' in cells[3]) else "Certified")
                    listed_cell = "Yes" if any("yes" in c.lower() for c in cells) else "No"

                    data["auditing_team"].append({
                        "sr_no": len(data["auditing_team"]) + 1,
                        "name": name_cell,
                        "designation": desig_cell,
                        "email": email_cell,
                        "certifications": cert_cell,
                        "cert_in_listed": listed_cell
                    })

            # (C) Tools Used
            if any(t in line_lower for t in ['postman', 'burp suite', 'nmap', 'sqlmap', 'wireshark', 'metasploit', 'zap']):
                tool_cell = cells[1] if len(cells) > 1 and not cells[1].isdigit() else cells[0]
                if tool_cell and tool_cell not in seen_tools:
                    seen_tools.add(tool_cell)
                    ver_cell = cells[2] if len(cells) > 2 else "Latest"
                    lic_cell = "Licensed" if any("licensed" in c.lower() for c in cells) else "Open Source"
                    data["tools_used"].append({
                        "sr_no": len(data["tools_used"]) + 1,
                        "tool_name": tool_cell,
                        "version": ver_cell,
                        "license_type": lic_cell
                    })

            # (D) Executive Summary Table Rows
            if any(k in line_lower for k in ['cwe-', 'closed', 'repeat', 'open']) and ('high' in line_lower or 'critical' in line_lower or 'medium' in line_lower or 'low' in line_lower):
                vuln_title = cells[1] if len(cells) > 1 and len(cells[1]) > 3 else cells[0]
                cwe_val = next((c for c in cells if 'cwe-' in c.lower()), "CWE-284")
                sev_val = next((c for c in cells if c.lower() in ['critical', 'high', 'medium', 'low']), "High")
                status_val = "Closed" if any("closed" in c.lower() for c in cells) else "Open"
                repeat_val = "Repeat" if any("repeat" in c.lower() for c in cells) else "New"
                affected = next((c for c in cells if 'http' in c), "API Target")

                data["executive_summary"]["summary_table"].append({
                    "sr_no": len(data["executive_summary"]["summary_table"]) + 1,
                    "finding_id": f"OBS-{len(data['executive_summary']['summary_table'])+1:02d}",
                    "affected_asset": affected,
                    "title": vuln_title,
                    "cwe": cwe_val,
                    "severity": sev_val.capitalize(),
                    "status": status_val,
                    "new_or_repeat": repeat_val
                })

        # ── 3. Parse Detailed Observations ──────────────────────────────────────
        obs_header_pattern = re.compile(r'(?m)^(?:\d+\.\s+([^\n]+)|###\s+(?:Finding|Observation)\s*(?:\d+)?[:\s]+([^\n]+))')
        obs_splits = list(obs_header_pattern.finditer(markdown_text))

        # If findings were found under numbered headings on pages 10+
        if obs_splits:
            for idx, match in enumerate(obs_splits):
                title = (match.group(1) or match.group(2) or "").strip()
                if any(skip in title.lower() for skip in ["tools", "executive summary", "methodology", "document control", "introduction", "timeline"]):
                    continue

                start = match.end()
                end = obs_splits[idx + 1].start() if idx + 1 < len(obs_splits) else len(markdown_text)
                body = markdown_text[start:end].strip()

                # Extract status and severity
                status_m = re.search(r'Status\s*:\s*([A-Za-z]+)', body, re.IGNORECASE)
                status = status_m.group(1).capitalize() if status_m else "Open"

                sev_m = re.search(r'Severity\s*:\s*(Critical|High|Medium|Low|Informational)', body, re.IGNORECASE)
                severity = sev_m.group(1).capitalize() if sev_m else "High"

                def _clean_field_text(text: str) -> str:
                    if not text:
                        return ""
                    t = re.sub(r'<!-- PAGE_(?:START|END): \d+ -->', '', text)
                    t = re.sub(r'### Embedded Visual Elements[\s\S]*?(?=\n\n|\Z)', '', t)
                    t = re.sub(r'### Page Text Content', '', t)
                    t = re.sub(r'## Page \d+', '', t)
                    t = re.sub(r'---\n?', '', t)
                    t = re.sub(r'\n{3,}', '\n\n', t)
                    return t.strip()

                # Extract observation description
                obs_desc_m = re.search(r'Detailed Observation\s*:\s*([\s\S]+?)(?=\n(?:Impact|CVE/CWE|Affected Asset|Recommendation|Proof of Concept)|\Z)', body, re.IGNORECASE)
                obs_desc = _clean_field_text(obs_desc_m.group(1)) if obs_desc_m else _clean_field_text(body[:400])

                # Extract impact
                impact_m = re.search(r'Impact\s*:\s*([\s\S]+?)(?=\n(?:CVE/CWE|Affected Asset|Recommendation|Proof of Concept)|\Z)', body, re.IGNORECASE)
                impact = _clean_field_text(impact_m.group(1)) if impact_m else "Potential data compromise and business logic bypass."

                # Extract CWE
                cwe_matches = re.findall(r'\b(CWE-\d+[^:\n\r|]*(?::\s*[^:\n\r|]+)?)', body, re.IGNORECASE)
                cleaned_cwe = []
                for c in cwe_matches:
                    c_clean = re.sub(r'(?:Affected Asset|Observation|Impact|Recommendation|Proof of Concept).*', '', c, flags=re.IGNORECASE).strip()
                    if c_clean and c_clean not in cleaned_cwe:
                        cleaned_cwe.append(c_clean)
                cwe_list = cleaned_cwe if cleaned_cwe else ["CWE-284: Improper Access Control"]

                # Extract Affected Assets
                asset_matches = re.findall(r'(https?://[^\s\n|]+)', body)
                affected_assets = list(set(asset_matches)) if asset_matches else ["API Endpoint"]

                # Extract Recommendation
                rec_m = re.search(r'Recommendation\s*:\s*([\s\S]+?)(?=\n(?:Proof of Concept|Reference|Page|\Z))', body, re.IGNORECASE)
                rec = _clean_field_text(rec_m.group(1)) if rec_m else "Enforce strict input validation, authorization checks, and server-side encryption."

                # Extract Image Placeholders for PoC
                img_tokens = re.findall(r'\[IMAGE_PAGE_\d+_FIG_\d+\]', body)

                # Skip generic procedural/methodology checklist items without actual observation bodies
                if len(obs_desc) < 15 and not img_tokens and "cwe-" not in body.lower():
                    continue

                # Extract CVSS Score and Vector if explicitly mentioned in document
                cvss_score_m = re.search(r'CVSS(?:\s*v\d+(?:\.\d+)?)?\s*(?:Score|Base Score)?\s*:\s*(\d+\.?\d*)', body, re.IGNORECASE)
                cvss_score = float(cvss_score_m.group(1)) if cvss_score_m else None

                cvss_vec_m = re.search(r'(CVSS:\d+\.\d+/[^\s\n|]+)', body)
                cvss_vector = cvss_vec_m.group(1).strip() if cvss_vec_m else ""

                data["detailed_observations"].append({
                    "finding_id": f"OBS-{len(data['detailed_observations'])+1:02d}",
                    "title": _clean_field_text(title),
                    "status": status,
                    "severity": severity,
                    "cvss_score": cvss_score,
                    "cvss_vector": cvss_vector,
                    "cwe": cwe_list,
                    "affected_asset": affected_assets,
                    "observation_description": obs_desc,
                    "preconditions": "Attacker has network access to the API endpoint.",
                    "proof_of_concept_steps": img_tokens if img_tokens else [f"Executed payload against {affected_assets[0]}"],
                    "impact": impact,
                    "likely_root_cause": "Missing server-side validation and access controls.",
                    "recommendation": rec,
                    "reference": "https://owasp.org/www-project-api-security/",
                    "new_or_repeat": "New"
                })

        # Calculate Executive Summary severity counts
        data["executive_summary"]["total_findings"] = len(data["detailed_observations"])
        for obs in data["detailed_observations"]:
            sev_k = obs["severity"].lower()
            if sev_k in data["executive_summary"]["severity_count"]:
                data["executive_summary"]["severity_count"][sev_k] += 1

        return data

    def structure_transcript(
        self,
        markdown_text: str,
        output_json_path: Optional[str] = None,
        source_file_name: str = ""
    ) -> Dict[str, Any]:
        """
        Main execution method for Stage 3.
        """
        print(f"[Stage 3] Structuring markdown ({len(markdown_text)} chars) into canonical JSON schema...")
        prompt = self._build_prompt(markdown_text)

        structured_json = {}
        if self.backend == "ollama":
            try:
                raw_result = self._call_ollama(prompt)
                structured_json = self._parse_and_clean_json(raw_result)
            except Exception as e:
                print(f"[Stage 3] Ollama connection error ({e}). Using deterministic fallback parser...")
                structured_json = self._rule_based_structuring(markdown_text)
        elif self.backend == "rule_based":
            structured_json = self._rule_based_structuring(markdown_text)
        else:
            try:
                raw_result = self._call_transformers(prompt)
                structured_json = self._parse_and_clean_json(raw_result)
            except Exception as e:
                print(f"[Stage 3] Transformers error ({e}). Using deterministic fallback parser...")
                structured_json = self._rule_based_structuring(markdown_text)

        # Attach standard metadata
        if "_meta" not in structured_json:
            structured_json["_meta"] = {}
        structured_json["_meta"].update({
            "pipeline_version": "3.0.0-decoupled",
            "source_file": source_file_name,
            "structuring_backend": self.backend,
            "structuring_model": self.model_id
        })

        if output_json_path:
            out_path = Path(output_json_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(structured_json, f, indent=2)
            print(f"[Stage 3] Saved standardized Master JSON to: {out_path}")

        return structured_json
