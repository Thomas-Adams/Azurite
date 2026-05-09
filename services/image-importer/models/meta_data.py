from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint,   BigInteger, Text, Integer, String, CHAR, TIMESTAMP, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, EntityBaseMixin


class MetaData(EntityBaseMixin, Base):
    __tablename__ = "meta_data"
    __table_args__ = (
        UniqueConstraint("image_id", name="meta_data_image_id_uix"),
        {"schema": "pony_image"},
    )
    image_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("pony_image.image.id",name="fk_meta_data_image_id"),
        nullable=False,
    )
    raw: Mapped[dict | None] = mapped_column(JSONB, nullable=True)