import hashlib
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, Query
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
import mimetypes
import os

from api.state import app, ALLOWED_EXTENSIONS, jobs, IMAGE_ROOT
from api.tasks import run_scan
from datetime import UTC, datetime

from dto.request.ScanImagesRequestDto import ScanImagesRequestDto
from dto.response.StartedJobResponseDto import StartedJobResponseDto


def folder_to_job_id(directory: str) -> str:
    # Stable, URL-safe ID derived from the folder path
    return hashlib.sha256(directory.encode()).hexdigest()[:16]
@app.get("/file")
def serve_file(path: str):
    ext = os.path.splitext(path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(403, "File type not allowed")
    if not os.path.isfile(path):
        raise HTTPException(404, "File not found")
    mime, _ = mimetypes.guess_type(path)
    return FileResponse(path, media_type=mime or "application/octet-stream")

@app.post("/scan", response_model=StartedJobResponseDto)
async def scan_images_job(request: ScanImagesRequestDto, background_tasks: BackgroundTasks):
     global latest_job_id
     job_id = folder_to_job_id(request.directory)
     latest_job_id = job_id
     jobs[job_id] = {
          "job_id": job_id,
          "directory": request.directory,
          "status": "pending",
          "started_at": datetime.now(UTC).isoformat(),
          "total_images": 0,
          "scanned_images": 0,
          "current_image": None,
          "progress_percent": 0,
          "scanned_files": [],
          "errors": [],
     }# ← correct field names from ScanImagesRequestDto
     background_tasks.add_task(run_scan, job_id, request.directory, request.image_types)
     return StartedJobResponseDto(job_id=job_id, status="pending")

@app.get("/scan-jobs/latest/files")
def get_latest_files(offset: int = Query(0), limit: int = Query(10)):
    if not latest_job_id or latest_job_id not in jobs:
        raise HTTPException(404, "No jobs run yet")
    return get_files_for_job(latest_job_id, offset, limit)

@app.get("/scan-jobs/{job_id}/files")
def get_scanned_files(job_id: str, offset: int = Query(0), limit: int = Query(10)):
    return get_files_for_job(job_id, offset, limit)








# Serve image files statically so the frontend can load them by URL



def get_files_for_job(job_id: str, offset: int = 0, limit: int = 10):
    """
    Paginated list of scanned files — this is what the carousel fetches,
    10 at a time, as the user scrolls through.
    """
    job = jobs.get(job_id)
    if not job:
        return {"error": "job not found"}
    all_files = job.get("scanned_files", [])
    page = all_files[offset: offset + limit]
    return {
        "job_id": job_id,
        "total": len(all_files),
        "offset": offset,
        "files": [
            {
                "index": offset + i,
                # Return a URL the browser can fetch directly from /images/...
                "url": "/images/" + os.path.relpath(f, IMAGE_ROOT).replace("\\", "/"),
                "filename": os.path.basename(f),
                "full_path": f,
            }
            for i, f in enumerate(page)
        ],
        "hasMore": offset + limit < len(all_files),
    }



@app.post("/scan", response_model=StartedJobResponseDto)
async def scan_images_job(request: ScanImagesRequestDto, background_tasks: BackgroundTasks):
    job_id = str(uuid4())
    jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "total_images": 0,
        "scanned_images": 0,
        "current_image": None,
        "progress_percent": 0,
        "scanned_files": [],
        "errors": [],
    }
    # ← correct field names from ScanImagesRequestDto
    background_tasks.add_task(run_scan, job_id, request.directory, request.image_types)
    return StartedJobResponseDto(job_id=job_id, status="pending")


@app.get("/scan-jobs/{job_id}")
def get_job(job_id: str):
    """Poll job status (alternative to WebSocket)."""
    return jobs.get(job_id, {"error": "not found"})


@app.get("/scan-jobs/{job_id}/files")
def get_scanned_files(job_id: str, offset: int = Query(0), limit: int = Query(10)):
    """
    Paginated list of scanned files — this is what the carousel fetches,
    10 at a time, as the user scrolls through.
    """
    job = jobs.get(job_id)
    if not job:
        return {"error": "job not found"}
    all_files = job.get("scanned_files", [])
    page = all_files[offset: offset + limit]
    return {
        "job_id": job_id,
        "total": len(all_files),
        "offset": offset,
        "files": [
            {
                "index": offset + i,
                # Return a URL the browser can fetch directly from /images/...
                "url": "/images/" + os.path.relpath(f, IMAGE_ROOT).replace("\\", "/"),
                "filename": os.path.basename(f),
                "full_path": f,
            }
            for i, f in enumerate(page)
        ],
        "hasMore": offset + limit < len(all_files),
    }


@app.post("/import")
async def import_images(paths: list[str]):
    """Receive list of full_path strings the user checked, import them to DB."""
    from services.image_importer import read_png_metadata, read_png_sidecar, import_one
    from pathlib import Path
    results = {"imported": [], "errors": []}
    for path in paths:
        p = Path(path)
        parsed = read_png_metadata(p) or read_png_sidecar(p)
        if parsed:
            try:
                await import_one(parsed)
                results["imported"].append(path)
            except Exception as e:
                results["errors"].append({"path": path, "error": str(e)})
        else:
            results["errors"].append({"path": path, "error": "no metadata found"})
    return results