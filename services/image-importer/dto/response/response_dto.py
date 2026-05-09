from pydantic import BaseModel


class StartedJobResponseDto(BaseModel):
    job_id: str
    status: str

