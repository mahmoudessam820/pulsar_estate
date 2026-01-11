from app.providers.ai.ollama import OllamaCloudProvider


def test_ai_provider_parses_json(monkeypatch):
    class MockResponse:
        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": '{"summary":"ok","key_trends":[],"market_sentiment":"neutral","evidence":[]}'
                        }
                    }
                ]
            }

        def raise_for_status(self):
            pass

    def mock_post(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr("httpx.post", mock_post)

    provider = OllamaCloudProvider()
    result = provider.analyze(
        [
            {"url": "x", "content": "test", "title": "t"},
            {"url": "y", "content": "test2", "title": "t2"},
        ]
    )

    assert result["summary"] == "ok"
