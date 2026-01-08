from app.providers.search.duckduckgo import DuckDuckGoSearchProvider


def test_search_uses_normalized_query(monkeypatch):
    captured_query = {}

    class MockDDGS:
        def text(self, query, max_results):
            captured_query["value"] = query
            print(captured_query)
            return [{"href": "https://example.com"}]

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(
        "app.providers.search.duckduckgo.DDGS",
        MockDDGS,
    )

    provider = DuckDuckGoSearchProvider(max_results=1)
    provider.search("test")

    assert "Dubai real estate" in captured_query["value"]
