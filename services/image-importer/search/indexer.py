import logging
from typing import Any

from models.generation import Generation
from models.image import Image as ModelImage
from models.lora import Lora
from models.review import Review
from models.storage import Storage
from search.client import get_index

logger = logging.getLogger(__name__)


def build_document(
    image: ModelImage,
    generation: Generation,
    loras: list[Lora],
    review: Review,
    storage: Storage,
) -> dict[str, Any]:
    return {
        "id": image.sha256,
        "filename": image.file_name,
        "path": image.path,
        "url": storage.url,
        "bucket": storage.bucket,
        "model": generation.model_name,
        "positive_prompts": generation.positive_prompt or "",
        "negative_prompts": generation.negative_prompt or "",
        "styles": (generation.styles or "").split(", ") if generation.styles else [],
        "loras": [lora.name for lora in loras if lora.name],
        "steps": generation.steps,
        "cfg": generation.cfg,
        "seed": generation.seed,
        "scheduler": generation.scheduler,
        "sampler_name": generation.scheduler,
        "rating": review.rating,
        "comment": review.comment or "",
        "image_width": image.width,
        "image_height": image.height,
    }


def index_review(
    image: ModelImage,
    generation: Generation,
    loras: list[Lora],
    review: Review,
    storage: Storage,
) -> None:
    doc = build_document(image, generation, loras, review, storage)
    try:
        get_index().add_documents([doc])
    except Exception:
        logger.error("Failed to index reviewed image %s in Meilisearch", image.sha256, exc_info=True)
