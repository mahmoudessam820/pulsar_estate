from app.core.pipeline.pipeline_service import PipelineService


class MockSearch:
    def search(self, query: str):
        return ["url1", "url2"]


class MockCrawler:
    def crawl(self, url: str):
        return {"url": url, "content": "text"}


class MockAI:
    def analyze(self, documents):
        return {"summary": "market insight", "sources": len(documents)}


def test_pipeline_runs():
    pipeline = PipelineService(
        search_provider=MockSearch(),
        crawl_provider=MockCrawler(),
        ai_provider=MockAI(),
    )
    
    result = pipeline.run("Dubai real estate")

    assert result["sources"] == 2
