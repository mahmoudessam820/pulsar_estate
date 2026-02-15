from typing import List, Dict, Union
from urllib.parse import urlparse
from datetime import datetime


DOMAIN_AUTHORITY: Dict[str, float] = {
    # High authority government and official sources
    "dubailand.gov.ae": 0.95,
    "dari.ae": 0.95,
    "dubai.ae": 0.95,
    "wam.ae": 0.95,
    "u.ae": 0.95,
    "ncema.gov.ae": 0.95,
    # High authority international news sources
    "reuters.com": 0.9,
    "bloomberg.com": 0.9,
    "forbes.com": 0.9,
    "cnbc.com": 0.9,
    "edition.cnn.com": 0.9,
    "wsj.com": 0.9,
    "bbc.com": 0.9,
    "ft.com": 0.9,
    "globalpropertyguide.com": 0.9,
    # High authority regional news and real estate sources
    "bayut.com": 0.9,
    "khaleejtimes.com": 0.9,
    "dxbproperties.ae": 0.9,
    "propertyfinder.ae": 0.9,
    "aljazeera.com": 0.9,
    "gulfnews.com": 0.9,
    "iqiglobal.com": 0.9,
    "thenationalnews.com": 0.9,
    "anika-property.com": 0.9,
    "mordorintelligence.com": 0.9,
    "arabianbusiness.com": 0.9,
    "dxbinteract.com": 0.9,
    "jamesedition.com": 0.9,
    "knightfrank.ae": 0.9,
    "emirates.estate": 0.9,
    "economymiddleeast.com": 0.9,
    "miradevelopments.ae": 0.9,
    "dubai-immo.com": 0.9,
}

DEFAULT_AUTHORITY = 0.3
MAX_DAYS = 365


def source_strength(urls: List[str]) -> float:
    if not urls:
        return 0.0

    scores: List[float] = []

    for url in urls:
        domain: str = urlparse(url).netloc.lower()
        matched: bool = False

        for known, score in DOMAIN_AUTHORITY.items():
            if domain.endswith(known):
                scores.append(score)
                matched = True
                break

        if not matched:
            scores.append(DEFAULT_AUTHORITY)

    return round(sum(scores) / len(scores), 2)


def evidence_coverage(evidence: List[Dict]) -> float:
    if not evidence:
        return 0.0

    backed = [ev for ev in evidence if ev.get("source_url")]

    return round(len(backed) / len(evidence), 2)


def freshness_score(published_date: Union[str, datetime]) -> float:
    if not published_date:
        return 0.0

    try:
        # Handle both string and datetime inputs
        if isinstance(published_date, datetime):
            published = published_date
        else:
            published = datetime.strptime(published_date, "%Y-%m-%d")
    except ValueError:
        return 0.0

    days_old = (datetime.utcnow() - published).days

    if days_old > MAX_DAYS:
        return 0.0

    return round(1 - (days_old / MAX_DAYS), 2)


def consensus_score(num_sources: int) -> float:
    return round(min(num_sources / 5, 1.0), 2)
