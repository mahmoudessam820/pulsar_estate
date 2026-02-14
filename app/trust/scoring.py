from typing import Dict, List

from app.trust.rules import (
    source_strength,
    evidence_coverage,
    freshness_score,
    consensus_score,
)


def confidence_label(score: float) -> str:
    if score >= 85:
        return "Very High"
    elif score >= 70:
        return "High"
    elif score >= 50:
        return "Moderate"
    elif score >= 30:
        return "Low"
    return "Very Low"


def confidence_badge(score: float) -> str:
    if score >= 70:
        return "🟢"
    elif score >= 50:
        return "🟡"
    return "🔴"


def calculate_confidence(
    documents: List[Dict],
    ai_result: Dict,
) -> Dict:
    urls = [d["url"] for d in documents if d.get("url")]
    published_dates = [
        d.get("published_at") for d in documents if d.get("published_at")
    ]

    source = source_strength(urls)
    evidence = evidence_coverage(ai_result.get("evidence", []))

    freshness_scores = [freshness_score(date) for date in published_dates]
    avg_freshness = (
        round(sum(freshness_scores) / len(freshness_scores), 2)
        if freshness_scores
        else 0.0
    )

    consensus = consensus_score(len(urls))

    confidence = (
        source * 0.4 + evidence * 0.2 + avg_freshness * 0.2 + consensus * 0.2
    ) * 100

    score = round(confidence, 1)

    return {
        "score": score,
        "label": confidence_label(score),
        "badge": confidence_badge(score),
        "source_strength": source,
        "evidence_coverage": evidence,
        "freshness": avg_freshness,
        "consensus": consensus,
        "sources_count": len(urls),
    }
