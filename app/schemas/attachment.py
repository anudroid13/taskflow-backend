from pydantic import BaseModel
from typing import Optional

class AttachmentBase(BaseModel):
    filename: str
    url: str

class AttachmentCreate(AttachmentBase):
    uploader_id: int
    task_id: int

class AttachmentRead(AttachmentBase):
    id: int
    uploader_id: int
    task_id: int
    class Config:
        orm_mode = True
