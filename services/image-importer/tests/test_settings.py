import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from api.main import app


class TestSettingsService:
    async def test_get_settings_returns_existing_row(self):
        from services.settings_service import get_settings

        existing = MagicMock()
        existing.image_root = "/data/images"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=existing)
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_ctx = MagicMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=None)

        with patch("services.settings_service.async_session_factory", return_value=mock_ctx):
            result = await get_settings()

        assert result.image_root == "/data/images"

    async def test_get_settings_seeds_default_when_no_row(self):
        from services.settings_service import get_settings

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.refresh = AsyncMock(side_effect=lambda obj: None)
        mock_ctx = MagicMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("services.settings_service.async_session_factory", return_value=mock_ctx),
            patch("services.settings_service.env_settings") as mock_env,
        ):
            mock_env.image_root = "/default/root"
            result = await get_settings()

        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()

    async def test_update_settings_updates_existing_row(self):
        from services.settings_service import update_settings

        existing = MagicMock()
        existing.image_root = "/old/path"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=existing)
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.refresh = AsyncMock(side_effect=lambda obj: None)
        mock_ctx = MagicMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=None)

        with patch("services.settings_service.async_session_factory", return_value=mock_ctx):
            await update_settings("/new/path")

        assert existing.image_root == "/new/path"
        mock_session.commit.assert_awaited_once()

    async def test_update_settings_creates_row_when_none(self):
        from services.settings_service import update_settings

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.refresh = AsyncMock(side_effect=lambda obj: None)
        mock_ctx = MagicMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=None)

        with patch("services.settings_service.async_session_factory", return_value=mock_ctx):
            await update_settings("/brand/new")

        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()


class TestSettingsEndpoints:
    async def test_get_settings_endpoint(self):
        mock_row = MagicMock()
        mock_row.image_root = "/mnt/images"

        with patch("api.app.get_settings", new=AsyncMock(return_value=mock_row)):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/settings")

        assert response.status_code == 200
        assert response.json() == {"image_root": "/mnt/images"}

    async def test_put_settings_endpoint(self):
        mock_row = MagicMock()
        mock_row.image_root = "/new/path"

        with patch("api.app.update_settings", new=AsyncMock(return_value=mock_row)):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.put("/api/settings", json={"image_root": "/new/path"})

        assert response.status_code == 200
        assert response.json() == {"image_root": "/new/path"}

    async def test_put_settings_requires_image_root(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put("/api/settings", json={})
        assert response.status_code == 422
