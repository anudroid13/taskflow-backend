from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional

class AttachmentBase(BaseModel):
    filename: str
    url: str

class AttachmentCreate(AttachmentBase):
    uploader_id: int
    task_id: int

class AttachmentCreateRequest(BaseModel):
    filename: str
    url: str
    task_id: int

class AttachmentUpdate(BaseModel):
    filename: Optional[str] = None

class AttachmentRead(AttachmentBase):
    id: int
    uploader_id: int
    task_id: int
    uploaded_at: datetime
    model_config = ConfigDict(from_attributes=True)
