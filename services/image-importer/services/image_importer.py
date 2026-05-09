import glob
import os
import json
import asyncio
from PIL import Image
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import TypeAdapter
from sqlalchemy.ext.asyncio import AsyncSession

from api.state import IMAGE_ROOT
from database import async_session_factory
from dto.request.request_dto import ReviewDto
from storage.config import minio_client
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
        workflow = json.loads(str(workflow_raw)) if workflow_raw else None
        prompt = json.loads(str(prompt_raw)) if prompt_raw else None

        if prompt:
            extracted = extract_comfyui_essentials({"prompt": prompt})
            return {"filename": filename, "raw": raw, "workflow": workflow, **extracted}
        return None
    except (FileNotFoundError, AttributeError, IOError):
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
        workflow_raw = raw.get("workflow") if raw else None
        prompt_raw = raw.get("prompt") if raw else None
        workflow = json.loads(workflow_raw) if workflow_raw else None
        parsed = json.loads(prompt_raw) if prompt_raw else None
        prompt: dict[str, Any] | None = parsed if isinstance(parsed, dict) else None
        size = os.path.getsize(filename)

        result = {"filename": filename, "raw": raw, "workflow": workflow, "prompt_raw": prompt_raw}
        if prompt:
            extracted = extract_comfyui_essentials({"prompt": prompt})
            result.update(extracted)
        if os.path.exists(sidecar_path):
            with open(sidecar_path, "r", encoding="utf-8") as f:
                sidecar = json.load(f)
                side_extracted = extract_comfyui_essentials(sidecar)
                result["sidecar"] = sidecar
                result.update(**side_extracted)
        return result
    except (FileNotFoundError, AttributeError, IOError):
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


async def prepare_data(filename: Path) -> dict[str, Any]:
    data = dict()
    img = Image.open(filename)
    raw = img.info or {}
    data.update({"width": img.width})
    data.update({"file_size": os.path.getsize(filename)})
    data.update({"mimetype": img.format})
    data.update({"file_date": get_created(filename)})
    data.update({"height": img.height})
    data.update({"aspect_ratio": (img.width / img.height) if (img.width is not None and img.height not in (None, 0)) else 0})
    data.update({"filename": filename})
    data.update({"info": raw})
    data.update({"workflow_raw": str(raw.get("workflow")) if raw is not None else None})
    data.update({"prompt_raw": str(raw.get("prompt")) if raw is not None else None})
    data.update({"workflow" : json.loads(data.get("workflow_raw", '{}'))})
    data.update({"prompt": json.loads(data.get("prompt_raw", '{}'))})
    data.update({"styles": None})
    data.update({"cfg": None})
    return data


async def save_image(session: AsyncSession, data: Dict[str, Any], filename: Path) -> ModelImage:
    model = ModelImage()
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
    model.negative_prompt = ", ".join(data.get("negative_prompts") or [])
    model.styles = ", ".join(data.get("styles") or [])
    model.cfg = data.get("cfg")
    model.steps = int(data["steps"]) if data.get("steps") is not None else None
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
    model.size = to_int(data, "size") or 0
    model.width = to_int(data, "width") or 0
    model.height = to_int(data, "height") or 0
    model.mimetype = data.get("mimetype")
    model.aspect_ratio = data.get("aspect_ratio") or None
    model.bucket_name = data.get("bucket")
    model.file_size = to_int(data, "file_size") or 0
    model.url = data.get("url") or None
    model.file_date = data.get("file_date") or None
    model.search = data.get("prompt_raw") or None

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
        lora_model.model_name = str(data.get("model")) if data.get("model") else None  # global
        lora_model.name = lora.get("lora_name")
        lora_model.strength_model = lora.get("strength_model")
        lora_model.strength_clip = lora.get("strength_clip")
        lora_model.description = lora.get("description")
        lora_model.url = lora.get("url")
        lora_model.trigger = lora.get("trigger")
        lora_model.tokens = lora.get("tokens")
        lora_model.generation_id = generation.id
        loras.append(lora_model)
        session.add(lora_model)
        await session.flush()  # gets PK from DB without committing yet
        await session.refresh(lora_model)
    return loras


async def save_review(session: AsyncSession, dto: ReviewDto, filename: Path, image: ModelImage) -> Review:
    review = Review()
    review.image_id = image.id
    review.rating = int(dto.rating)
    review.comment = dto.comment

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

            review = ReviewDto()
            review.image_id = asset.id
            review.rating = parsed["rating"]
            review.comment = parsed["comment"]
            review = await save_review(session, review, parsed["filename"], asset)
            store = await save_storage(session, parsed, parsed["filename"], asset)
            meta = await  save_meta_data(session, parsed, parsed["filename"], asset)

            await session.commit()
            return asset
        except Exception:
            logger.error(f"Error importing image: {parsed['filename']}", exc_info=True)
            await session.rollback()
            raise


async def upload_and_review_image(review_dto: ReviewDto):
    async with async_session_factory() as session:
        try:
            if review_dto.path.startswith(IMAGE_ROOT):
                image_path: Path = Path(review_dto.path)
            else:
                image_path: Path = Path(os.path.join(IMAGE_ROOT, review_dto.path))

            data = await prepare_data(image_path)
            data.update({"review": review_dto, "bucket_name": review_dto.bucket_name})
            image = Image.open(image_path)
            meta_data = image_metadata(image_path)
            if meta_data:
                data.update(meta_data)

            model_image = await save_image(session, data, image_path)
            model_generation = await save_generation(session, data, image_path, model_image)
            loras = await  save_loras(session, data, image_path, model_generation)
            review = await  save_review(session, review_dto, image_path, model_image)
            meta_data = await  save_meta_data(session, data, image_path, model_image)
            object_name = f"{model_image.id}{image_path.suffix}"
            await asyncio.to_thread(
                lambda: not minio_client.bucket_exists(review_dto.bucket_name) and minio_client.make_bucket(review_dto.bucket_name)
            )
            await asyncio.to_thread(
                minio_client.fput_object,
                review_dto.bucket_name,
                object_name,
                str(image_path),
                content_type=f"image/{image_path.suffix.lstrip('.')}",
            )
            url = f"http://localhost:9001/{review_dto.bucket_name}/{object_name}"
            data.update({"url": url})
            storage = await  save_storage(session, data, image_path, model_image)
            await session.commit()
            return (
                model_image,
                model_generation,
                loras,
                review,
                storage,
                meta_data
            )

        except Exception:
            logger.error(f"Error importing image: ${image_path}", exc_info=True)
            await session.rollback()
            raise
