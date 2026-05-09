

from pydantic import BaseModel
from typing import Optional

class StartedJobResponseDto(BaseModel):
    job_id: str
    status: str

