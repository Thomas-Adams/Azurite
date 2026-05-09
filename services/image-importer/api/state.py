import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from config import settings
from search.client import ensure_index


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_index()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
IMAGE_ROOT = settings.image_root
SUB_FOLDERS = ["vorlagen-red-elf", "vorlagen-tsukuyomi"]

STATIC_FOLDERS = [
    os.path.join(IMAGE_ROOT, sub)
    for sub in SUB_FOLDERS
]

jobs: dict[str, dict] = {}
latest_job_id: str | None = None

# Mount each subfolder individually
for folder in STATIC_FOLDERS:
    if os.path.isdir(folder):
        name = os.path.basename(folder)
        app.mount(f"/static/{name}", StaticFiles(directory=folder), name=f"static-{name}")
