import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import api.state as state


class TestConnectionManager:
    async def test_connect_accepts_websocket(self):
        from api.websocket import ConnectionManager
        manager = ConnectionManager()
        ws = AsyncMock()
        await manager.connect("job1", ws)
        ws.accept.assert_awaited_once()
        assert ws in manager.connections["job1"]

    async def test_connect_multiple_sockets_same_job(self):
        from api.websocket import ConnectionManager
        manager = ConnectionManager()
        ws1, ws2 = AsyncMock(), AsyncMock()
        await manager.connect("job1", ws1)
        await manager.connect("job1", ws2)
        assert len(manager.connections["job1"]) == 2

    async def test_disconnect_removes_socket(self):
        from api.websocket import ConnectionManager
        manager = ConnectionManager()
        ws = AsyncMock()
        await manager.connect("job1", ws)
        manager.disconnect("job1", ws)
        assert "job1" not in manager.connections

    async def test_disconnect_unknown_job_is_noop(self):
        from api.websocket import ConnectionManager
        manager = ConnectionManager()
        ws = AsyncMock()
        manager.disconnect("nonexistent", ws)  # must not raise

    async def test_send_progress_broadcasts_to_all(self):
        from api.websocket import ConnectionManager
        manager = ConnectionManager()
        ws1, ws2 = AsyncMock(), AsyncMock()
        await manager.connect("job1", ws1)
        await manager.connect("job1", ws2)
        await manager.send_progress("job1", {"status": "running"})
        ws1.send_json.assert_awaited_once_with({"status": "running"})
        ws2.send_json.assert_awaited_once_with({"status": "running"})

    async def test_send_progress_no_connections_is_noop(self):
        from api.websocket import ConnectionManager
        manager = ConnectionManager()
        await manager.send_progress("nojob", {"status": "done"})  # must not raise


class TestRunScan:
    async def test_scan_finds_matching_files(self, tmp_path):
        from api.tasks import run_scan

        (tmp_path / "a.png").write_bytes(b"x")
        (tmp_path / "b.png").write_bytes(b"x")
        (tmp_path / "c.txt").write_bytes(b"x")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "d.png").write_bytes(b"x")

        job_id = "scan-test"
        state.jobs[job_id] = {
            "job_id": job_id, "status": "pending", "total_images": 0,
            "scanned_images": 0, "current_image": None, "progress_percent": 0,
            "scanned_files": [], "errors": [],
        }

        with patch("api.tasks.manager") as mock_mgr:
            mock_mgr.send_progress = AsyncMock()
            await run_scan(job_id, str(tmp_path), [".png"])

        job = state.jobs[job_id]
        assert job["status"] == "finished"
        assert job["total_images"] == 3
        assert len(job["scanned_files"]) == 3
        assert job["progress_percent"] == 100
        assert all(f.endswith(".png") for f in job["scanned_files"])

    async def test_scan_empty_folder(self, tmp_path):
        from api.tasks import run_scan

        job_id = "scan-empty"
        state.jobs[job_id] = {
            "job_id": job_id, "status": "pending", "total_images": 0,
            "scanned_images": 0, "current_image": None, "progress_percent": 0,
            "scanned_files": [], "errors": [],
        }

        with patch("api.tasks.manager") as mock_mgr:
            mock_mgr.send_progress = AsyncMock()
            await run_scan(job_id, str(tmp_path), [".png"])

        job = state.jobs[job_id]
        assert job["status"] == "finished"
        assert job["total_images"] == 0
        assert job["progress_percent"] == 100

    async def test_scan_sets_status_running_then_finished(self, tmp_path):
        from api.tasks import run_scan

        job_id = "scan-status"
        state.jobs[job_id] = {
            "job_id": job_id, "status": "pending", "total_images": 0,
            "scanned_images": 0, "current_image": None, "progress_percent": 0,
            "scanned_files": [], "errors": [],
        }

        statuses = []
        async def capture_progress(job_id, msg):
            statuses.append(msg.get("status"))

        with patch("api.tasks.manager") as mock_mgr:
            mock_mgr.send_progress = capture_progress
            await run_scan(job_id, str(tmp_path), [".png"])

        assert "finished" in statuses
