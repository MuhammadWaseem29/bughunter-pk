SEVERITY_PROMPT = """You are a cybersecurity expert. Analyze the following bug report and classify its severity.

Bug Report:
{report}

Respond in this exact JSON format:
{{
  "severity": "Critical" | "High" | "Medium" | "Low",
  "score": <number 1-10>,
  "reasoning": "<brief explanation in English>",
  "reasoning_urdu": "<brief explanation in Urdu>"
}}

Classification guidelines:
- Critical (9-10): Remote code execution, SQL injection with data exfiltration, authentication bypass, full system compromise
- High (7-8): Stored XSS, CSRF on sensitive actions, IDOR exposing PII, privilege escalation
- Medium (4-6): Reflected XSS, information disclosure, missing security headers, weak password policy
- Low (1-3): Clickjacking, verbose error messages, version disclosure, minor information leaks

Respond ONLY with valid JSON."""


CATEGORY_PROMPT = """You are a cybersecurity expert. Classify this bug report into vulnerability categories.

Bug Report:
{report}

Respond in this exact JSON format:
{{
  "primary_category": "<primary vulnerability type>",
  "secondary_categories": ["<category1>", "<category2>"],
  "owasp_top10": "<corresponding OWASP Top 10 category>",
  "attack_vector": "<Network|Adjacent|Local|Physical>",
  "explanation": "<brief explanation>"
}}

Valid categories: XSS, SQL Injection, CSRF, IDOR, Authentication Bypass, Authorization Bypass,
Information Disclosure, Remote Code Execution, File Upload, Path Traversal, SSRF, XXE,
Business Logic, Cryptographic Issues, Security Misconfiguration, Open Redirect, Command Injection

Respond ONLY with valid JSON."""


FIX_SUGGESTION_PROMPT = """You are a senior security engineer. Based on this vulnerability report, suggest a fix.

Vulnerability: {category}
Severity: {severity}
Details:
{report}

Provide:
1. Root cause analysis
2. Specific code fix (if applicable)
3. Best practices to prevent this in the future
4. Testing recommendations

Respond in this exact JSON format:
{{
  "root_cause": "<explanation>",
  "code_fix": "<code snippet or configuration change>",
  "best_practices": ["<practice1>", "<practice2>", "<practice3>"],
  "testing": "<how to verify the fix>",
  "estimated_effort": "<Low|Medium|High>"
}}

Respond ONLY with valid JSON."""


URDU_TRANSLATION_PROMPT = """Translate the following Urdu bug report to English. Preserve all technical terms.

Urdu Report:
{report}

Respond in this exact JSON format:
{{
  "english_translation": "<full English translation>",
  "technical_terms": ["<term1>: <translation>", "<term2>: <translation>"],
  "confidence": "<High|Medium|Low>"
}}

Respond ONLY with valid JSON."""


RISK_SCORE_PROMPT = """You are a risk assessment expert. Calculate a comprehensive risk score for this vulnerability.

Category: {category}
Severity: {severity}
Details:
{report}

Consider: exploitability, impact, affected users, data sensitivity, remediation complexity.

Respond in this exact JSON format:
{{
  "risk_score": <number 1-100>,
  "exploitability": "<High|Medium|Low>",
  "business_impact": "<High|Medium|Low>",
  "affected_scope": "<number of potentially affected users/systems>",
  "remediation_urgency": "<Immediate|Short-term|Long-term>",
  "summary": "<one paragraph risk summary>"
}}

Respond ONLY with valid JSON."""
