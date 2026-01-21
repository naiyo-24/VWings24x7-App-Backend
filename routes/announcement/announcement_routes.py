from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from db import get_db
from models.announcement.announcement_models import Announcement
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/announcements", tags=["Announcements"])

# Pydantic Schemas
class AnnouncementCreate(BaseModel):
	headline: str
	description: str
	active_status: Optional[bool] = True

class AnnouncementUpdate(BaseModel):
	headline: Optional[str]
	description: Optional[str]
	active_status: Optional[bool]

class AnnouncementOut(BaseModel):
	announcement_id: int
	headline: str
	description: str
	active_status: bool
	created_at: datetime
	updated_at: datetime

	class Config:
		orm_mode = True

# Create announcement
@router.post("/create", response_model=AnnouncementOut, status_code=status.HTTP_201_CREATED)
def create_announcement(payload: AnnouncementCreate, db: Session = Depends(get_db)):
	announcement = Announcement(**payload.dict())
	db.add(announcement)
	db.commit()
	db.refresh(announcement)
	return announcement

# Get all announcements
@router.get("/get-all", response_model=List[AnnouncementOut])
def get_all_announcements(db: Session = Depends(get_db)):
	return db.query(Announcement).all()

# Update announcement by id
@router.put("/update-by/{announcement_id}", response_model=AnnouncementOut)
def update_announcement(announcement_id: int, payload: AnnouncementUpdate, db: Session = Depends(get_db)):
	announcement = db.query(Announcement).filter(Announcement.announcement_id == announcement_id).first()
	if not announcement:
		raise HTTPException(status_code=404, detail="Announcement not found")
	for key, value in payload.dict(exclude_unset=True).items():
		setattr(announcement, key, value)
	db.commit()
	db.refresh(announcement)
	return announcement

# Delete announcement by id
@router.delete("/delete-by/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_announcement(announcement_id: int, db: Session = Depends(get_db)):
	announcement = db.query(Announcement).filter(Announcement.announcement_id == announcement_id).first()
	if not announcement:
		raise HTTPException(status_code=404, detail="Announcement not found")
	db.delete(announcement)
	db.commit()
	return

# Bulk delete announcements
class BulkDeleteRequest(BaseModel):
	ids: List[int]

@router.delete("/delete/bulk", status_code=status.HTTP_204_NO_CONTENT)
def bulk_delete_announcements(payload: BulkDeleteRequest, db: Session = Depends(get_db)):
	db.query(Announcement).filter(Announcement.announcement_id.in_(payload.ids)).delete(synchronize_session=False)
	db.commit()
	return
