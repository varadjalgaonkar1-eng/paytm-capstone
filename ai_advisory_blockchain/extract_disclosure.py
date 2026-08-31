import json
import re
from disclosure_snippets import DISCLOSURE_SNIPPETS


def extract_signals(snippet: str) -> dict:
    text = snippet.lower()

    # 1. Risk Flags (Litigation, Regulatory, Customer Concentration)
    risk_flags = []
    if "litigation" in text or "lawsuit" in text:
        risk_flags.append("litigation_risk")
    if (
        "regulatory" in text
        or "compliance" in text
        or "regulator" in text
        or "data-localization" in text
    ):
        risk_flags.append("regulatory_scrutiny")
    if "top three customers" in text or "concentration" in text or "percent of total revenue" in text:
        risk_flags.append("customer_concentration_risk")

    # 2. Hedging Detection (Assuming, Cautiously, Visibility)
    hedging_detected = bool(
        re.search(r"\b(assuming|cautiously|visibility|macro uncertainty)\b", text)
    )

    # 3. Sentiment Classification
    if any(w in text for w in ["confident", "approved", "expanded"]):
        sentiment = "confident"
    elif hedging_detected or len(risk_flags) > 0:
        sentiment = "cautious"
    else:
        sentiment = "neutral"

    return {
        "risk_flags": risk_flags,
        "hedging_detected": hedging_detected,
        "sentiment": sentiment,
    }


if __name__ == "__main__":
    print("=== Structured Disclosure Extraction Outputs ===")
    for doc in DISCLOSURE_SNIPPETS:
        doc_id = doc.split(":")[0]
        signals = extract_signals(doc)
        print(f"\nSnippet: {doc}")
        print(f"Extracted Signals: {json.dumps(signals, indent=2)}")
