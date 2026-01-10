from app.providers.crawler.crawl4ai import Crawl4AIProvider


def test_crawl_success(monkeypatch):
    class MockAsyncCrawler:
        async def arun(self, url):
            class Result:
                markdown = "Test content"
                metadata = {
                    "title": "Test Title",
                    "published_date": "2024-01-01",
                    "author": "Author",
                }

            return Result()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    monkeypatch.setattr(
        "app.providers.crawler.crawl4ai.AsyncWebCrawler",
        lambda timeout: MockAsyncCrawler(),
    )

    provider = Crawl4AIProvider()
    result = provider.crawl("https://example.com")

    assert result["content"] == "Test content"
    assert result["error"] is None


def test_crawl_failure(monkeypatch):
    class MockAsyncCrawler:
        async def arun(self, url):
            raise Exception("Boom")

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    monkeypatch.setattr(
        "app.providers.crawler.crawl4ai.AsyncWebCrawler",
        lambda timeout: MockAsyncCrawler(),
    )

    provider = Crawl4AIProvider()
    result = provider.crawl("https://example.com")

    assert result["content"] is None
    assert "Boom" in result["error"]
