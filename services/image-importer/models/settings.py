from sqlalchemy import JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, EntityBaseMixin


class Settings(EntityBaseMixin, Base):
    __tablename__ = "settings"
    __table_args__ = {"schema": "pony_image"}

    image_root: Mapped[str] = mapped_column(Text, nullable=False)
    buckets: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list, server_default="[]")
