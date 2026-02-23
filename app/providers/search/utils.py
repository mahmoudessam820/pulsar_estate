from urllib.parse import urlparse


def normalize_query(query: str) -> str:
    """
    Normalize and enrich search queries for real estate intelligence.
    """

    base_keywords = [
        "Dubai real estate",
        "property market",
        "Dubai house for sale",
        "apartments for sale Dubai",
        "off-plan property UAE",
        "luxury real estate",
        "prices",
        "investment",
        "trends",
        "United Arab Emirates",
        "Abu Dhabi",
        "property market growth in United Arab Emirates",
        "House prices",
        "house prices in Abu Dhabi",
        "house prices in United Arab Emirates",
        "interest rates in United Arab Emirates",
        "investment in property",
        "Price history",
        "Prices fell",
        "Prices rose",
        "Property boom",
        "Property bubble",
        "property in Abu Dhabi",
        "property in United Arab Emirates",
        "Property news",
        "Property prices",
        "Real Estate In",
        "rent",
        "rental income",
        "rental yield",
        "residential",
        "Dubai",
        "UAE",
        "Abu Dhabi",
        "Property in Dubai",
        "Dubai real estate",
        "Villas for sale",
        "Dubai Residential Property Report Q3",
        "UAE Luxury Residential Real Estate Market",
        "UAE Luxury Residential Real Estate Market Size",
        "UAE Luxury Residential Real Estate Market Share",
        "UAE Luxury Residential Real",
        "Estate Market Analysis",
        "UAE Luxury Residential Real Estate Market Trends",
        "UAE Luxury Residential Real Estate Market Report",
        "UAE Luxury Residential Real Estate Market Research",
        "UAE Luxury Residential Real Estate Industry",
        "UAE Luxury Residential Real Estate Industry Report",
        "Dubai Land",
        "Valuation",
        "Transaction",
        "DLD",
        "Service Charge",
        "Rental Index",
        "Land Status",
        "Project Status",
        "Ejari",
        "dubai property market forecast",
        "dubai real estate prices",
        "dubai property investment opportunities",
        "dubai property investment",
        "dubai housing market trends",
        "buy property in dubai",
        "dubai real estate outlook",
        "dubai real estate market analysis",
    ]

    return f"{query} " + " ".join(base_keywords)


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
