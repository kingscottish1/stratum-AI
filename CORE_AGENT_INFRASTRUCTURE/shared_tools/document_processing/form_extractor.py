"""
Form field extraction: regex + LLM hybrid.

Regex handles structured fields (dates, amounts, codes); the LLM fills
the gaps for free-text fields. Falls back gracefully if no LLM is set.
"""
import json
import re
from typing import Any, Optional

import json

DATE_PATTERN = re.compile(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b")
AMOUNT_PATTERN = re.compile(r"\$?\s?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)")
CODE_PATTERN = re.compile(r"\b([A-Z]{2,6}-?\d{3,10})\b")


class FormExtractor:
    """Extract structured fields from raw document text."""

    FIELD_RULES = {
        "date": DATE_PATTERN,
        "amount": AMOUNT_PATTERN,
        "reference_code": CODE_PATTERN,
    }

    def __init__(self, llm: Any = None):
        self.llm = llm

    def extract(self, text: str, fields: list[str]) -> dict[str, Any]:
        """Extract requested fields. Known fields use regex, unknown use LLM."""
        result: dict[str, Any] = {}
        regex_fields = [f for f in fields if f in self.FIELD_RULES]
        llm_fields = [f for f in fields if f not in self.FIELD_RULES]

        for field in regex_fields:
            match = self.FIELD_RULES[field].search(text)
            result[field] = match.group(0) if match else None

        if llm_fields and self.llm:
            prompt = (
                "Extract these fields from the document text as JSON: "
                f"{json.dumps(llm_fields)}\n\nDocument:\n{text[:6000]}\n\n"
                "Respond with JSON only."
            )
            raw = self.llm.invoke(prompt)
            content = raw.content if hasattr(raw, "content") else str(raw)
            try:
                result.update(json.loads(content))
            except json.JSONDecodeError:
                result.update({f: None for f in llm_fields})

        return result
