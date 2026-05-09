import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from api.main import app

FOLDER = "vorlagen-tsukuyomi/vorlagen-bilder"


class TestGetReviewedHashes:
    async def test_empty_input_returns_empty_set(self):
        from services.image_importer import get_reviewed_hashes
        result = await get_reviewed_hashes([])
        assert result == set()

    async def test_returns_set_of_known_hashes(self):
        from services.image_importer import get_reviewed_hashes

        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([("abc123",), ("def456",)]))
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_ctx = MagicMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=None)

        with patch("services.image_importer.async_session_factory", return_value=mock_ctx):
            result = await get_reviewed_hashes(["abc123", "def456", "notfound"])

        assert "abc123" in result
        assert "def456" in result
        assert "notfound" not in result


class TestFetchBatchAlreadyReviewed:
    async def test_already_reviewed_field_present(self, tmp_path):
        from PIL import Image as PILImage
        img = PILImage.new("RGB", (10, 10))
        img.save(tmp_path / "test.png")

        with (
            patch("api.app.IMAGE_ROOT", str(tmp_path)),
            patch("api.app.get_reviewed_hashes", new=AsyncMock(return_value=set())),
        ):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/fetch-image-batch", params={"folder": "", "page": 1, "size": 10})

        assert response.status_code == 200
        items = response.json()["content"]
        assert len(items) == 1
        assert "already_reviewed" in items[0]
        assert items[0]["already_reviewed"] is False

    async def test_already_reviewed_true_when_hash_known(self, tmp_path):
        from PIL import Image as PILImage
        from utils.image_sha import sha256_of_file
        img = PILImage.new("RGB", (10, 10))
        img.save(tmp_path / "test.png")
        file_hash = sha256_of_file(str(tmp_path / "test.png"))

        with (
            patch("api.app.IMAGE_ROOT", str(tmp_path)),
            patch("api.app.get_reviewed_hashes", new=AsyncMock(return_value={file_hash})),
        ):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/fetch-image-batch", params={"folder": "", "page": 1, "size": 10})

        items = response.json()["content"]
        assert items[0]["already_reviewed"] is True
