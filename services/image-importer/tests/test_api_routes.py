import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
from httpx import AsyncClient, ASGITransport

from api.main import app
import api.state as state


class TestHelpers:
    def test_folder_to_job_id_deterministic(self):
        from api.app import folder_to_job_id
        assert folder_to_job_id("/foo/bar") == folder_to_job_id("/foo/bar")

    def test_folder_to_job_id_different_inputs(self):
        from api.app import folder_to_job_id
        assert folder_to_job_id("/foo") != folder_to_job_id("/bar")

    def test_human_size_bytes(self):
        from api.app import human_size
        assert human_size(512) == "512 B"

    def test_human_size_kb(self):
        from api.app import human_size
        assert human_size(2048) == "2 KB"

    def test_human_size_mb(self):
        from api.app import human_size
        assert human_size(2 * 1024 * 1024) == "2 MB"

    def test_build_listing_finds_images(self, tmp_path):
        from api.app import build_listing
        (tmp_path / "a.png").write_bytes(b"x")
        (tmp_path / "subdir").mkdir()
        result = build_listing(str(tmp_path), "/listing/root", "/static/root")
        assert any(img["name"] == "a.png" for img in result["images"])
        assert any(f["name"] == "subdir" for f in result["folders"])

    def test_build_listing_excludes_non_images(self, tmp_path):
        from api.app import build_listing
        (tmp_path / "file.txt").write_bytes(b"x")
        result = build_listing(str(tmp_path), "/l", "/s")
        assert result["images"] == []


class TestFileServing:
    async def test_serves_existing_png(self, tmp_path):
        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG\r\n")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/file", params={"path": str(img)})

        assert response.status_code == 200

    async def test_rejects_disallowed_extension(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_bytes(b"hello")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/file", params={"path": str(f)})

        assert response.status_code == 403

    async def test_returns_404_for_missing_file(self, tmp_path):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/file", params={"path": str(tmp_path / "nope.png")})

        assert response.status_code == 404


class TestScanRoutes:
    async def test_post_scan_returns_job_id(self):
        with patch("api.app.run_scan"):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/scan", json={"directory": "/some/dir"})

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"

    async def test_get_job_returns_not_found_for_unknown(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/scan-jobs/unknownjobid")
        assert response.json() == {"error": "not found"}

    async def test_get_job_returns_state_for_known(self):
        state.jobs["testjob"] = {"job_id": "testjob", "status": "done"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/scan-jobs/testjob")
        assert response.json()["status"] == "done"

    async def test_get_latest_files_404_when_no_jobs(self):
        state.latest_job_id = None
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/scan-jobs/latest/files")
        assert response.status_code == 404

    async def test_get_job_files_returns_paginated(self):
        state.jobs["filejob"] = {
            "job_id": "filejob",
            "status": "done",
            "scanned_files": ["/img/a.png", "/img/b.png"],
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/scan-jobs/filejob/files", params={"offset": 0, "limit": 1})
        data = response.json()
        assert data["total"] == 2
        assert len(data["files"]) == 1


class TestImportRoute:
    async def test_import_calls_import_one(self, tmp_path):
        f = tmp_path / "img.png"
        f.write_bytes(b"x")

        with (
            patch("api.app.read_png_metadata", return_value={"some": "data"}),
            patch("api.app.read_png_sidecar", return_value=None),
            patch("api.app.import_one", new=AsyncMock()),
        ):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/import", json=[str(f)])

        assert response.status_code == 200
        data = response.json()
        assert str(f) in data["imported"]

    async def test_import_reports_error_when_no_metadata(self, tmp_path):
        f = tmp_path / "img.png"
        f.write_bytes(b"x")

        with (
            patch("api.app.read_png_metadata", return_value=None),
            patch("api.app.read_png_sidecar", return_value=None),
        ):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/import", json=[str(f)])

        data = response.json()
        assert str(f) in [e["path"] for e in data["errors"]]
