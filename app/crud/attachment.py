from sqlalchemy.orm import Session
from app.models.attachment import Attachment
from app.schemas.attachment import AttachmentCreate, AttachmentUpdate

def create_attachment(db: Session, attachment_in: AttachmentCreate) -> Attachment:
    attachment = Attachment(**attachment_in.model_dump())
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment

def get_attachment(db: Session, attachment_id: int) -> Attachment:
    return db.query(Attachment).filter(Attachment.id == attachment_id).first()

def get_attachments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Attachment).offset(skip).limit(limit).all()

def delete_attachment(db: Session, attachment: Attachment):
    db.delete(attachment)
    db.commit()

def update_attachment(db: Session, db_attachment: Attachment, update_data: AttachmentUpdate) -> Attachment:
    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(db_attachment, key, value)
    db.commit()
    db.refresh(db_attachment)
    return db_attachment
