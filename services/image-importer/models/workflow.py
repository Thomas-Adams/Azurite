from sqlalchemy import UniqueConstraint, BigInteger, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, EntityBaseMixin


class Workflow(EntityBaseMixin, Base):
    __tablename__ = "workflow"
    __table_args__ = (
        UniqueConstraint("image_id", name="workflow_image_id_uix"),
        {"schema": "pony_image"},
    )
    image_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("pony_image.image.id", name="fk_workflow_image_id"),
        nullable=False,
    )
    workflow: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    sidecar: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
