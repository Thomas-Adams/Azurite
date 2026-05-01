from datetime import datetime

from sqlalchemy import (
    BigInteger, Text, Integer, String, CHAR, TIMESTAMP, Float,
    SmallInteger, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, EntityBaseMixin


class Image(EntityBaseMixin, Base):
    __tablename__ = "image"
    __table_args__ = (
        UniqueConstraint("sha256", name="image_assets_sha256_unique"),
        CheckConstraint("quality_rating between 0 and 5", name="image_assets_quality_rating_chk"),
        CheckConstraint("width > 0", name="image_assets_width_chk"),
        CheckConstraint("height > 0", name="image_assets_height_chk"),
        {"schema": "pony_image"},
    )
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    mimetype: Mapped[str | None] = mapped_column(String(30), nullable=True)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    aspect_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)  # see note below
    file_date: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)



