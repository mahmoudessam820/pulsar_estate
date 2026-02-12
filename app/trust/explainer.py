from typing import Dict


def explain_confidence(confidence: Dict) -> str:

    label = confidence["label"]
    score = confidence["score"]
    sources = confidence["sources_count"]
    source_strength = confidence["source_strength"]
    freshness = confidence["freshness"]
    evidence = confidence["evidence_coverage"]

    explanation_parts = []

    explanation_parts.append(
        f"This insight is rated '{label}' with a confidence score of {score}/100."
    )

    if sources >= 3:
        explanation_parts.append(
            f"It is supported by {sources} independent sources."
        )
    elif sources == 2:
        explanation_parts.append(
            "It is supported by two independent sources."
        )
    else:
        explanation_parts.append(
            "It relies on limited source coverage."
        )

    if source_strength >= 0.8:
        explanation_parts.append(
            "The referenced domains have strong authority."
        )
    elif source_strength >= 0.5:
        explanation_parts.append(
            "The referenced domains have moderate authority."
        )
    else:
        explanation_parts.append(
            "The referenced domains have limited authority."
        )

    if freshness >= 0.7:
        explanation_parts.append(
            "The information is based on recent publications."
        )
    elif freshness >= 0.4:
        explanation_parts.append(
            "The information has moderate recency."
        )
    else:
        explanation_parts.append(
            "The information may be outdated."
        )

    if evidence >= 0.7:
        explanation_parts.append(
            "Most claims are directly supported by evidence."
        )
    elif evidence >= 0.4:
        explanation_parts.append(
            "Some claims are supported by evidence."
        )
    else:
        explanation_parts.append(
            "Evidence coverage is limited."
        )

    return " ".join(explanation_parts)
