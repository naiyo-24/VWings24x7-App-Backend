from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path
import os
import json
from datetime import datetime

from db import get_db
from models.classroom.classroom_models import Classroom, ClassMember, MemberRole, Message
from models.auth.teacher_models import Teacher
from models.auth.student_models import Student
from models.auth.admin_models import Admin
from models.courses.course_models import Course
from services.class_id_generator import generate_class_id

from pydantic import BaseModel

router = APIRouter(prefix="/api/classes", tags=["Classrooms"])


# Pydantic Schemas
class MemberOut(BaseModel):
    user_id: str
    role: str


class ClassroomCreate(BaseModel):
    name: str
    description: Optional[str] = None
    creator_admin_id: str
    teacher_ids: Optional[List[str]] = None
    student_ids: Optional[List[str]] = None


class ClassroomOut(BaseModel):
    class_id: str
    name: str
    description: Optional[str] = None
    photo: Optional[str] = None
    creator_admin_id: str
    created_at: datetime
    updated_at: datetime
    members: List[MemberOut] = []

    class Config:
        from_attributes = True


# Create classroom
@router.post("/create", response_model=ClassroomOut, status_code=status.HTTP_201_CREATED)
async def create_classroom(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    creator_admin_id: str = Form(...),
    teacher_ids: Optional[str] = Form(None),  # JSON string list
    student_ids: Optional[str] = Form(None),  # JSON string list
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    # validate admin
    admin = db.query(Admin).filter_by(id=creator_admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Creator admin not found")

    now = datetime.utcnow()
    class_id = generate_class_id(now)

    photo_path = None
    if photo:
        uploads_dir = Path("uploads") / "classes" / class_id
        uploads_dir.mkdir(parents=True, exist_ok=True)
        ext = os.path.splitext(photo.filename)[1]
        file_name = f"photo{ext}"
        file_path = uploads_dir / file_name
        with open(file_path, "wb") as buffer:
            buffer.write(await photo.read())
        photo_path = os.path.relpath(str(file_path), os.getcwd())

    classroom = Classroom(
        class_id=class_id,
        name=name,
        description=description,
        photo=photo_path,
        creator_admin_id=creator_admin_id,
        created_at=now,
        updated_at=now,
    )
    db.add(classroom)

    # add creator as admin member
    admin_member = ClassMember(
        id=f"CM{class_id}A",
        class_id=class_id,
        user_id=creator_admin_id,
        role=MemberRole.admin,
        added_by=creator_admin_id,
    )
    db.add(admin_member)

    # parse teacher_ids and student_ids
    teachers = []
    students = []
    if teacher_ids:
        try:
            teachers = json.loads(teacher_ids)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid teacher_ids JSON")
    if student_ids:
        try:
            students = json.loads(student_ids)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid student_ids JSON")

    # add teacher members
    for t_id in teachers:
        t = db.query(Teacher).filter_by(teacher_id=t_id).first()
        if not t:
            raise HTTPException(status_code=404, detail=f"Teacher {t_id} not found")
        cm = ClassMember(
            id=f"CM{class_id}T{t_id}",
            class_id=class_id,
            user_id=t_id,
            role=MemberRole.teacher,
            added_by=creator_admin_id,
        )
        db.add(cm)

    # add student members
    for s_id in students:
        s = db.query(Student).filter_by(student_id=s_id).first()
        if not s:
            raise HTTPException(status_code=404, detail=f"Student {s_id} not found")
        cm = ClassMember(
            id=f"CM{class_id}S{s_id}",
            class_id=class_id,
            user_id=s_id,
            role=MemberRole.student,
            added_by=creator_admin_id,
        )
        db.add(cm)

    db.commit()
    db.refresh(classroom)

    members = db.query(ClassMember).filter_by(class_id=class_id).all()
    members_out = [MemberOut(user_id=m.user_id, role=m.role.value) for m in members]

    return ClassroomOut(**{**classroom.__dict__}, members=members_out)


# Get classroom by id
@router.get("/{class_id}", response_model=ClassroomOut)
def get_classroom(class_id: str, db: Session = Depends(get_db)):
    classroom = db.query(Classroom).filter_by(class_id=class_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    members = db.query(ClassMember).filter_by(class_id=class_id).all()
    members_out = [MemberOut(user_id=m.user_id, role=m.role.value) for m in members]
    return ClassroomOut(**{**classroom.__dict__}, members=members_out)


# List classrooms
@router.get("/", response_model=List[ClassroomOut])
def list_classrooms(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    classes = db.query(Classroom).offset(skip).limit(limit).all()
    result = []
    for c in classes:
        members = db.query(ClassMember).filter_by(class_id=c.class_id).all()
        members_out = [MemberOut(user_id=m.user_id, role=m.role.value) for m in members]
        result.append(ClassroomOut(**{**c.__dict__}, members=members_out))
    return result


# Update classroom (only teacher or admin in class can update)
@router.put("/{class_id}", response_model=ClassroomOut)
async def update_classroom(
    class_id: str,
    user_id: str = Form(...),  # actor performing update
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    classroom = db.query(Classroom).filter_by(class_id=class_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    member = db.query(ClassMember).filter_by(class_id=class_id, user_id=user_id).first()
    if not member or member.role not in (MemberRole.teacher, MemberRole.admin):
        raise HTTPException(status_code=403, detail="Not authorized to update classroom")

    if name is not None:
        classroom.name = name
    if description is not None:
        classroom.description = description

    if photo:
        uploads_dir = Path("uploads") / "classes" / class_id
        uploads_dir.mkdir(parents=True, exist_ok=True)
        ext = os.path.splitext(photo.filename)[1]
        file_name = f"photo{ext}"
        file_path = uploads_dir / file_name
        with open(file_path, "wb") as buffer:
            buffer.write(await photo.read())
        classroom.photo = os.path.relpath(str(file_path), os.getcwd())

    classroom.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(classroom)

    members = db.query(ClassMember).filter_by(class_id=class_id).all()
    members_out = [MemberOut(user_id=m.user_id, role=m.role.value) for m in members]
    return ClassroomOut(**{**classroom.__dict__}, members=members_out)


# Delete classroom (admin only)
@router.delete("/{class_id}", response_model=dict)
def delete_classroom(class_id: str, admin_id: str = Query(...), db: Session = Depends(get_db)):
    classroom = db.query(Classroom).filter_by(class_id=class_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    admin_member = db.query(ClassMember).filter_by(class_id=class_id, user_id=admin_id, role=MemberRole.admin).first()
    if not admin_member:
        raise HTTPException(status_code=403, detail="Only class admin can delete the classroom")
    db.delete(classroom)
    db.commit()
    return {"detail": "Classroom deleted"}


# Add member (admin only)
class MemberCreate(BaseModel):
    user_id: str
    role: str  # admin|teacher|student


@router.post("/{class_id}/members", response_model=MemberOut)
def add_member(class_id: str, request: MemberCreate, admin_id: str = Query(...), db: Session = Depends(get_db)):
    classroom = db.query(Classroom).filter_by(class_id=class_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    admin_member = db.query(ClassMember).filter_by(class_id=class_id, user_id=admin_id, role=MemberRole.admin).first()
    if not admin_member:
        raise HTTPException(status_code=403, detail="Only class admin can add members")

    role_val = None
    try:
        role_val = MemberRole(request.role)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid role")

    # check existence depending on role
    if role_val == MemberRole.teacher:
        if not db.query(Teacher).filter_by(teacher_id=request.user_id).first():
            raise HTTPException(status_code=404, detail="Teacher not found")
    elif role_val == MemberRole.student:
        if not db.query(Student).filter_by(student_id=request.user_id).first():
            raise HTTPException(status_code=404, detail="Student not found")
    elif role_val == MemberRole.admin:
        if not db.query(Admin).filter_by(id=request.user_id).first():
            raise HTTPException(status_code=404, detail="Admin not found")

    existing = db.query(ClassMember).filter_by(class_id=class_id, user_id=request.user_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Member already exists")

    cm = ClassMember(
        id=f"CM{class_id}{request.user_id}",
        class_id=class_id,
        user_id=request.user_id,
        role=role_val,
        added_by=admin_id,
    )
    db.add(cm)
    db.commit()
    return MemberOut(user_id=cm.user_id, role=cm.role.value)


# Remove member (admin only)
@router.delete("/{class_id}/members/{user_id}", response_model=dict)
def remove_member(class_id: str, user_id: str, admin_id: str = Query(...), db: Session = Depends(get_db)):
    member = db.query(ClassMember).filter_by(class_id=class_id, user_id=admin_id, role=MemberRole.admin).first()
    if not member:
        raise HTTPException(status_code=403, detail="Only class admin can remove members")
    target = db.query(ClassMember).filter_by(class_id=class_id, user_id=user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(target)
    db.commit()
    return {"detail": "Member removed"}


# Get messages (pagination)
class MessageOut(BaseModel):
    message_id: str
    class_id: str
    sender_id: str
    sender_role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/{class_id}/messages", response_model=List[MessageOut])
def get_messages(class_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    msgs = db.query(Message).filter_by(class_id=class_id).order_by(Message.created_at.desc()).offset(skip).limit(limit).all()
    return [MessageOut(**{**m.__dict__}) for m in reversed(msgs)]
