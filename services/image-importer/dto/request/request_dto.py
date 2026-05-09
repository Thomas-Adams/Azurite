from pydantic import BaseModel


class ScanImagesRequestDto(BaseModel):
    directory: str
    image_types: list[str] = ['.png']


class ReviewDto(BaseModel):
    hash: str
    path: str
    bucket_name: str
    rating: int
    comment: str