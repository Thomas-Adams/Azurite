import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from api.main import app

VALID_PAYLOAD = {
    "hash": "abc123def456",
    "path": "/mnt/windows/stablediffusion/vorlagen-tsukuyomi/vorlagen-bilder/test.png",
    "bucket_name": "tsukuyomi",
    "rating": 1,
    "comment": "Very good, almost no flaws",
}


class TestReviewEndpoint:
    async def test_success_returns_200(self):
        with patch("api.app.upload_and_review_image", new=AsyncMock(return_value=None)):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/review", json=VALID_PAYLOAD)
        assert response.status_code == 200

    async def test_success_body(self):
        with patch("api.app.upload_and_review_image", new=AsyncMock(return_value=None)):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/review", json=VALID_PAYLOAD)
        data = response.json()
        assert data["success"] is True
        assert data["errors"] == []

    async def test_upload_called_with_dto(self):
        mock = AsyncMock(return_value=None)
        with patch("api.app.upload_and_review_image", new=mock):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                await client.post("/review", json=VALID_PAYLOAD)
        mock.assert_called_once()
        dto = mock.call_args[0][0]
        assert dto.path == VALID_PAYLOAD["path"]
        assert dto.bucket_name == VALID_PAYLOAD["bucket_name"]
        assert dto.rating == VALID_PAYLOAD["rating"]

    async def test_error_returns_success_false(self):
        with patch("api.app.upload_and_review_image", new=AsyncMock(side_effect=Exception("DB connection failed"))):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/review", json=VALID_PAYLOAD)
        data = response.json()
        assert data["success"] is False
        assert len(data["errors"]) == 1
        assert "DB connection failed" in data["errors"][0]["message"]

    async def test_error_still_returns_200(self):
        with patch("api.app.upload_and_review_image", new=AsyncMock(side_effect=Exception("oops"))):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/review", json=VALID_PAYLOAD)
        assert response.status_code == 200

    async def test_missing_required_fields_returns_422(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/review", json={"rating": 1})
        assert response.status_code == 422

    async def test_invalid_rating_type_returns_422(self):
        payload = {**VALID_PAYLOAD, "rating": "not-a-number"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/review", json=payload)
        assert response.status_code == 422
