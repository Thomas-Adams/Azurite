import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport

from api.main import app


class TestSearchEndpoint:
    async def test_returns_hits(self):
        mock_index = MagicMock()
        mock_index.search.return_value = {
            "estimatedTotalHits": 1,
            "hits": [{"id": "abc", "filename": "test.png", "rating": 1}],
        }

        with patch("api.app.get_index", return_value=mock_index):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/search", params={"q": "cat"})

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["query"] == "cat"
        assert len(data["hits"]) == 1
        assert data["hits"][0]["filename"] == "test.png"

    async def test_passes_limit_and_offset(self):
        mock_index = MagicMock()
        mock_index.search.return_value = {"estimatedTotalHits": 0, "hits": []}

        with patch("api.app.get_index", return_value=mock_index):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                await client.get("/api/search", params={"q": "dog", "limit": 5, "offset": 10})

        mock_index.search.assert_called_once_with("dog", {"limit": 5, "offset": 10})

    async def test_empty_query_rejected(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/search", params={"q": ""})
        assert response.status_code == 422

    async def test_missing_query_rejected(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/search")
        assert response.status_code == 422

    async def test_empty_results(self):
        mock_index = MagicMock()
        mock_index.search.return_value = {"estimatedTotalHits": 0, "hits": []}

        with patch("api.app.get_index", return_value=mock_index):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/search", params={"q": "noresults"})

        assert response.status_code == 200
        assert response.json()["total"] == 0
        assert response.json()["hits"] == []
