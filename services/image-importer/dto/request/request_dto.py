

from pydantic import BaseModel
from typing import Optional

class ScanImagesRequestDto(BaseModel):
    directory: str
    image_types: list[str] = ['.png']
    filters: Optional[dict] = None
    recursive: bool = False


class ReviewDto(BaseModel):
    hash: str
    path: str
    bucket_name: str
    rating: str
    comment: str