import logging
from typing import List
from urllib.parse import urlparse


logger = logging.getLogger(__name__)


# Define blacklisted domains (without 'www.' for easier matching)
BLACKLISTED_DOMAINS = {"youtube.com", "tiktok.com"}


def normalize_query(query: str) -> str:
    """
    Normalize and enrich search queries without duplicating keywords
    already present in the query. This prevents timeouts and 403 errors.
    """

    base_keywords = [
        "United Arab Emirates",
        "UAE",
        "Dubai real estate",
        "Abu Dhabi",
        "Dubai",
        "Real Estate In",
    ]

    query_lower = query.lower()

    # Filter out base keywords that are already present in the query
    missing_keywords = [kw for kw in base_keywords if kw.lower() not in query_lower]

    # Limit to max 3 extra keywords to prevent excessively long queries
    if missing_keywords:
        logger.info(
            "Enriching query with missing keywords: %s", ", ".join(missing_keywords)
        )
        return f"{query} {' '.join(missing_keywords[:3])}".strip()

    return query


def has_meaningful_content(url: str) -> bool:
    """
    Check if a URL has meaningful content beyond just the domain.

    Returns True if the URL has:
    - A non-root path (anything other than empty, '/', or whitespace-only paths)
    - Query parameters
    - Fragment identifiers

    Returns False for URLs that are essentially just domains or malformed URLs.

    Examples:
    - "https://example.com/" -> False (just root path)
    - "https://example.com" -> False (just domain)
    - "https://example.com/path" -> True (has path)
    - "https://example.com/?query=param" -> True (has query)
    - "https://example.com#fragment" -> True (has fragment)
    - "https://example.com/   " -> False (path is just whitespace)
    - "example.com/path" -> False (invalid URL, missing scheme)
    - "https:///path" -> False (invalid URL, missing domain)
    """

    # Clean the input
    url = url.strip()
    if not url:
        return False

    # Validate URL structure
    try:
        parsed = urlparse(url)
        # Check if URL has a scheme and network location (domain)
        if not parsed.scheme or not parsed.netloc:
            return False
    except Exception:
        return False

    # Check if path is empty, just a slash, or just whitespace
    is_root_path = parsed.path in ("", "/") or parsed.path.strip() == ""

    # Check if there are query parameters or fragment identifiers
    has_query_or_fragment = bool(parsed.query) or bool(parsed.fragment)

    # Return True if it has a non-root path OR query/fragment parameters
    return (not is_root_path) or has_query_or_fragment


def is_blacklisted(url: str) -> bool:
    """
    Check if a URL belongs to a blacklisted domain (e.g., YouTube, TikTok).
    """
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()

        # Remove 'www.' prefix for consistent matching
        if netloc.startswith("www."):
            netloc = netloc[4:]

        # Check if the domain ends with any blacklisted domain
        return any(netloc.endswith(domain) for domain in BLACKLISTED_DOMAINS)
    except Exception:
        logger.warning("Failed to parse URL: %s", url)
        return False


def filter_blacklisted_urls(urls: List[str]) -> List[str]:
    """
    Filter out URLs from the list that belong to blacklisted domains.
    """

    logger.info("Filter out urls from blacklisted domains")
    return [url for url in urls if not is_blacklisted(url)]
