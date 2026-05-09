from sqlalchemy import select

from config import settings as env_settings
from database import async_session_factory
from models.settings import Settings


async def get_settings() -> Settings:
    async with async_session_factory() as session:
        row = (await session.execute(select(Settings))).scalar_one_or_none()
        if row is None:
            row = Settings(image_root=env_settings.image_root)
            session.add(row)
            await session.commit()
            await session.refresh(row)
        return row


async def update_settings(image_root: str) -> Settings:
    async with async_session_factory() as session:
        row = (await session.execute(select(Settings))).scalar_one_or_none()
        if row is None:
            row = Settings(image_root=image_root)
            session.add(row)
        else:
            row.image_root = image_root
        await session.commit()
        await session.refresh(row)
        return row
