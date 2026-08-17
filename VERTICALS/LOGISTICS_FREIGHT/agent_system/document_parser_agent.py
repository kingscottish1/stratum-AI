"""
Document parser agent: turns inbound freight documents (PDF, scanned,
email attachments) into structured JSON for downstream agents.

Document types handled:
  - invoices (carrier invoices, fuel surcharge, accessorials)
  - bills of lading (BOL)
  - proofs of delivery (POD)
  - rate confirmations (rate cons)
  - exception notices / OS&D reports
"""
import json
import logging
from pathlib import Path
from typing import Any, Optional

from CORE_AGENT_INFRASTRUCTURE.frameworks.custom_frameworks.base_agent_class import BaseAgent
from CORE_AGENT_INFRASTRUCTURE.shared_tools.document_processing.pdf_parser import PDFParser
from CORE_AGENT_INFRASTRUCTURE.shared_tools.document_processing.document_classifier import DocumentClassifier

logger = logging.getLogger("vertical.logistics.docparser")

DOC_TAXONOMY = [
    "carrier_invoice", "bill_of_lading", "proof_of_delivery",
    "rate_confirmation", "exception_notice", "fuel_surcharge", "other",
]


class DocumentParserAgent(BaseAgent):
    def __init__(self, pdf_parser: Optional[PDFParser] = None, classifier: Optional[DocumentClassifier] = None, llm=None):
        super().__init__(name="document_parser_agent", vertical="logistics_freight", llm=llm)
        self.pdf_parser = pdf_parser or PDFParser()
        self.classifier = classifier or DocumentClassifier(llm=llm)

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        file_path = input_data.get("file_path") or input_data.get("file_bytes")
        source = input_data.get("source", "email")

        text = self._extract_text(file_path)
        classification = self.classifier.classify(text, DOC_TAXONOMY)
        fields = self._extract_fields(text, classification["document_type"])

        return {
            "status": "success",
            "result": {
                "document_type": classification["document_type"],
                "confidence": classification["confidence"],
                "fields": fields,
                "source": source,
                "text_preview": text[:500],
            },
        }

    # -- internals ------------------------------------------------------------
    def _extract_text(self, file_path) -> str:
        if isinstance(file_path, (str, Path)) and str(file_path).lower().endswith(".pdf"):
            return self.pdf_parser.extract_text(file_path)
        if isinstance(file_path, bytes):
            return self.pdf_parser.extract_text(file_path)
        if isinstance(file_path, (str, Path)):
            return Path(file_path).read_text(encoding="utf-8", errors="ignore")
        raise ValueError("Unsupported document source")

    def _extract_fields(self, text: str, doc_type: str) -> dict:
        """Extract doc-specific fields. Uses regex + LLM hybrid."""
        common = self._regex_extract(text)
        if self.llm is not None and doc_type in ("carrier_invoice", "bill_of_lading"):
            prompt = (
                f"Extract structured fields from this {doc_type.replace('_', ' ')} text. "
                'JSON keys: "invoice_number", "shipment_reference", "carrier", '
                '"shipper", "consignee", "origin", "destination", "amount", '
                '"currency", "date", "weight_lbs", "pieces", "notes". '
                'Use null when absent.\n\nText:\n{text[:6000]}'
            )
            try:
                raw = self.llm.invoke(prompt.format(text=text))
                content = raw.content if hasattr(raw, "content") else str(raw)
                return {**common, **json.loads(content)}
            except Exception:  # noqa: BLE001
                logger.warning("LLM field extraction failed, using regex only")
        return common

    def _regex_extract(self, text: str) -> dict:
        import re

        def first(pattern: str) -> Optional[str]:
            m = re.search(pattern, text, re.IGNORECASE)
            return m.group(1).strip() if m else None

        return {
            "invoice_number": first(r"(?:invoice|inv\.?)\s*[#:]?\s*([A-Z0-9\-]{5,25})"),
            "amount": first(r"(?:total|amount)\s*(?:due)?\s*[:$]?\s*\$?([0-9,]+\.\d{2})"),
            "date": first(r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"),
            "weight_lbs": first(r"(\d[\d,]*)\s*(?:lbs|lb|pounds)"),
        }
