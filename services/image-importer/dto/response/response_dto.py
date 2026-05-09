from pydantic import BaseModel


class StartedJobResponseDto(BaseModel):
    job_id: str
    status: str


class ErrorMessageDto(BaseModel):
    field: str | None = None
    message: str


class ReviewResultDto(BaseModel):
    success: bool
    errors: list[ErrorMessageDto] = []

