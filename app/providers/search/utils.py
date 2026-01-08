def normalize_query(query: str) -> str:
    """
    Normalize and enrich search queries for real estate intelligence.
    """

    base_keywords = [
        "Dubai real estate",
        "property market",
        "prices",
        "investment",
        "trends",
    ]

    return f"{query} " + " ".join(base_keywords)
