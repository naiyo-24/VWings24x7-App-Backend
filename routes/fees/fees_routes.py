from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path
import os
from datetime import datetime

from db import get_db
from models.fees.fees_models import Fee
from models.auth.student_models import Student
from services.fees_id_generator import generate_fee_id

router = APIRouter(prefix="/api/fees", tags=["Fees"])


# Create/upload fee file for a student
@router.post("/create", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_fee(
	student_id: str = Form(...),
	installment_no: int = Form(...),
	file: UploadFile = File(...),
	db: Session = Depends(get_db),
):
	# verify student exists
	student = db.query(Student).filter_by(student_id=student_id).first()
	if not student:
		raise HTTPException(status_code=404, detail="Student not found")

	now = datetime.utcnow()
	fee_id = generate_fee_id(now)

	# save file
	uploads_dir = Path("uploads") / "fees" / fee_id
	uploads_dir.mkdir(parents=True, exist_ok=True)
	filename = f"{fee_id}_{file.filename}"
	file_path = uploads_dir / filename
	with open(file_path, "wb") as f:
		content = await file.read()
		f.write(content)

	db_fee = Fee(
		fee_id=fee_id,
		student_id=student_id,
		installment_no=installment_no,
		file_path=str(file_path),
		created_at=now,
		updated_at=now,
	)
	db.add(db_fee)
	db.commit()
	db.refresh(db_fee)

	return {"detail": "Fee uploaded", "fee_id": fee_id}


# Get fee by id
@router.get("/get-by/{fee_id}", response_model=dict)
def get_fee_by_id(fee_id: str, db: Session = Depends(get_db)):
	fee = db.query(Fee).filter_by(fee_id=fee_id).first()
	if not fee:
		raise HTTPException(status_code=404, detail="Fee not found")
	return {
		"fee_id": fee.fee_id,
		"student_id": fee.student_id,
		"installment_no": fee.installment_no,
		"file_path": fee.file_path,
		"created_at": fee.created_at,
		"updated_at": fee.updated_at,
	}


# Get all fees
@router.get("/get-all", response_model=List[dict])
def get_all_fees(db: Session = Depends(get_db)):
	fees = db.query(Fee).all()
	return [
		{
			"fee_id": f.fee_id,
			"student_id": f.student_id,
			"installment_no": f.installment_no,
			"file_path": f.file_path,
			"created_at": f.created_at,
			"updated_at": f.updated_at,
		}
		for f in fees
	]


# Get fees by student id
@router.get("/get-by-student/{student_id}", response_model=List[dict])
def get_fees_by_student(student_id: str, db: Session = Depends(get_db)):
	fees = db.query(Fee).filter_by(student_id=student_id).all()
	return [
		{
			"fee_id": f.fee_id,
			"student_id": f.student_id,
			"installment_no": f.installment_no,
			"file_path": f.file_path,
			"created_at": f.created_at,
			"updated_at": f.updated_at,
		}
		for f in fees
	]


# Delete fee by id
@router.delete("/delete-by/{fee_id}", response_model=dict)
def delete_fee(fee_id: str, db: Session = Depends(get_db)):
	fee = db.query(Fee).filter_by(fee_id=fee_id).first()
	if not fee:
		raise HTTPException(status_code=404, detail="Fee not found")

	# remove file if exists
	try:
		if fee.file_path and os.path.exists(fee.file_path):
			os.remove(fee.file_path)
	except Exception:
		pass

	db.delete(fee)
	db.commit()
	return {"detail": "Fee deleted"}

