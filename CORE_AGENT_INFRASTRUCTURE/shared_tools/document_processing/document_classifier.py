"""
Document type classifier (LLM-based with cache).

Used by the logistics vertical to route inbound documents
(invoice, POD, rate confirmation, BOL, exception notice...).
"""
import hashlib
import json
import logging
from typing import Any, Optional

logger = logging.getLogger("stratum.documents")


class DocumentClassifier:
    """Classify documents into a known taxonomy with confidence."""

    def __init__(self, llm: Any, cache: Any = None):
        self.llm = llm
        self.cache = cache  # optional redis-backed cache

    def classify(self, text: str, taxonomy: list[str]) -> dict:
        """Return {'document_type': str, 'confidence': float, 'reason': str}."""
        if self.llm is None:
            return self._rule_based(text, taxonomy)

        cache_key = hashlib.sha256(text[:2000].encode()).hexdigest()
        if self.cache is not None:
            try:
                cached = self.cache.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception:  # noqa: BLE001
                pass

        prompt = (
            "Classify the following document into exactly one of these types:\n"
            f"{json.dumps(taxonomy)}\n\n"
            f"Document text (first 6000 chars):\n{text[:6000]}\n\n"
            'Respond with JSON: {"document_type": "...", "confidence": 0.0-1.0, "reason": "..."}'
        )
        raw = self.llm.invoke(prompt)
        content = raw.content if hasattr(raw, "content") else str(raw)
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Classifier returned non-JSON, defaulting to unknown")
            parsed = {"document_type": "unknown", "confidence": 0.0, "reason": "parse failure"}

        if self.cache is not None:
            try:
                self.cache.set(cache_key, json.dumps(parsed), ex=86400)
            except Exception:  # noqa: BLE001
                pass
        return parsed

    # -- rule-based fallback (works with no LLM configured) --------------------
    RULE_KEYWORDS = [
        ("carrier_invoice", ["invoice", "total due", "freight charges"]),
        ("proof_of_delivery", ["proof of delivery", "pod", "delivered by", "signed"]),
        ("rate_confirmation", ["rate confirmation", "rate con", "confirmation of rate"]),
        ("bill_of_lading", ["bill of lading", "b.o.l.", "shipper", "consignee", "equipment"]),
        ("exception_notice", ["exception", "os&d", "shortage", "damage", "overage"]),
        ("fuel_surcharge", ["fuel surcharge", "fsc"]),
    ]

    def _rule_based(self, text: str, taxonomy: list[str]) -> dict:
        """Keyword-based classification used when no LLM is available."""
        lowered = text.lower()
        for doc_type, keywords in self.RULE_KEYWORDS:
            if doc_type not in taxonomy:
                continue
            hits = sum(1 for kw in keywords if kw in lowered)
            if hits >= 2 or (hits == 1 and keywords[0] in lowered):
                return {
                    "document_type": doc_type,
                    "confidence": round(0.55 + 0.1 * hits, 2),
                    "reason": "rule-based match",
                }
        return {"document_type": "other", "confidence": 0.4, "reason": "no rule matched"}
