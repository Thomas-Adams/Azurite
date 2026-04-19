from datetime import datetime

from sqlalchemy import (
    BigInteger, Text, Integer, String, CHAR, TIMESTAMP,Float,
    SmallInteger, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class ImageAssets(Base):
    __tablename__ = "image_assets"
    __table_args__ = (
        UniqueConstraint("sha256", name="image_assets_sha256_unique"),
        CheckConstraint("quality_rating between 0 and 5", name="image_assets_quality_rating_chk"),
        CheckConstraint("width > 0", name="image_assets_width_chk"),
        CheckConstraint("height > 0", name="image_assets_height_chk"),
        {"schema": "pony_image"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    mimetype: Mapped[str | None] = mapped_column(String(30), nullable=True)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(CHAR(64), nullable=False)

    workflow: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    sidecar: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    positive_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    negative_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    seed: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    steps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cfg: Mapped[float | None] = mapped_column(Float, nullable=True)  # see note below
    aspect_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)  # see note below
    samplers: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduler: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    loras: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    generation_params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    quality_rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, default=0)
    quality_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow
    )
    imported_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True, default=datetime.utcnow
    )