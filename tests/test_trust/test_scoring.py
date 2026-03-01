import pytest
from unittest.mock import patch, Mock

from app.trust.scoring import (
    confidence_label,
    confidence_badge,
    calculate_confidence,
)


# Test confidence_label function
def test_confidence_label():
    assert confidence_label(100) == "Very High"
    assert confidence_label(85) == "Very High"
    assert confidence_label(84.9) == "High"
    assert confidence_label(70) == "High"
    assert confidence_label(69.9) == "Moderate"
    assert confidence_label(50) == "Moderate"
    assert confidence_label(49.9) == "Low"
    assert confidence_label(30) == "Low"
    assert confidence_label(29.9) == "Very Low"
    assert confidence_label(0) == "Very Low"


# Test confidence_badge function
def test_confidence_badge():
    assert confidence_badge(100) == "🟢"
    assert confidence_badge(70) == "🟢"
    assert confidence_badge(69.9) == "🟡"
    assert confidence_badge(50) == "🟡"
    assert confidence_badge(49.9) == "🔴"
    assert confidence_badge(0) == "🔴"


# Test calculate_confidence function
@patch("app.trust.rules.source_strength")
@patch("app.trust.rules.evidence_coverage")
@patch("app.trust.rules.freshness_score")
@patch("app.trust.rules.consensus_score")
def test_calculate_confidence_normal(
    mock_consensus_score,
    mock_freshness_score,
    mock_evidence_coverage,
    mock_source_strength,
):
    # Setup mocks
    mock_source_strength.return_value = 0.8
    mock_evidence_coverage.return_value = 0.9
    mock_freshness_score.side_effect = [
        0.85,
        0.75,
    ]  # Two documents with different freshness
    mock_consensus_score.return_value = 0.8

    # Test data
    documents = [
        {"url": "https://dubailand.gov.ae/report", "published_at": "2026-01-01"},
        {"url": "https://reuters.com/article", "published_at": "2025-11-01"},
    ]

    ai_result = {
        "evidence": [
            {"claim": "A", "source_url": "https://valid.com"},
            {"claim": "B", "source_url": "https://another.com"},
            {"claim": "C", "source_url": None},
        ]
    }

    result = calculate_confidence(documents, ai_result)

    # Calculate expected values
    avg_freshness = (0.84 + 0.67) / 2  # 0.76

    expected_confidence = (
        0.8 * 0.4  # source strength
        + 0.9 * 0.2  # evidence coverage
        + avg_freshness * 0.2  # freshness
        + 0.8 * 0.2  # consensus
    ) * 100  # 81.2

    assert result["score"] == pytest.approx(expected_confidence, 0.1)
    assert result["label"] == confidence_label(result["score"])
    assert result["badge"] == confidence_badge(result["score"])
    assert result["source_strength"] == 0.93
    assert result["evidence_coverage"] == 0.67
    assert result["freshness"] == pytest.approx(avg_freshness, 0.77)
    assert result["consensus"] == 0.4
    assert result["sources_count"] == 2


def test_calculate_confidence_no_urls():
    documents = [{"title": "Doc without URL", "published_at": "2026-01-01"}]

    ai_result = {"evidence": []}

    with patch.multiple(
        "app.trust.rules",
        source_strength=Mock(return_value=0.0),
        evidence_coverage=Mock(return_value=0.0),
        freshness_score=Mock(return_value=0.8),
        consensus_score=Mock(return_value=0.0),
    ):
        result = calculate_confidence(documents, ai_result)

        assert result["sources_count"] == 0
        assert result["consensus"] == 0.0
        assert result["source_strength"] == 0.0


def test_calculate_confidence_no_dates():
    documents = [{"url": "https://example.com"}]

    ai_result = {"evidence": []}

    with patch.multiple(
        "app.trust.rules",
        source_strength=Mock(return_value=0.8),
        evidence_coverage=Mock(return_value=0.0),
        freshness_score=Mock(return_value=0.8),  # Won't be used
        consensus_score=Mock(return_value=0.8),
    ):
        result = calculate_confidence(documents, ai_result)

        assert result["freshness"] == 0.0  # Default when no dates
        assert result["sources_count"] == 1
