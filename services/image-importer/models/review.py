from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, EntityBaseMixin


class Review(EntityBaseMixin, Base):
    __tablename__ = "review"
    __table_args__ = (
        UniqueConstraint("image_id", name="review_image_id_uix"),
        {"schema": "pony_image"},
    )
    image_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("pony_image.image.id", name="fk_review_image_id"),
        nullable=False,
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)

