import pytest

from app.trust.explainer import explain_confidence


def test_high_confidence():
    confidence = {
        "label": "High",
        "score": 95,
        "sources_count": 5,
        "source_strength": 0.85,
        "freshness": 0.8,
        "evidence_coverage": 0.9,
    }
    result = explain_confidence(confidence)
    expected = (
        "This insight is rated 'High' with a confidence score of 95/100. "
        "It is supported by 5 independent sources. "
        "The referenced domains have strong authority. "
        "The information is based on recent publications. "
        "Most claims are directly supported by evidence."
    )
    assert result == expected


def test_medium_confidence():
    confidence = {
        "label": "Medium",
        "score": 65,
        "sources_count": 2,
        "source_strength": 0.6,
        "freshness": 0.5,
        "evidence_coverage": 0.5,
    }
    result = explain_confidence(confidence)
    expected = (
        "This insight is rated 'Medium' with a confidence score of 65/100. "
        "It is supported by two independent sources. "
        "The referenced domains have moderate authority. "
        "The information has moderate recency. "
        "Some claims are supported by evidence."
    )
    assert result == expected


def test_low_confidence():
    confidence = {
        "label": "Low",
        "score": 25,
        "sources_count": 1,
        "source_strength": 0.3,
        "freshness": 0.3,
        "evidence_coverage": 0.3,
    }
    result = explain_confidence(confidence)
    expected = (
        "This insight is rated 'Low' with a confidence score of 25/100. "
        "It relies on limited source coverage. "
        "The referenced domains have limited authority. "
        "The information may be outdated. "
        "Evidence coverage is limited."
    )
    assert result == expected


# Edge Cases
def test_sources_exactly_3():
    confidence = {
        "sources_count": 3,
        "label": "Test",
        "score": 50,
        "source_strength": 0.5,
        "freshness": 0.5,
        "evidence_coverage": 0.5,
    }
    result = explain_confidence(confidence)
    assert "It is supported by 3 independent sources." in result


def test_source_strength_threshold_0_8():
    confidence = {
        "source_strength": 0.8,
        "label": "Test",
        "score": 50,
        "sources_count": 3,
        "freshness": 0.5,
        "evidence_coverage": 0.5,
    }
    result = explain_confidence(confidence)
    assert "The referenced domains have strong authority." in result


def test_freshness_threshold_0_4():
    confidence = {
        "freshness": 0.4,
        "label": "Test",
        "score": 50,
        "sources_count": 3,
        "source_strength": 0.5,
        "evidence_coverage": 0.5,
    }
    result = explain_confidence(confidence)
    assert "The information has moderate recency." in result


def test_evidence_threshold_0_7():
    confidence = {
        "evidence_coverage": 0.7,
        "label": "Test",
        "score": 50,
        "sources_count": 3,
        "source_strength": 0.5,
        "freshness": 0.5,
    }
    result = explain_confidence(confidence)
    assert "Most claims are directly supported by evidence." in result


def test_minimum_score():
    confidence = {
        "score": 0,
        "label": "Test",
        "sources_count": 3,
        "source_strength": 0.5,
        "freshness": 0.5,
        "evidence_coverage": 0.5,
    }
    result = explain_confidence(confidence)
    assert "confidence score of 0/100" in result


def test_maximum_score():
    confidence = {
        "score": 100,
        "label": "Test",
        "sources_count": 3,
        "source_strength": 0.5,
        "freshness": 0.5,
        "evidence_coverage": 0.5,
    }
    result = explain_confidence(confidence)
    assert "confidence score of 100/100" in result


# Invalid Inputs
def test_missing_label_key():
    confidence = {
        "score": 50,
        "sources_count": 3,
        "source_strength": 0.5,
        "freshness": 0.5,
        "evidence_coverage": 0.5,
    }
    with pytest.raises(KeyError):
        explain_confidence(confidence)


def test_sources_count_as_string():
    confidence = {
        "label": "Test",
        "score": 50,
        "sources_count": "3",
        "source_strength": 0.5,
        "freshness": 0.5,
        "evidence_coverage": 0.5,
    }
    with pytest.raises(TypeError):
        explain_confidence(confidence)


def test_source_strength_out_of_bounds():
    confidence = {
        "label": "Test",
        "score": 50,
        "sources_count": 3,
        "source_strength": 1.2,  # Beyond 0-1 range
        "freshness": 0.5,
        "evidence_coverage": 0.5,
    }
    result = explain_confidence(confidence)
    assert "strong authority" in result  # Still triggers highest tier


def test_negative_sources_count():
    confidence = {
        "label": "Test",
        "score": 50,
        "sources_count": -1,
        "source_strength": 0.5,
        "freshness": 0.5,
        "evidence_coverage": 0.5,
    }
    result = explain_confidence(confidence)
    assert "It relies on limited source coverage." in result


def test_all_numeric_fields_invalid_type():
    confidence = {
        "label": "Test",
        "score": "fifty",
        "sources_count": [],
        "source_strength": {},
        "freshness": None,
        "evidence_coverage": set(),
    }
    with pytest.raises(TypeError):
        explain_confidence(confidence)
