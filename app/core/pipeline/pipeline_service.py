from typing import List, Dict

from app.core.pipeline.interfaces import (
    SearchProvider,
    CrawlProvider,
    AIProvider,
)


class PipelineService:
    def __init__(
        self,
        search_provider: SearchProvider,
        crawl_provider: CrawlProvider,
        ai_provider: AIProvider,
    ):
        self.search_provider = search_provider
        self.crawl_provider = crawl_provider
        self.ai_provider = ai_provider

    def run(self, query: str) -> Dict:
        urls = self.search_provider.search(query)

        documents: List[Dict] = []

        for url in urls:
            doc = self.crawl_provider.crawl(url)
            documents.append(doc)

        insights = self.ai_provider.analyze(documents)

        return insights
