
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from sqlalchemy.orm import Session
import os
from db import get_db
from models.classroom.classroom_models import Classroom
from services.classroom_id_generator import generate_class_id
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

# Pydantic Schemas
class ClassroomCreate(BaseModel):
    class_name: str
    class_description: Optional[str] = None

class ClassroomResponse(BaseModel):
    class_id: str
    class_name: str
    class_description: Optional[str] = None
    class_photo: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

router = APIRouter(prefix="/api/classrooms", tags=["Classrooms"])

UPLOAD_DIR = "uploads/classroom"

# Helper to save photo
async def save_class_photo(class_id: str, photo: UploadFile):
    dir_path = os.path.join(UPLOAD_DIR, class_id)
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, photo.filename)
    with open(file_path, "wb") as f:
        f.write(await photo.read())
    return file_path


@router.post("/create", response_model=ClassroomResponse)
async def create_classroom(
    class_name: str = File(...),
    class_description: str = File(None),
    photo: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    class_id = generate_class_id()
    photo_path = None
    if photo:
        photo_path = await save_class_photo(class_id, photo)
    classroom = Classroom(
        class_id=class_id,
        class_name=class_name,
        class_description=class_description,
        class_photo=photo_path,
        created_at=datetime.utcnow()
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return classroom


@router.get("/get-all", response_model=List[ClassroomResponse])
def get_all_classrooms(db: Session = Depends(get_db)):
    classrooms = db.query(Classroom).all()
    return classrooms


@router.get("/get-by/{class_id}", response_model=ClassroomResponse)
def get_classroom_by_id(class_id: str, db: Session = Depends(get_db)):
    classroom = db.query(Classroom).filter(Classroom.class_id == class_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    return classroom


@router.put("/update-by/{class_id}", response_model=ClassroomResponse)
async def update_classroom(
    class_id: str,
    class_name: str = File(...),
    class_description: str = File(None),
    photo: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    classroom = db.query(Classroom).filter(Classroom.class_id == class_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    classroom.class_name = class_name
    classroom.class_description = class_description
    if photo:
        photo_path = await save_class_photo(class_id, photo)
        classroom.class_photo = photo_path
    classroom.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(classroom)
    return classroom


@router.delete("/delete-by/{class_id}")
def delete_classroom(class_id: str, db: Session = Depends(get_db)):
    classroom = db.query(Classroom).filter(Classroom.class_id == class_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    db.delete(classroom)
    db.commit()
    dir_path = os.path.join(UPLOAD_DIR, class_id)
    if os.path.exists(dir_path):
        import shutil
        shutil.rmtree(dir_path)
    return {"message": "Classroom deleted"}


class BulkDeleteRequest(BaseModel):
    class_ids: List[str]

@router.delete("/delete/bulk")
def delete_classrooms_bulk(request: BulkDeleteRequest, db: Session = Depends(get_db)):
    deleted = 0
    for class_id in request.class_ids:
        classroom = db.query(Classroom).filter(Classroom.class_id == class_id).first()
        if classroom:
            db.delete(classroom)
            dir_path = os.path.join(UPLOAD_DIR, class_id)
            if os.path.exists(dir_path):
                import shutil
                shutil.rmtree(dir_path)
            deleted += 1
    db.commit()
    return {"message": f"Deleted {deleted} classrooms"}
