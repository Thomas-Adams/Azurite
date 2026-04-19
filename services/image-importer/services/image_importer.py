import glob
import os
import json
from PIL import Image
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session_factory
from models.image_assets import ImageAssets
from utils import get_created
from utils.image_sha import sha256_of_file


def scan_images(directory):
    patterns = ["**/*.jpg", "**/*.jpeg", "**/*.png", "**/*.webp"]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(directory, pattern), recursive=True))
    return files


def read_png_metadata(filename: Path) -> Optional[Dict[str, Any]]:
    img = Image.open(filename)

    if img.info is not None:
        metadata = img.info  # dict
        return {
            "filename": filename,  # or filename.name
            **metadata
        }
    return None


def read_png_sidecar(filename: Path) -> Optional[Dict[str, Any]]:
    sidecar_path = filename.stem + ".json"
    if os.path.exists(sidecar_path):
        with open(sidecar_path, "r", encoding="utf-8") as f:
            return {
                "filename": filename,  # or filename.name
                **json.load(f)
            }
    return None


async def save_image_asset(session: AsyncSession, data: Dict[str, Any], filename: Path) -> ImageAssets:
    model = ImageAssets()
    model.model_name = data.get("model")
    model.loras = data.get("loras")
    model.positive_prompt = data.get("positive_prompts").join(", ")
    model.negative_prompt = data.get("positive_prompts").join(", ")
    model.styles = data.get("styles").join(", ")
    model.image_width = data.get("image_width")
    model.image_height = data.get("image_height")
    model.samplers = data.get("sampler_name")
    model.cfg = data.get("cfg")
    model.steps = int(data.steps) if data.get("steps") is not None else None
    model.scheduler = data.get("scheduler")
    model.seed = int(data.get("seed")) if data.get("seed") is not None else None
    model.file_name = filename.name
    model.path = filename.parent
    model.mimetype = "image/png"
    model.created_at = datetime.now()
    model.aspect_ratio = data.get("image_width") / data.get("image_height") if data.get("image_width") and data.get("image_height") else None
    model.file_size = os.path.getsize(filename)
    model.sha256 = sha256_of_file(str(filename))
    model.created_at = get_created(filename)

    session.add(model)
    await session.flush()  # gets PK from DB without committing yet
    await session.refresh(model)
    return model


async def import_one(parsed: dict):
    async with async_session_factory() as session:
        try:
            asset = await save_image_asset(session, parsed, parsed.filename)
            await session.commit()
            return asset
        except Exception:
            await session.rollback()
            raise


def start_import(images_dir: str):
    files = scan_images(images_dir)
    print(f"Found {len(files)} images")
    for file in files:
        if file.lower().endswith(".png"):
            result = read_png_metadata(file)
            if result is not None:
                print(f"Importing metadata {file}")
                import_one(result)
            else:
                result = read_png_sidecar(file)
                if result is not None:
                    print(f"Importing sidecar {file}")
                    import_one(result)
