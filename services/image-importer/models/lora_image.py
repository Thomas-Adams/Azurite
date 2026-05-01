from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint, BigInteger, Text, Integer, String, CHAR, TIMESTAMP, Float
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, EntityBaseMixin


class Lora(EntityBaseMixin, Base):
    __table__ = "lora_image"
    __table_args__ = (
        {"schema": "pony_image"},
    )
    lora_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("pony_image.lora.id"),
        nullable=False,
    )
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    bucket: Mapped[str] = mapped_column(Text, nullable=False)
    host: Mapped[str] = mapped_column(Text, nullable=False)



