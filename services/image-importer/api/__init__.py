from uuid import uuid4

from fastapi import FastAPI, BackgroundTasks

from api.tasks import run_scan
from dto.request import ScanImagesRequestDto
from dto.response import StartedJobResponseDto
from services.image_importer import start_import
app = FastAPI()

jobs: dict[str, dict] = {}


@app.post("/scan")
async def scan_image_director_job(request: ScanImagesRequestDto, background_tasks: BackgroundTasks):
     start_import(request.directory)
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

     background_tasks.add_task(run_scan, job_id, request.folder, request.extensions)
     return StartedJobResponseDto(job_id=job_id, status="pending")



