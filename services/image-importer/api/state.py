from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

IMAGE_ROOT = "/your/image/root"   # set via env var in production
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
IMAGE_ROOT = "/"

jobs: dict[str, dict] = {}
latest_job_id: str | None = None

app.mount("/images", StaticFiles(directory=IMAGE_ROOT), name="images")