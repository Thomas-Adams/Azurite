from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, EntityBaseMixin


class Settings(EntityBaseMixin, Base):
    __tablename__ = "settings"
    __table_args__ = {"schema": "pony_image"}

    image_root: Mapped[str] = mapped_column(Text, nullable=False)
