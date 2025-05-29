from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class StoryRequest(BaseModel):
    character_description: str

class StoryResponse(BaseModel):
    job_id: str
    status: str
    message: str

class JobStatus(BaseModel):
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error: Optional[str] = None
    output_dir: str 