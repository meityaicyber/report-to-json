"""
LLM-driven schema inference and data extraction.
Interfaces with Ollama for local LLM processing.
Optimized for GPU inference with qwen2.5:7b.
"""

import json
import re
import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests


class LLMExtractor:
    """Extract structured JSON from Markdown using LLM schema inference and extraction."""

    def __init__(self, model: str = "qwen2.5:7b", backend: str = "ollama", 
                 host: str = "localhost", port: int = 11434):
        """
        Initialize LLM extractor.
        
        Args:
            model: LLM model name (default: qwen2.5:7b)
            backend: LLM backend (only ollama supported for now)
            host: Ollama server host
            port: Ollama server port
        """
        self.model = model
        self.backend = backend
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.max_tokens_per_call = 16000  # ~64KB text — qwen2.5:7b has 128K context
        self.timeout = 300  # 5 minutes — realistic for local GPU inference

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (conservative: 1 token per 4 chars)."""
        return len(text) // 4

    def chunk_if_needed(self, text: str, max_tokens: int = None) -> List[str]:
        """
        Split text into chunks if it exceeds token budget.
        Splits by ## section boundaries to preserve structure.
        """
        if max_tokens is None:
            max_tokens = self.max_tokens_per_call
        
        if self.estimate_tokens(text) <= max_tokens:
            return [text]
        
        # Split by ## sections
        sections = text.split('\n## ')
        chunks = []
        current_chunk = sections[0]  # Content before first ##
        
        for section in sections[1:]:
            section_with_marker = f'\n## {section}'
            
            if self.estimate_tokens(current_chunk + section_with_marker) > max_tokens:
                # Save current chunk and start new one
                if current_chunk.strip():
                    chunks.append(current_chunk)
                current_chunk = section_with_marker
            else:
                current_chunk += section_with_marker
        
        if current_chunk.strip():
            chunks.append(current_chunk)
        
        return chunks if chunks else [text]

    def _collapse_image_placeholders(self, markdown: str) -> str:
        """
        Collapse consecutive IMAGE_PLACEHOLDER markers to reduce token waste.
        Runs of >3 consecutive placeholders are replaced with a summary.
        """
        lines = markdown.split('\n')
        result = []
        placeholder_count = 0
        
        for line in lines:
            if '<!-- IMAGE_PLACEHOLDER:' in line:
                placeholder_count += 1
                if placeholder_count <= 2:
                    result.append(line)
                # Skip additional placeholders, will add summary after run ends
            else:
                if placeholder_count > 2:
                    result.append(f'<!-- {placeholder_count - 2} additional images omitted -->')
                placeholder_count = 0
                result.append(line)
        
        # Handle trailing placeholders
        if placeholder_count > 2:
            result.append(f'<!-- {placeholder_count - 2} additional images omitted -->')
        
        return '\n'.join(result)

    def _call_ollama(self, prompt: str, timeout: int = None) -> str:
        """
        Call Ollama API and get response.
        Uses GPU-optimized settings for qwen2.5:7b.
        
        Args:
            prompt: Full prompt text
            timeout: Call timeout in seconds
            
        Returns:
            LLM response text
            
        Raises:
            RuntimeError: If API call fails
        """
        if timeout is None:
            timeout = self.timeout
        
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,       # Low temperature for deterministic extraction
                "num_predict": 8192,       # Allow longer responses for complete JSON
                "num_ctx": 32768,          # Use large context window (qwen2.5 supports 128K)
                "num_gpu": 99,             # Force all layers to GPU
                "top_p": 0.9,
                "repeat_penalty": 1.1,
            }
        }
        
        try:
            start_time = time.time()
            response = requests.post(url, json=payload, timeout=timeout)
            elapsed = time.time() - start_time
            
            if response.status_code != 200:
                raise RuntimeError(f"Ollama API error ({response.status_code}): {response.text}")
            
            result = response.json()
            
            print(f"    [LLM] Call completed in {elapsed:.1f}s")
            
            if elapsed > timeout * 0.8:
                print(f"    ⚠️  LLM call approaching timeout ({elapsed:.1f}s / {timeout}s)")
            
            return result.get('response', '')
        
        except requests.Timeout:
            raise RuntimeError(f"Ollama API timeout (>{timeout}s)")
        except requests.RequestException as e:
            raise RuntimeError(f"Ollama API connection error: {e}")

    def _parse_json_response(self, response: str) -> dict:
        """
        Parse JSON from LLM response.
        Handles markdown code fences, preamble text, and other wrapping.
        """
        # Remove markdown code fences
        response = re.sub(r'^```(?:json)?\n?', '', response, flags=re.MULTILINE)
        response = re.sub(r'\n?```$', '', response, flags=re.MULTILINE)
        
        # Try direct parse first
        response_stripped = response.strip()
        try:
            return json.loads(response_stripped)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON object in the response (skip preamble text)
        # Look for the first { and last }
        first_brace = response_stripped.find('{')
        last_brace = response_stripped.rfind('}')
        
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            json_candidate = response_stripped[first_brace:last_brace + 1]
            try:
                return json.loads(json_candidate)
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON array
        first_bracket = response_stripped.find('[')
        last_bracket = response_stripped.rfind(']')
        
        if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
            json_candidate = response_stripped[first_bracket:last_bracket + 1]
            try:
                parsed = json.loads(json_candidate)
                return {"items": parsed}  # Wrap array in object
            except json.JSONDecodeError:
                pass
        
        raise ValueError(f"Invalid JSON response: {response_stripped[:300]}")

    def infer_schema(self, full_markdown: str, doc_type_hint: Optional[str] = None) -> dict:
        """
        Pass 1: Infer JSON schema from document.
        
        Args:
            full_markdown: Full normalized Markdown document
            doc_type_hint: Optional hint about document type
            
        Returns:
            Inferred JSON schema as dict
        """
        # Collapse image placeholders to save tokens
        compact_md = self._collapse_image_placeholders(full_markdown)
        
        # Chunk if needed
        chunks = self.chunk_if_needed(compact_md)
        
        # For schema inference, only send first chunk + summary of remaining sections
        if len(chunks) > 1:
            section_summary = self._extract_section_summary(chunks[1:])
            markdown_for_inference = chunks[0] + '\n\n' + section_summary
        else:
            markdown_for_inference = chunks[0]
        
        # Load schema inference prompt template
        prompt_template = self._load_prompt('schema_inference.txt')
        
        # Build final prompt
        prompt = prompt_template.format(markdown_chunk=markdown_for_inference)
        
        if doc_type_hint:
            prompt = f"Document type hint: {doc_type_hint}\n\n{prompt}"
        
        print(f"  [LLM] Inferring schema ({self.estimate_tokens(prompt)} est. tokens)...")
        
        # Call LLM with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self._call_ollama(prompt)
                schema = self._parse_json_response(response)
                
                # Ensure schema has sections key
                if 'sections' not in schema:
                    schema['sections'] = {}
                
                print(f"  [LLM] ✓ Schema inferred with {len(schema.get('sections', {}))} sections")
                return schema
            
            except (RuntimeError, ValueError) as e:
                if attempt < max_retries - 1:
                    print(f"  [LLM] ⚠️  Schema inference attempt {attempt + 1}/{max_retries} failed: {e}")
                    prompt += "\n\nIMPORTANT: Return ONLY a valid JSON object. No explanation, no markdown fences, no preamble. Start your response with { and end with }."
                else:
                    print(f"  [LLM] ❌ Schema inference failed after {max_retries} attempts: {e}")
        
        # Return minimal schema on failure
        return {
            'sections': {},
            '_error': str(e)
        }

    def extract(self, markdown_chunk: str, inferred_schema: dict, 
                section_hint: Optional[str] = None) -> dict:
        """
        Pass 2: Extract data into inferred schema.
        
        Args:
            markdown_chunk: Markdown content (may be chunk of full document)
            inferred_schema: Schema from Pass 1
            section_hint: Optional name of section being extracted
            
        Returns:
            Extracted JSON conforming to schema
        """
        # Collapse image placeholders
        compact_md = self._collapse_image_placeholders(markdown_chunk)
        
        # Load extraction prompt template
        prompt_template = self._load_prompt('extraction.txt')
        
        # Build final prompt
        prompt = prompt_template.format(
            inferred_schema=json.dumps(inferred_schema, indent=2),
            section_hint=section_hint or '',
            markdown_chunk=compact_md
        )
        
        print(f"  [LLM] Extracting {'(section: ' + section_hint + ')' if section_hint else ''}({self.estimate_tokens(prompt)} est. tokens)...")
        
        # Retry logic
        max_retries = 3
        last_response = None
        for attempt in range(max_retries):
            try:
                response = self._call_ollama(prompt)
                last_response = response
                extracted = self._parse_json_response(response)
                
                print(f"  [LLM] ✓ Extraction successful")
                return extracted
            
            except (RuntimeError, ValueError) as e:
                if attempt < max_retries - 1:
                    print(f"  [LLM] ⚠️  Attempt {attempt + 1}/{max_retries} failed, retrying: {e}")
                    
                    # Append parsing hint for next attempt
                    prompt += "\n\nReturn ONLY a valid JSON object. No markdown, no explanation, no code fences. Start with { and end with }."
                else:
                    print(f"  [LLM] ❌ Extraction failed after {max_retries} attempts")
                    
                    # Return fallback with raw response
                    return {
                        'raw_text_fallback': (last_response[:500] if last_response else str(e)[:500]),
                        '_extraction_status': 'failed'
                    }

    def extract_audit_report(self, markdown_chunk: str) -> dict:
        """
        Direct extraction for audit reports - bypasses schema inference.
        Uses audit-specific prompt to extract vulnerabilities, findings, metadata.
        
        Args:
            markdown_chunk: Markdown content of audit report
            
        Returns:
            Extracted audit data as JSON
        """
        # Collapse image placeholders to save tokens
        compact_md = self._collapse_image_placeholders(markdown_chunk)
        
        # Try to load audit-specific prompt, fallback to generic
        try:
            prompt_template = self._load_prompt('audit_extraction.txt')
        except FileNotFoundError:
            # Fallback to generic extraction
            return self.extract(compact_md, {'sections': {}})
        
        # Build prompt
        prompt = prompt_template.format(markdown_chunk=compact_md)
        
        print(f"  [LLM] Extracting audit report data ({self.estimate_tokens(prompt)} est. tokens)...")
        
        # Retry logic
        max_retries = 3
        last_response = None
        for attempt in range(max_retries):
            try:
                response = self._call_ollama(prompt)
                last_response = response
                extracted = self._parse_json_response(response)
                
                # Validate it looks like an audit extraction
                if isinstance(extracted, dict):
                    vuln_count = len(extracted.get('vulnerabilities', []))
                    print(f"  [LLM] ✓ Audit extraction successful ({vuln_count} vulnerabilities found)")
                else:
                    print(f"  [LLM] ✓ Audit extraction successful")
                return extracted
            
            except (RuntimeError, ValueError) as e:
                if attempt < max_retries - 1:
                    print(f"  [LLM] ⚠️  Attempt {attempt + 1}/{max_retries} failed, retrying: {e}")
                    prompt += "\n\nCRITICAL: Return ONLY a valid JSON object. Start with { and end with }. No markdown, no explanation."
                else:
                    print(f"  [LLM] ❌ Audit extraction failed after {max_retries} attempts")
                    return {
                        'raw_text_fallback': (last_response[:500] if last_response else str(e)[:500]),
                        '_extraction_status': 'failed'
                    }

    def _extract_findings_section(self, markdown_content: str) -> str:
        """
        Extract the findings/vulnerabilities section from audit report.
        Looks for 'Detailed Observations' or similar sections and captures
        everything up to 'Appendices' or end of document.
        
        Args:
            markdown_content: Full markdown content
            
        Returns:
            Findings section or empty string if not found
        """
        # Use patterns that capture from the findings heading to Appendices/END
        # NOT stopping at the first ## heading (which would be inside a finding)
        patterns = [
            r'(?:##\s+)?Detailed Observations.*?(?=(?:##\s+)?Appendic|END OF DOCUMENT|$)',
            r'(?:##\s+)?Findings.*?(?=(?:##\s+)?Appendic|END OF DOCUMENT|$)',
            r'(?:##\s+)?Vulnerabilities.*?(?=(?:##\s+)?Appendic|END OF DOCUMENT|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, markdown_content, re.DOTALL | re.IGNORECASE)
            if match:
                result = match.group(0)
                # Only return if we got substantial content (not just the heading)
                if len(result) > 100:
                    return result
        
        # If no findings section found, return empty
        return ""

    def is_audit_report(self, markdown_content: str) -> bool:
        """
        Detect if content is an audit/security assessment report.
        
        Args:
            markdown_content: Markdown content to analyze
            
        Returns:
            True if appears to be audit report, False otherwise
        """
        audit_keywords = [
            'audit', 'vulnerability', 'finding', 'cvss', 'remediation',
            'exploit', 'severity', 'critical', 'high risk', 'penetration',
            'assessment', 'security testing', 'threat', 'risk rating',
            'recommendation', 'scope', 'methodology', 'engagement'
        ]
        
        content_lower = markdown_content.lower()
        keyword_count = sum(1 for kw in audit_keywords if kw in content_lower)
        
        # If 5+ audit keywords found, likely an audit report
        return keyword_count >= 5

    def extract_concurrent(self, section_chunks: List[Tuple[str, Optional[str]]], 
                          inferred_schema: dict, workers: int = 2) -> List[dict]:
        """
        Extract multiple sections concurrently.
        
        Args:
            section_chunks: List of (markdown, section_hint) tuples
            inferred_schema: Schema from Pass 1
            workers: Number of concurrent workers (default 2 for 8GB VRAM)
            
        Returns:
            List of extracted JSON objects in same order
        """
        results = [None] * len(section_chunks)
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {}
            
            for idx, (chunk, hint) in enumerate(section_chunks):
                future = executor.submit(
                    self.extract,
                    chunk,
                    inferred_schema,
                    hint
                )
                futures[future] = idx
            
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    print(f"  [LLM] ❌ Worker error: {e}")
                    results[idx] = {'_extraction_status': 'worker_error', '_error': str(e)}
        
        return results

    def _extract_section_summary(self, chunks: List[str]) -> str:
        """Extract section headings from chunks for schema inference summary."""
        headings = set()
        
        for chunk in chunks:
            for line in chunk.split('\n'):
                if line.startswith('## '):
                    heading = line[3:].strip()
                    if heading:
                        headings.add(heading)
        
        if headings:
            return f"\nOther sections in this document: {', '.join(sorted(headings))}"
        return ""

    def _load_prompt(self, filename: str) -> str:
        """Load prompt template from prompts directory."""
        # Try multiple possible paths
        paths = [
            Path(__file__).parent.parent / 'prompts' / filename,
            Path('prompts') / filename,
            Path('.') / 'prompts' / filename,
        ]
        
        for path in paths:
            if path.exists():
                with open(path, 'r') as f:
                    return f.read()
        
        raise FileNotFoundError(f"Prompt template not found: {filename}")
