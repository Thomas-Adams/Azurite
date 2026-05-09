from pydantic import BaseModel
from datetime import datetime


class ImageFileDto(BaseModel):
    filename: str
    index: int | None = None
    url: str
    full_path: str
    size_bytes: int
    width: int
    height: int
    meta: dict | None
    modified_at: datetime
    hash: str
    already_reviewed: bool = False