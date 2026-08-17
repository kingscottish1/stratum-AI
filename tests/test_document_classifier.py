from CORE_AGENT_INFRASTRUCTURE.shared_tools.document_processing.document_classifier import (
    DocumentClassifier,
)

TAXONOMY = ["carrier_invoice", "bill_of_lading", "proof_of_delivery",
            "rate_confirmation", "exception_notice", "fuel_surcharge", "other"]


def test_rule_based_fallback_without_llm():
    classifier = DocumentClassifier(llm=None)
    assert classifier.classify(
        "CARRIER INVOICE — FedEx Freight, Invoice INV-88213, Total due $1,250.00",
        TAXONOMY,
    )["document_type"] == "carrier_invoice"
    assert classifier.classify(
        "PROOF OF DELIVERY — delivered 07/30, signed by J. Smith", TAXONOMY,
    )["document_type"] == "proof_of_delivery"
    assert classifier.classify(
        "Rate confirmation RC-2210 for lane Denver to Salt Lake City", TAXONOMY,
    )["document_type"] == "rate_confirmation"


def test_unknown_document():
    classifier = DocumentClassifier(llm=None)
    assert classifier.classify("completely random note here", TAXONOMY)["document_type"] == "other"
