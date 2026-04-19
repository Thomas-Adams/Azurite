import os
import asyncio

from api import jobs
from api.websocket import manager


async def run_scan(job_id: str, folder: str, extensions: list[str] ):
    job = jobs[job_id]
    job["status"] = "running"

    all_files = []
    for root, _, files in os.walk(folder):
        for file in files:
            if os.path.splitext(file)[1].lower() in extensions:
                all_files.append(os.path.join(root, file))

    job["total_images"] = len(all_files)
    await manager.send_progress(job_id, job.copy())

    for index, file_path in enumerate(all_files, start=1):
        try:
            job["current_image"] = file_path

            # simulate actual work
            await asyncio.sleep(0.1)

            job["scanned_images"] = index
            job["scanned_files"].append(file_path)
            job["progress_percent"] = int(index / job["total_images"] * 100) if job["total_images"] else 100

            await manager.send_progress(job_id, {
                "job_id": job_id,
                "status": job["status"],
                "total_images": job["total_images"],
                "scanned_images": job["scanned_images"],
                "current_image": job["current_image"],
                "progress_percent": job["progress_percent"],
            })

        except Exception as e:
            job["errors"].append({"file": file_path, "error": str(e)})

    job["status"] = "finished"
    job["current_image"] = None
    job["progress_percent"] = 100
    await manager.send_progress(job_id, job.copy())