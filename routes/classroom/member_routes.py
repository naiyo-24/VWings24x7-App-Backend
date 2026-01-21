
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from db import get_db
from models.classroom.member_models import Member
from models.classroom.classroom_models import Classroom
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/classrooms/members", tags=["Classroom Members"])

# Pydantic Schemas
class MemberCreateRequest(BaseModel):
	class_id: str
	user_id: str
	user_type: str  # 'student' or 'teacher'
	role: str       # 'member' or 'admin'

class MemberRemoveRequest(BaseModel):
	class_id: str
	user_id: str
	user_type: str  # 'student' or 'teacher'

class AdminDemoteRequest(BaseModel):
	class_id: str
	teacher_id: str

class AdminAddRequest(BaseModel):
	class_id: str
	teacher_id: str

class MemberResponse(BaseModel):
	classroom_id: str
	members: List[str]
	admins: List[str]
	created_at: Optional[datetime] = None
	updated_at: Optional[datetime] = None

	class Config:
		orm_mode = True

# Helper to get or create Member row for a classroom
def get_or_create_member_row(db: Session, class_id: str):
	member_row = db.query(Member).filter(Member.classroom_id == class_id).first()
	if not member_row:
		member_row = Member(
			id=str(uuid.uuid4()),
			classroom_id=class_id,
			members=[],
			admins=[],
			created_at=datetime.utcnow()
		)
		db.add(member_row)
		db.commit()
		db.refresh(member_row)
	return member_row

# Add member or admin
@router.post("/add-member", response_model=MemberResponse)
def add_member(req: MemberCreateRequest, db: Session = Depends(get_db)):
	member_row = get_or_create_member_row(db, req.class_id)
	if req.user_type == "student" and req.role == "member":
		if req.user_id not in member_row.members:
			member_row.members.append(req.user_id)
	elif req.user_type == "teacher" and req.role == "admin":
		if req.user_id not in member_row.admins:
			member_row.admins.append(req.user_id)
	else:
		raise HTTPException(status_code=400, detail="Invalid user_type or role")
	member_row.updated_at = datetime.utcnow()
	db.commit()
	db.refresh(member_row)
	return member_row

# Remove member or admin
@router.post("/remove-member", response_model=MemberResponse)
def remove_member(req: MemberRemoveRequest, db: Session = Depends(get_db)):
	member_row = db.query(Member).filter(Member.classroom_id == req.class_id).first()
	if not member_row:
		raise HTTPException(status_code=404, detail="Classroom members not found")
	changed = False
	if req.user_type == "student":
		if req.user_id in member_row.members:
			member_row.members.remove(req.user_id)
			changed = True
	elif req.user_type == "teacher":
		if req.user_id in member_row.admins:
			member_row.admins.remove(req.user_id)
			changed = True
	else:
		raise HTTPException(status_code=400, detail="Invalid user_type")
	if changed:
		member_row.updated_at = datetime.utcnow()
		db.commit()
		db.refresh(member_row)
	return member_row

# Add admin (promote teacher)
@router.post("/add-admin", response_model=MemberResponse)
def add_admin(req: AdminAddRequest, db: Session = Depends(get_db)):
	member_row = get_or_create_member_row(db, req.class_id)
	if req.teacher_id not in member_row.admins:
		member_row.admins.append(req.teacher_id)
		member_row.updated_at = datetime.utcnow()
		db.commit()
		db.refresh(member_row)
	return member_row

# Demote admin (remove teacher from admins)
@router.post("/demote-admin", response_model=MemberResponse)
def demote_admin(req: AdminDemoteRequest, db: Session = Depends(get_db)):
	member_row = db.query(Member).filter(Member.classroom_id == req.class_id).first()
	if not member_row:
		raise HTTPException(status_code=404, detail="Classroom members not found")
	if req.teacher_id in member_row.admins:
		member_row.admins.remove(req.teacher_id)
		member_row.updated_at = datetime.utcnow()
		db.commit()
		db.refresh(member_row)
	return member_row

# Get members for a classroom
@router.get("/members/get-by/{class_id}", response_model=MemberResponse)
def get_members(class_id: str, db: Session = Depends(get_db)):
	member_row = db.query(Member).filter(Member.classroom_id == class_id).first()
	if not member_row:
		raise HTTPException(status_code=404, detail="Classroom members not found")
	return member_row
