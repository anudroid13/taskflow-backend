import logging
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
from app.schemas.attachment import AttachmentRead, AttachmentCreate, AttachmentCreateRequest, AttachmentUpdate
from app.crud import attachment as crud_attachment
from app.crud import task as crud_task
from app.core.security import get_current_active_user, require_role
from app.db.session import get_db

logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter(prefix="/attachments", tags=["attachments"])

@router.post("/upload", response_model=AttachmentRead, status_code=status.HTTP_201_CREATED)
def upload_attachment(
    task_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    if not crud_task.get_task(db, task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    # Read in chunks to avoid loading huge files into memory
    chunk_size = 1024 * 1024  # 1 MB
    contents = b""
    while True:
        chunk = file.file.read(chunk_size)
        if not chunk:
            break
        contents += chunk
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File size exceeds 10 MB limit")
    ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    with open(file_path, "wb") as f:
        f.write(contents)
    attachment_in = AttachmentCreate(
        filename=file.filename,
        url=f"/{UPLOAD_DIR}/{unique_filename}",
        uploader_id=current_user.id,
        task_id=task_id,
    )
    return crud_attachment.create_attachment(db, attachment_in)

@router.post("/", response_model=AttachmentRead, status_code=status.HTTP_201_CREATED)
def create_attachment(
    attachment_in: AttachmentCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    if not crud_task.get_task(db, attachment_in.task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    full_attachment = AttachmentCreate(
        filename=attachment_in.filename,
        url=attachment_in.url,
        task_id=attachment_in.task_id,
        uploader_id=current_user.id,
    )
    return crud_attachment.create_attachment(db, full_attachment)

@router.get("/", response_model=List[AttachmentRead])
def list_attachments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    return crud_attachment.get_attachments(db, skip=skip, limit=limit)

@router.get("/{attachment_id}", response_model=AttachmentRead)
def get_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    db_attachment = crud_attachment.get_attachment(db, attachment_id)
    if not db_attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return db_attachment

@router.put("/{attachment_id}", response_model=AttachmentRead)
def update_attachment(
    attachment_id: int,
    update_data: AttachmentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "manager"])),
):
    db_attachment = crud_attachment.get_attachment(db, attachment_id)
    if not db_attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return crud_attachment.update_attachment(db, db_attachment, update_data)

@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin"])),
):
    db_attachment = crud_attachment.get_attachment(db, attachment_id)
    if not db_attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    # Delete file from disk if it exists
    if db_attachment.url:
        file_path = db_attachment.url.lstrip("/")
        if os.path.isfile(file_path):
            os.remove(file_path)
            logger.info("Deleted file: %s", file_path)
    crud_attachment.delete_attachment(db, db_attachment)
    return None
