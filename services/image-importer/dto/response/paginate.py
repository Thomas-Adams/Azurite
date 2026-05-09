from pydantic import BaseModel
from typing import Optional, TypeVar, Generic, Any, Dict

T = TypeVar("T")


class Paginated(BaseModel, Generic[T]):
    page: int
    size: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool
    params: Dict[str, Any] = {}
    content: list[T]

