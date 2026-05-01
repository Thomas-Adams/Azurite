import glob
import os
import json
from PIL import Image
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import TypeAdapter
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session_factory
from models.generation import Generation
from models.image import Image as ModelImage
from models.lora import Lora
from models.meta_data import MetaData
from models.review import Review
from models.storage import Storage
from utils import get_created
from utils.excerpt_parser import extract_comfyui_essentials
from utils.image_sha import sha256_of_file
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


def scan_images(directory):
    patterns = ["**/*.jpg", "**/*.jpeg", "**/*.png", "**/*.webp"]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(directory, pattern), recursive=True))
    return files


def read_png_metadata(filename: Path) -> Optional[Dict[str, Any]]:
    try:
        img = Image.open(filename)
        raw = img.info or {}
        workflow_raw = raw.get("workflow")
        prompt_raw = raw.get("prompt")
        workflow = json.loads(workflow_raw) if workflow_raw else None
        prompt = json.loads(prompt_raw) if prompt_raw else None

        if prompt:
            extracted = extract_comfyui_essentials(prompt)
            return {"filename": filename, "raw": raw, "workflow": workflow, **extracted}
        return None
    except Exception:
        logger.error(f"Error processing image metadata: {filename}")
        return None


def read_png_sidecar(filename: Path) -> Optional[Dict[str, Any]]:
    sidecar_path = filename.with_suffix(".json")
    if os.path.exists(sidecar_path):
        with open(sidecar_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            extracted = extract_comfyui_essentials(data)
            return {"filename": filename, "sidecar": data, **extracted}
    return None


def image_metadata(filename: Path) -> Optional[Dict[str, Any]]:
    try:
        sidecar_path = filename.with_suffix(".json")
        sidecar = None
        img = Image.open(filename)
        raw = img.info or {}
        workflow_raw = str(raw.get("workflow")) if raw is not None else None
        prompt_raw = str(raw.get("prompt")) if raw is not None else None
        workflow = json.loads(workflow_raw) if workflow_raw is not None else None
        parsed = json.loads(prompt_raw) if prompt_raw else None
        prompt: dict[str, Any] | None = parsed if isinstance(parsed, dict) else None
        size = os.path.getsize(filename)

        result = {"filename": filename, "raw": raw, "workflow": workflow, "prompt_raw": prompt_raw}
        if prompt:
            extracted = extract_comfyui_essentials(prompt)
            result.update(extracted)
        if os.path.exists(sidecar_path):
            with open(sidecar_path, "r", encoding="utf-8") as f:
                sidecar = json.load(f)
                side_extracted = extract_comfyui_essentials(sidecar)
                result["sidecar"] = sidecar
                result.update(**side_extracted)
        return result
    except Exception:
        logger.error(f"Error processing image metadata: {filename}")
        return None


def to_int(data: Dict[str, Any], key: str) -> Optional[int]:
    value = data.get(key)
    if value is not None:
        try:
            return TypeAdapter(int).validate_strings(str(value)) if value is not None else None
        except (ValueError, TypeError):
            logger.warning(f"Expected integer for key '{key}', got {value} in file {data.get('filename')}")
    return None


async def save_image(session: AsyncSession, data: Dict[str, Any], filename: Path) -> ModelImage:
    model = ModelImage()
    model.width = int(data.get("image_width") or 0)
    model.height = int(data.get("image_height") or 0)
    model.file_name = filename.name
    model.path = str(filename.parent)
    model.mimetype = "image/png"

    width = to_int(data, "image_width") or 0
    height = to_int(data, "image_height") or 0
    model.width = width
    model.height = height
    model.aspect_ratio = (width / height) if (width is not None and height not in (None, 0)) else None

    model.file_size = os.path.getsize(filename)
    model.sha256 = sha256_of_file(str(filename))
    model.file_date = get_created(filename)

    session.add(model)
    await session.flush()  # gets PK from DB without committing yet
    await session.refresh(model)
    return model


async def save_generation(session: AsyncSession, data: Dict[str, Any], filename: Path, image: ModelImage) -> Generation:
    model = Generation()
    model.model_name = data.get("model")
    model.positive_prompt = ", ".join(data.get("positive_prompts") or [])
    model.negative_prompt = ", ".join(data.get("positive_prompts") or [])
    model.styles = ", ".join(data.get("styles") or [])
    model.cfg = data.get("cfg")
    model.steps = int(data.steps) if data.get("steps") is not None else None
    model.scheduler = data.get("scheduler")
    model.seed = int(data.get("seed") or 0) if data.get("seed") is not None else None
    model.image_id = image.id

    session.add(model)
    await session.flush()  # gets PK from DB without committing yet
    await session.refresh(model)
    return model


async def save_storage(session: AsyncSession, data: Dict[str, Any], filename: Path, image: ModelImage) -> Storage:
    model = Storage()
    model.image_id = image.id
    model.file_name = str(data.get("filename")) if data.get("filename") is not None else None
    model.size = to_int(data,"size") or 0
    model.mimetype = data.get("mimetype")
    session.add(model)
    await session.flush()  # gets PK from DB without committing yet
    await session.refresh(model)
    return model

async def save_meta_data(session: AsyncSession, data: Dict[str, Any], filename: Path, image: ModelImage) -> MetaData:
    model = MetaData()
    model.image_id = image.id
    model.raw = data["raw"]
    session.add(model)
    await session.flush()  # gets PK from DB without committing yet
    await session.refresh(model)
    return model


async def save_loras(session: AsyncSession, data: Dict[str, Any], filename: Path, generation: Generation) -> list[Lora]:
    loras = []
    for lora in data.get("loras") or []:
        lora_model = Lora()
        lora_model.model_name = str(data.get("model")) if data.get("model") is not None else None
        lora_model.name = data.get("lora_name")
        lora_model.strength_model = data.get("strength_model")
        lora_model.strength_clip = data.get("strength_clip")
        lora_model.description = data.get("description")
        lora_model.url = data.get("url")
        lora_model.trigger = data.get("trigger")
        lora_model.tokens = data.get("tokens")
        lora_model.generation_id = generation.id
        loras.append(lora_model)
        session.add(lora_model)
        await session.flush()  # gets PK from DB without committing yet
        await session.refresh(lora_model)
    return loras


async def save_review(session: AsyncSession, data: Dict[str, Any], filename: Path, image: ModelImage) -> Review:
    review = Review()
    review.image_id = image.id
    session.add(review)
    await session.flush()  # gets PK from DB without committing yet
    await session.refresh(review)
    return review


async def import_one(parsed: dict):
    async with async_session_factory() as session:
        try:
            asset = await save_image(session, parsed, parsed["filename"])
            generation = await save_generation(session, parsed, parsed["filename"], asset)
            loras = await save_loras(session, parsed, parsed["filename"], generation)
            review = await save_review(session, parsed, parsed["filename"], asset)
            store = await save_storage(session, parsed, parsed["filename"], asset)
            meta = await  save_meta_data(session, parsed, parsed["filename"], asset)

            await session.commit()
            return asset
        except Exception:
            logger.error(f"Error importing image: {parsed['filename']}", exc_info=True)
            await session.rollback()
            raise


async def start_import(images_dir: str):
    files = scan_images(images_dir)
    print(f"Found {len(files)} images")
    for file in files:
        if file.lower().endswith(".png"):
            result = read_png_metadata(file)
            if result is not None:
                print(f"Importing metadata {file}")
                await   import_one(result)
            else:
                result = read_png_sidecar(file)
                if result is not None:
                    print(f"Importing sidecar {file}")
                    await  import_one(result)
