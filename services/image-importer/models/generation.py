from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint,   BigInteger, Text, Integer, String, CHAR, TIMESTAMP, Float
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, EntityBaseMixin


class Generation(EntityBaseMixin, Base):
    __tablename__ = "generation"
    __table_args__ = (
        UniqueConstraint("image_id", name="generation_image_id"),
        {"schema": "pony_image"},
    )
    image_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("pony_image.image.id"),
        nullable=False,
    )
    positive_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    negative_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    styles: Mapped[str | None] = mapped_column(Text, nullable=True)
    seed: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    steps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cfg: Mapped[float | None] = mapped_column(Float, nullable=True)  # see note below
    aspect_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)  # see note below
    samplers: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduler: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_name: Mapped[str | None] = mapped_column(Text, nullable=True)
