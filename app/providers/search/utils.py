import re
import logging
from dataclasses import dataclass, field
from urllib.parse import ParseResult, urlparse
from typing import Final, FrozenSet, Iterable, Sequence

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration (tune here, not in function bodies)
# ---------------------------------------------------------------------------

MAX_QUERY_LENGTH: Final[int] = 500
MAX_SPECIAL_CHAR_RATIO: Final[float] = 0.35
MAX_ENRICHMENT_KEYWORDS: Final[int] = 3
MIN_MEANINGFUL_PATH_LENGTH: Final[int] = 2

# Characters that are ubiquitous in natural language and should NOT be
# counted against the special-character ratio. Apostrophes are *deliberately*
# still counted — they are the primary SQLi delimiter.
BENIGN_SPECIAL_CHARS: Final[FrozenSet[str]] = frozenset({".", "-", ","})

BLACKLISTED_DOMAINS: Final[FrozenSet[str]] = frozenset({"youtube.com", "tiktok.com", "apple.com", "pinterest.com"})

# ---------------------------------------------------------------------------
# Compiled patterns (built once at import time)
# ---------------------------------------------------------------------------

_MALICIOUS_PATTERNS: Final[tuple[re.Pattern[str], ...]] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"<\s*script",
        r"<\s*svg",
        r"<\s*img\s+[^>]*onerror\s*=",
        r"javascript\s*:",
        r"eval\s*\(",
        r"document\.cookie",
        r"%3c",
        r"%3e",
        r"&text=",
        r"\bunion\s+select\b",
        r"\bdrop\s+table\b",
        r"\bexec\s*\(",
        r"\.\./",
    )
)

_URL_FRAGMENT_RE: Final[re.Pattern[str]] = re.compile(r"[&?=#]+")
_WHITESPACE_RE: Final[re.Pattern[str]] = re.compile(r"\s+")
# Percent signs that are NOT part of a numeric token (e.g. "%20" or "%3C").
# A literal percent sign directly following a digit ("3% yield") is preserved.
_STRAY_PERCENT_RE: Final[re.Pattern[str]] = re.compile(r"(?<!\d)%(?!\s)")

# ---------------------------------------------------------------------------
# Keyword vocabulary
# ---------------------------------------------------------------------------

# Weighted keyword map: higher weight == stronger topical signal.
# Word-boundary matching is enforced; substrings like "marketplace" will not
# fire on "market".
_KEYWORD_WEIGHTS: Final[dict[str, int]] = {
    # Strong signals
    "real estate": 2,
    "property": 2,
    "villa": 2,
    "apartment": 2,
    "penthouse": 2,
    "townhouse": 2,
    "off-plan": 2,
    "off plan": 2,
    "developer": 2,
    "mortgage": 2,
    "roi": 2,
    # Geo signals
    "dubai": 2,
    "abu dhabi": 2,
    "uae": 2,
    "united arab emirates": 2,
    # Weaker signals (need a co-occurring keyword)
    "market": 1,
    "investment": 1,
    "rental": 1,
    "yield": 1,
    "price": 1,
    "trend": 1,
}

# Minimum weighted score for is_real_estate_query to return True.
RELEVANCE_THRESHOLD: Final[int] = 2

# Keywords appended by the normalizer, in priority order, and the minimum
# weight they are worth (kept as strings so downstream can consume verbatim).
_ENRICHMENT_KEYWORDS: Final[tuple[str, ...]] = (
    "United Arab Emirates",
    "UAE",
    "Dubai real estate",
    "Abu Dhabi",
    "Dubai",
    "Real Estate In",
)


# ---------------------------------------------------------------------------
# Structured results
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class QueryResult:
    """Result of the full L1→L2→L3 pipeline."""

    original: str
    normalized: str
    is_safe: bool
    is_relevant: bool
    reasons: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_valid(self) -> bool:
        return self.is_safe and self.is_relevant


@dataclass(frozen=True)
class URLResult:
    """Result of validating a single URL."""

    url: str
    is_meaningful: bool
    is_blacklisted: bool
    reasons: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_usable(self) -> bool:
        return self.is_meaningful and not self.is_blacklisted


# Layer 1: safety


def is_safe_query(query: str) -> bool:
    """
    Return True if *query* is well-formed and passes all safety heuristics.

    Checks (in order):
        1. Type is str and length <= MAX_QUERY_LENGTH.
        2. First non-space character is alphanumeric.
        3. No known injection / XSS / path-traversal signature.
        4. Ratio of "suspicious" special chars is <= MAX_SPECIAL_CHAR_RATIO.

    This is *defense-in-depth*, not a substitute for parameterized queries
    or output encoding. Treat a True result as "not obviously hostile",
    not as "safe to interpolate".
    """
    if not isinstance(query, str):
        logger.debug("is_safe_query: non-str input %r", type(query))
        return False
    if not query or not query.strip():
        return False
    if len(query) > MAX_QUERY_LENGTH:
        logger.info("is_safe_query: query exceeds %d chars", MAX_QUERY_LENGTH)
        return False

    stripped = query.strip()
    if not stripped[0].isalnum():
        return False

    for pattern in _MALICIOUS_PATTERNS:
        if pattern.search(query):
            logger.warning("is_safe_query: blocked pattern %r", pattern.pattern)
            return False

    suspicious = sum(
        1
        for c in query
        if not c.isalnum() and not c.isspace() and c not in BENIGN_SPECIAL_CHARS
    )
    ratio = suspicious / len(query)
    if ratio > MAX_SPECIAL_CHAR_RATIO:
        logger.info("is_safe_query: special-char ratio %.2f too high", ratio)
        return False

    return True


# Layer 2: topical relevance (scored, word-boundary matched)


def _keyword_hits(query_lower: str) -> list[tuple[str, int]]:
    """Return [(keyword, weight)] for each keyword with a word-boundary match."""
    hits: list[tuple[str, int]] = []
    for kw, weight in _KEYWORD_WEIGHTS.items():
        if re.search(rf"(?<!\w){re.escape(kw)}(?!\w)", query_lower):
            hits.append((kw, weight))
    return hits


def is_real_estate_query(query: str) -> bool:
    """
    Return True if *query* scores >= RELEVANCE_THRESHOLD on the weighted
    real-estate keyword vocabulary.

    Strong keywords (e.g. "villa", "dubai") alone are enough.
    Weak keywords (e.g. "market") require a co-occurring strong or geo term.
    """
    if not isinstance(query, str) or not query:
        return False
    score = sum(weight for _, weight in _keyword_hits(query.lower()))
    return score >= RELEVANCE_THRESHOLD


# Layer 3: normalization / enrichment


def _dedupe_keywords_present(query_lower: str, candidates: Sequence[str]) -> list[str]:
    """Return candidates not already present as word-boundary tokens in query."""
    missing: list[str] = []
    for kw in candidates:
        if not re.search(rf"(?<!\w){re.escape(kw.lower())}(?!\w)", query_lower):
            missing.append(kw)
    return missing


def normalize_query(
    query: str,
    *,
    enrichment_keywords: Sequence[str] = _ENRICHMENT_KEYWORDS,
    max_extra: int = MAX_ENRICHMENT_KEYWORDS,
) -> str:
    """
    Sanitize and (optionally) enrich *query*.

    Steps:
        1. Strip, collapse whitespace, drop URL-fragment characters (`&?=#`).
        2. Preserve numeric percent signs ("3% yield"); drop encoded ones.
        3. Append up to *max_extra* enrichment keywords not already present.

    Idempotent: passing the output back in yields the same string
    (modulo case-preservation of already-present keywords).
    """
    if not isinstance(query, str):
        return ""

    q = query.strip()
    q = _WHITESPACE_RE.sub(" ", q)
    q = _URL_FRAGMENT_RE.sub(" ", q)
    # Remove stray percent signs, but keep "%" that follows a digit.
    q = _STRAY_PERCENT_RE.sub("", q)
    q = _WHITESPACE_RE.sub(" ", q).strip()

    if not enrichment_keywords:
        return q

    q_lower = q.lower()
    missing = _dedupe_keywords_present(q_lower, enrichment_keywords)
    if not missing:
        return q

    extras = missing[:max_extra]
    logger.info("normalize_query: appending keywords %s", ", ".join(extras))
    return f"{q} {' '.join(extras)}".strip()


# URL validation


def _parse_url(url: str) -> ParseResult | None:
    """Return a parsed URL with scheme+host, or None on any problem."""
    if not isinstance(url, str):
        return None
    try:
        parsed = urlparse(url.strip())
    except (ValueError, AttributeError):
        return None
    if not parsed.scheme or not parsed.hostname:
        return None
    return parsed


def has_meaningful_content(url: str) -> bool:
    """
    Return True if *url* has a non-trivial path, query, or fragment.

    A bare domain ("https://example.com/") or an unparseable string
    returns False.
    """
    parsed = _parse_url(url)
    if parsed is None:
        return False

    raw_path = parsed.path or ""
    is_meaningful_path = (
        raw_path not in ("", "/")
        and len(raw_path.strip()) >= MIN_MEANINGFUL_PATH_LENGTH
    )
    has_query_or_fragment = bool(parsed.query) or bool(parsed.fragment)
    return is_meaningful_path or has_query_or_fragment


def is_blacklisted(url: str) -> bool:
    """
    Return True if the URL's host equals, or is a subdomain of, a
    blacklisted domain.

    Port-safe:   https://youtube.com:8080 → True
    Look-alikes are NOT blocked: notyoutube.com → False
    """
    parsed = _parse_url(url)
    if parsed is None:
        logger.warning("is_blacklisted: unparseable URL %r", url)
        # Safer default: treat unparseable as NOT blacklisted so a parser
        # hiccup doesn't silently discard otherwise-fine results.
        return False

    host = parsed.hostname or ""
    host = host.rstrip(".").lower()
    return any(
        host == banned or host.endswith("." + banned) for banned in BLACKLISTED_DOMAINS
    )


# Orchestrators


def validate_and_normalize_query(query: str) -> QueryResult:
    """
    Run the full L1 → L2 → L3 pipeline and return a structured result.

    Downstream code should branch on `result.is_valid`; the `reasons` tuple
    is intended for structured logs / API error messages.
    """
    reasons: list[str] = []
    is_safe = is_safe_query(query)
    if not is_safe:
        reasons.append("failed safety checks")

    is_relevant = is_safe and is_real_estate_query(query)
    if is_safe and not is_relevant:
        reasons.append("off-topic for real-estate domain")

    normalized = normalize_query(query) if is_safe else (query or "")
    return QueryResult(
        original=query,
        normalized=normalized,
        is_safe=is_safe,
        is_relevant=is_relevant,
        reasons=tuple(reasons),
    )


def validate_url(url: str) -> URLResult:
    """Run R1 + R2 on a single URL and return a structured result."""
    meaningful = has_meaningful_content(url)
    blacklisted = is_blacklisted(url)
    reasons: list[str] = []
    if not meaningful:
        reasons.append("no meaningful path/query/fragment")
    if blacklisted:
        reasons.append("blacklisted domain")
    return URLResult(
        url=url,
        is_meaningful=meaningful,
        is_blacklisted=blacklisted,
        reasons=tuple(reasons),
    )


def filter_blacklisted_urls(urls: Iterable[str]) -> list[str]:
    """
    Return only URLs that pass *both* URL checks (meaningful content AND
    not blacklisted). Single parse per URL.
    """
    logger.info(
        "filter_blacklisted_urls: filtering %d candidate(s)",
        len(list(urls)) if hasattr(urls, "__len__") else -1,
    )
    kept: list[str] = []
    for url in urls:
        result = validate_url(url)
        if result.is_usable:
            kept.append(url)
        else:
            logger.debug(
                "filter_blacklisted_urls: drop %r (%s)", url, ", ".join(result.reasons)
            )
    return kept
