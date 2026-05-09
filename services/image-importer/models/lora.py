from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint, BigInteger, Text, Integer, String, CHAR, TIMESTAMP, Float
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, EntityBaseMixin


class Lora(EntityBaseMixin, Base):
    __tablename__ = "lora"
    __table_args__ = (
        {"schema": "pony_image"},
    )
    generation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("pony_image.generation.id", name="fk_lora_generation_id"),
        nullable=False,
    )
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_name: Mapped[str| None] = mapped_column(Text, nullable=True)
    description: Mapped[str| None] = mapped_column(Text, nullable=True)
    url: Mapped[str| None] = mapped_column(Text, nullable=True)
    trigger: Mapped[str| None] = mapped_column(Text, nullable=True)
    tokens: Mapped[str| None] = mapped_column(Text, nullable=True)
    strength_model: Mapped[float | None] = mapped_column(Float, nullable=True)
    strength_clip: Mapped[float| None] = mapped_column(Float, nullable=True)

