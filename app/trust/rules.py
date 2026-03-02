from typing import List, Dict, Union
from urllib.parse import urlparse
from datetime import datetime, timezone


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
    "propertynews.ae": 0.9,
    "magusproperties.ae": 0.9,
}

DEFAULT_AUTHORITY = 0.3
MAX_DAYS = 365


def source_strength(urls: List[str]) -> float:
    """
    The function calculates the average authority score for a list of URLs based on their domain
    authority values.
    
    :param urls: A list of URLs for which you want to calculate the source strength
    :type urls: List[str]
    :return: The function `source_strength(urls: List[str]) -> float` returns the average authority
    score of the domains extracted from the list of URLs provided as input. If the list of URLs is
    empty, it returns 0.0.
    """
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
    """
    Computes the fraction of evidence entries that have a meaningful source_url.

    Rules for considering a source valid:
    - must exist (not missing key)
    - must be str
    - must not be empty after stripping whitespace

    Returns 0.0 when:
    - evidence list is empty
    - no entry has a valid source_url
    """
    if not evidence:
        return 0.0

    valid = 0

    for item in evidence:
        url = item.get("source_url")

        if isinstance(url, str) and url.strip():
            valid += 1

    return round(valid / len(evidence), 2)


def freshness_score(published_date: Union[str, datetime]) -> float:
    if not published_date:
        return 0.0

    # Convert to datetime
    if isinstance(published_date, datetime):
        published = published_date
    elif isinstance(published_date, str):
        try:
            published = datetime.strptime(published_date.strip(), "%Y-%m-%d")
        except ValueError:
            return 0.0
    else:
        # Not str, not datetime → invalid type
        return 0.0

    # Make both sides timezone-aware (UTC) to avoid naive-vs-aware comparison issues
    now = datetime.now(timezone.utc)

    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)
    else:
        published = published.astimezone(timezone.utc)

    # If published in the future → treat as 0 freshness (common heuristic)
    if published > now:
        return 0.0

    days_old = (now - published).days

    if days_old < 0:  # safety (shouldn't happen after check above)
        return 0.0
    if days_old > MAX_DAYS:
        return 0.0

    score = 1 - (days_old / MAX_DAYS)
    return round(max(0.0, min(1.0, score)), 2)  # clamp just in case


def consensus_score(num_sources: int) -> float:
    return round(min(num_sources / 5, 1.0), 2)
