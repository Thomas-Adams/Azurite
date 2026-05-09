from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ImageFileDto(BaseModel):
    filename: str
    index: Optional[int] = None
    url: str
    full_path: str
    size_bytes: int
    width: int
    height: int
    meta: dict
    modified_at: datetime
    hash: str