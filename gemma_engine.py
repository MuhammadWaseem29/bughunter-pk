import json
import google.generativeai as genai
from prompts import (
    SEVERITY_PROMPT, CATEGORY_PROMPT, FIX_SUGGESTION_PROMPT,
    URDU_TRANSLATION_PROMPT, RISK_SCORE_PROMPT
)


class GemmaEngine:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    def _generate(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text

    def _parse_json(self, text: str) -> dict:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(text[start:end])
            return {"error": "Failed to parse response", "raw": text}

    def classify_severity(self, report: str) -> dict:
        prompt = SEVERITY_PROMPT.format(report=report)
        raw = self._generate(prompt)
        return self._parse_json(raw)

    def detect_category(self, report: str) -> dict:
        prompt = CATEGORY_PROMPT.format(report=report)
        raw = self._generate(prompt)
        return self._parse_json(raw)

    def suggest_fix(self, report: str, category: str, severity: str) -> dict:
        prompt = FIX_SUGGESTION_PROMPT.format(
            report=report, category=category, severity=severity
        )
        raw = self._generate(prompt)
        return self._parse_json(raw)

    def translate_urdu(self, report: str) -> dict:
        prompt = URDU_TRANSLATION_PROMPT.format(report=report)
        raw = self._generate(prompt)
        return self._parse_json(raw)

    def calculate_risk(self, report: str, category: str, severity: str) -> dict:
        prompt = RISK_SCORE_PROMPT.format(
            report=report, category=category, severity=severity
        )
        raw = self._generate(prompt)
        return self._parse_json(raw)

    def full_analysis(self, report: str) -> dict:
        translation = self.translate_urdu(report)
        analysis_text = translation.get("english_translation", report)

        severity = self.classify_severity(analysis_text)
        category = self.detect_category(analysis_text)
        fix = self.suggest_fix(
            analysis_text,
            category.get("primary_category", "Unknown"),
            severity.get("severity", "Medium")
        )
        risk = self.calculate_risk(
            analysis_text,
            category.get("primary_category", "Unknown"),
            severity.get("severity", "Medium")
        )

        return {
            "translation": translation,
            "severity": severity,
            "category": category,
            "fix": fix,
            "risk": risk,
        }
