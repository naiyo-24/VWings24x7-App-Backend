from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path
import os
from datetime import datetime

from db import get_db
from models.salary.salary_models import Salary
from models.auth.teacher_models import Teacher
from services.salary_id_generator import generate_salary_id

router = APIRouter(prefix="/api/salaries", tags=["Salaries"])


# Create/upload salary file for a teacher
@router.post("/create", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_salary(
	teacher_id: str = Form(...),
	month: int = Form(...),
	year: int = Form(...),
	file: UploadFile = File(...),
	db: Session = Depends(get_db),
):
	# verify teacher exists
	teacher = db.query(Teacher).filter_by(teacher_id=teacher_id).first()
	if not teacher:
		raise HTTPException(status_code=404, detail="Teacher not found")

	now = datetime.utcnow()
	salary_id = generate_salary_id(now)

	# save file
	uploads_dir = Path("uploads") / "salaries" / salary_id
	uploads_dir.mkdir(parents=True, exist_ok=True)
	filename = f"{salary_id}_{file.filename}"
	file_path = uploads_dir / filename
	with open(file_path, "wb") as f:
		content = await file.read()
		f.write(content)

	db_salary = Salary(
		salary_id=salary_id,
		teacher_id=teacher_id,
		month=month,
		year=year,
		file_path=str(file_path),
		created_at=now,
		updated_at=now,
	)
	db.add(db_salary)
	db.commit()
	db.refresh(db_salary)

	return {"detail": "Salary uploaded", "salary_id": salary_id}


# Get salary by id
@router.get("/get-by/{salary_id}", response_model=dict)
def get_salary_by_id(salary_id: str, db: Session = Depends(get_db)):
	salary = db.query(Salary).filter_by(salary_id=salary_id).first()
	if not salary:
		raise HTTPException(status_code=404, detail="Salary not found")
	return {
		"salary_id": salary.salary_id,
		"teacher_id": salary.teacher_id,
		"month": salary.month,
		"year": salary.year,
		"file_path": salary.file_path,
		"created_at": salary.created_at,
		"updated_at": salary.updated_at,
	}


# Get all salaries
@router.get("/get-all", response_model=List[dict])
def get_all_salaries(db: Session = Depends(get_db)):
	salaries = db.query(Salary).all()
	return [
		{
			"salary_id": s.salary_id,
			"teacher_id": s.teacher_id,
			"month": s.month,
			"year": s.year,
			"file_path": s.file_path,
			"created_at": s.created_at,
			"updated_at": s.updated_at,
		}
		for s in salaries
	]


# Get salaries by teacher id
@router.get("/get-by-teacher/{teacher_id}", response_model=List[dict])
def get_salaries_by_teacher(teacher_id: str, db: Session = Depends(get_db)):
	salaries = db.query(Salary).filter_by(teacher_id=teacher_id).all()
	return [
		{
			"salary_id": s.salary_id,
			"teacher_id": s.teacher_id,
			"month": s.month,
			"year": s.year,
			"file_path": s.file_path,
			"created_at": s.created_at,
			"updated_at": s.updated_at,
		}
		for s in salaries
	]


# Delete salary by id
@router.delete("/delete-by/{salary_id}", response_model=dict)
def delete_salary(salary_id: str, db: Session = Depends(get_db)):
	salary = db.query(Salary).filter_by(salary_id=salary_id).first()
	if not salary:
		raise HTTPException(status_code=404, detail="Salary not found")

	# remove file if exists
	try:
		if salary.file_path and os.path.exists(salary.file_path):
			os.remove(salary.file_path)
	except Exception:
		pass

	db.delete(salary)
	db.commit()
	return {"detail": "Salary deleted"}

