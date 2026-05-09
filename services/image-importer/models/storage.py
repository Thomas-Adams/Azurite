from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint, Text, Integer, String, CHAR, TIMESTAMP, Float
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, EntityBaseMixin


class Storage(EntityBaseMixin, Base):
    __tablename__ = "storage"
    __table_args__ = (
        UniqueConstraint("image_id", name="storage_image_id_uix"),
        {"schema": "pony_image"},
    )
    image_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("pony_image.image.id", name="fk_storage_image_id"),
        nullable=False,
    )
    sha256: Mapped[str] = mapped_column(CHAR(64), nullable=False, index=True)
    search: Mapped[str | None] = mapped_column(TSVECTOR, nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    bucket: Mapped[str | None] = mapped_column(Text, nullable=True)
    host: Mapped[str | None] = mapped_column(Text, nullable=True)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    aspect_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    mimetype: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_date: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
