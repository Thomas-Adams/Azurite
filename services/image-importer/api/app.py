import hashlib
import mimetypes
import os
from datetime import UTC, datetime, timezone
from pathlib import Path as FSPath, Path  # ← alias to avoid clash with fastapi.Path

from fastapi import BackgroundTasks, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException
from starlette.responses import FileResponse

import api.state as state
from api.state import app, ALLOWED_EXTENSIONS, STATIC_FOLDERS, IMAGE_ROOT
from api.tasks import run_scan
from dto.request.request_dto import ScanImagesRequestDto
from dto.response.paginate import Paginated
from dto.response.response_dto import StartedJobResponseDto
from services.image_importer import image_metadata
from utils.image_sha import sha256_of_file
from utils.image_utils import read_image_size

TEMPLATES_DIR = FSPath(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000")


# ── helpers ──────────────────────────────────────────────────────────────────

def folder_to_job_id(directory: str) -> str:
    return hashlib.sha256(directory.encode()).hexdigest()[:16]


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def build_listing(abs_path: str, link_base: str, static_base: str) -> dict:
    folders, images = [], []
    for entry in sorted(os.scandir(abs_path), key=lambda e: (not e.is_dir(), e.name.lower())):
        if entry.is_dir():
            count = sum(1 for _ in os.scandir(entry.path))
            folders.append({
                "name": entry.name,
                "url": f"{link_base}/{entry.name}",
                "count": count,
            })
        elif FSPath(entry.name).suffix.lower() in ALLOWED_EXTENSIONS:
            images.append({
                "name": entry.name,
                "url": f"{static_base}/{entry.name}",
                "size_human": human_size(entry.stat().st_size),
            })
    return {"folders": folders, "images": images}


# ── listing routes ────────────────────────────────────────────────────────────

@app.get("/listing", response_class=HTMLResponse)
def listing_root(request: Request):
    folders = []
    for folder in STATIC_FOLDERS:
        if os.path.isdir(folder):
            name = os.path.basename(folder)
            count = sum(1 for _ in os.scandir(folder))
            folders.append({"name": name, "url": f"/listing/{name}", "count": count})

    return templates.TemplateResponse(request, "listing.html", {
        "title": "image root",
        "breadcrumbs": [],
        "folders": folders,
        "images": [],
    })


@app.get("/listing/{rest_path:path}", response_class=HTMLResponse)
def listing_path(request: Request, rest_path: str):
    parts = FSPath(rest_path).parts
    allowed = {os.path.basename(f): f for f in STATIC_FOLDERS}

    if not parts or parts[0] not in allowed:
        raise HTTPException(status_code=404, detail="Not found")

    abs_path = os.path.realpath(os.path.join(allowed[parts[0]], *parts[1:]))
    root = os.path.realpath(allowed[parts[0]])

    if not abs_path.startswith(root):
        raise HTTPException(status_code=403, detail="Forbidden")
    if not os.path.isdir(abs_path):
        raise HTTPException(status_code=404, detail="Not a directory")

    breadcrumbs = [
        {"name": parts[i], "url": "/listing/" + "/".join(parts[:i + 1])}
        for i in range(len(parts))
    ]
    static_base = "/static/" + "/".join(parts)
    data = build_listing(abs_path, link_base=f"/listing/{rest_path}", static_base=static_base)

    return templates.TemplateResponse(request, "listing.html", {
        "title": rest_path,
        "breadcrumbs": breadcrumbs,
        **data,
    })


# ── file serving ──────────────────────────────────────────────────────────────

@app.get("/file")
def serve_file(path: str):
    ext = FSPath(path).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=403, detail="File type not allowed")
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File not found")
    mime, _ = mimetypes.guess_type(path)
    return FileResponse(path, media_type=mime or "application/octet-stream")


# ── scan job routes ───────────────────────────────────────────────────────────

@app.post("/scan", response_model=StartedJobResponseDto)
async def scan_images_job(request: ScanImagesRequestDto, background_tasks: BackgroundTasks):
    job_id = folder_to_job_id(request.directory)
    state.latest_job_id = job_id
    state.jobs[job_id] = {
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
    }
    background_tasks.add_task(run_scan, job_id, request.directory, request.image_types)
    return StartedJobResponseDto(job_id=job_id, status="pending")


@app.get("/scan-jobs/latest/files")
def get_latest_files(offset: int = Query(0), limit: int = Query(10)):
    if not state.latest_job_id or state.latest_job_id not in state.jobs:
        raise HTTPException(status_code=404, detail="No jobs run yet")
    return get_files_for_job(state.latest_job_id, offset, limit)


@app.get("/scan-jobs/{job_id}")
def get_job(job_id: str):
    return state.jobs.get(job_id, {"error": "not found"})


@app.get("/scan-jobs/{job_id}/files")
def get_scanned_files(job_id: str, offset: int = Query(0), limit: int = Query(10)):
    return get_files_for_job(job_id, offset, limit)


def get_files_for_job(job_id: str, offset: int = 0, limit: int = 10):
    job = state.jobs.get(job_id)
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
                "url": f"/file?path={f}",
                "filename": os.path.basename(f),
                "full_path": f,
            }
            for i, f in enumerate(page)
        ],
        "hasMore": offset + limit < len(all_files),
    }


# ── import route ──────────────────────────────────────────────────────────────

@app.post("/import")
async def import_images(paths: list[str]):
    from pathlib import Path
    from services.image_importer import read_png_metadata, read_png_sidecar, import_one
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


@app.get("/api/fetch-image-batch")
def fetch_image_batch(
        folder: str = Query(..., description="Relative path beyond IMAGE_ROOT"),
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1, le=100),
        sort: str = Query("name", pattern="^(name|size|date)$"),
):
    # Resolve and guard against path traversal
    abs_path = os.path.realpath(os.path.join(IMAGE_ROOT, folder.lstrip("/")))
    root = os.path.realpath(IMAGE_ROOT)
    if not abs_path.startswith(str(root)):
        raise HTTPException(status_code=403, detail="Path outside IMAGE_ROOT")
    if not os.path.isdir(abs_path):
        raise HTTPException(status_code=404, detail="Folder not found")

    # Collect all image files
    all_files = [
        entry for entry in os.scandir(abs_path)
        if entry.is_file() and os.path.splitext(entry.name)[1].lower() in ALLOWED_EXTENSIONS
    ]

    # Sort
    sort_keys = {
        "name": lambda e: e.name.lower(),
        "size": lambda e: e.stat().st_size,
        "date": lambda e: e.stat().st_mtime,
    }
    all_files.sort(key=sort_keys[sort])

    # Paginate
    total = len(all_files)
    total_pages = max(1, -(-total // size))  # ceiling division
    offset = (page - 1) * size
    page_files = all_files[offset: offset + size]

    from dto.response.image_dto import ImageFileDto
    return Paginated[ImageFileDto](
        page=page,
        size=size,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
        params={"folder": folder},
        content=[
            ImageFileDto(
                filename=entry.name,
                index=i,
                url=f"{BASE_URL}/file?path={entry.path}",  # ← full absolute path, served by /file
                full_path=entry.path,
                size_bytes=entry.stat().st_size,
                hash=sha256_of_file(entry.path),
                meta = image_metadata(Path(entry.path)),
                modified_at=datetime.fromtimestamp(entry.stat().st_mtime, tz=timezone.utc),
                **dict(zip(("width", "height"), read_image_size(entry.path))),
            )
            for i, entry in enumerate(page_files, start=offset)
        ])

@app.post("/api/review")
def review_image():
    pass

