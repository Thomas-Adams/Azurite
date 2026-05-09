"""
Backfill Meilisearch index with all already-reviewed images from the database.
Run from services/image-importer/:
    .venv/bin/python scripts/backfill_search_index.py
"""
import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import async_session_factory
from models.generation import Generation
from models.image import Image as ModelImage
from models.lora import Lora
from models.review import Review
from models.storage import Storage
from search.client import get_index
from search.indexer import build_document
from sqlalchemy import select

logging.basicConfig(level=logging.WARNING)


async def backfill():
    async with async_session_factory() as session:
        images = (await session.execute(select(ModelImage))).scalars().all()
        docs = []
        for img in images:
            gen = (await session.execute(
                select(Generation).where(Generation.image_id == img.id)
            )).scalar_one_or_none()
            rev = (await session.execute(
                select(Review).where(Review.image_id == img.id)
            )).scalar_one_or_none()
            sto = (await session.execute(
                select(Storage).where(Storage.image_id == img.id)
            )).scalar_one_or_none()
            loras = (await session.execute(
                select(Lora).where(Lora.generation_id == gen.id)
            )).scalars().all() if gen else []

            if gen and rev and sto:
                docs.append(build_document(img, gen, loras, rev, sto))

    if docs:
        get_index().add_documents(docs)
        print(f"Indexed {len(docs)} document(s)")
    else:
        print("No reviewed images found to index.")


if __name__ == "__main__":
    asyncio.run(backfill())
