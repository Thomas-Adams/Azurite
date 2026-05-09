"""Targeted tests to cover remaining low-hanging-fruit lines."""
import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

from api.main import app
from api.state import ALLOWED_EXTENSIONS, STATIC_FOLDERS


class TestModelsImport:
    def test_lora_image_model_importable(self):
        from models.lora_image import LoraImage
        assert LoraImage.__tablename__ == "lora_image"

    def test_workflow_model_importable(self):
        from models.workflow import Workflow
        assert Workflow.__tablename__ == "workflow"


class TestUtilsGetCreated:
    def test_returns_datetime_for_real_file(self, tmp_path):
        from utils import get_created
        import datetime
        f = tmp_path / "f.txt"
        f.write_bytes(b"x")
        result = get_created(f)
        assert isinstance(result, datetime.datetime)

    def test_returns_now_when_stat_raises_attribute_error(self, tmp_path):
        from unittest.mock import patch
        from utils import get_created
        import datetime
        f = tmp_path / "f.txt"
        f.write_bytes(b"x")
        with patch.object(Path, "stat", side_effect=AttributeError):
            result = get_created(f)
        assert isinstance(result, datetime.datetime)


class TestListingRoutes:
    async def test_listing_root_returns_html(self, tmp_path):
        fake_folder = tmp_path / "myimages"
        fake_folder.mkdir()

        with patch("api.app.STATIC_FOLDERS", [str(fake_folder)]):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/listing")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    async def test_listing_root_empty_when_no_folders(self):
        with patch("api.app.STATIC_FOLDERS", []):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/listing")
        assert response.status_code == 200

    async def test_listing_path_404_for_unknown_top_folder(self):
        with patch("api.app.STATIC_FOLDERS", []):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/listing/nonexistent")
        assert response.status_code == 404

    async def test_listing_path_returns_html_for_known_folder(self, tmp_path):
        fake_folder = tmp_path / "bucket"
        fake_folder.mkdir()
        (fake_folder / "img.png").write_bytes(b"x")

        with patch("api.app.STATIC_FOLDERS", [str(fake_folder)]):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/listing/bucket")

        assert response.status_code == 200

    async def test_listing_path_404_for_file_not_dir(self, tmp_path):
        fake_folder = tmp_path / "bucket"
        fake_folder.mkdir()

        with patch("api.app.STATIC_FOLDERS", [str(fake_folder)]):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/listing/bucket/nonexistent-sub")

        assert response.status_code == 404
