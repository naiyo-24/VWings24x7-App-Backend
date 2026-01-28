from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pathlib import Path
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from db import get_db
from models.fee.fees_models import FeesReceipt
from models.auth.student_models import Student
from services.fees_receipt_generator import generate_fees_receipt

router = APIRouter(prefix="/api/fees", tags=["Fees"])


class FeesBase(BaseModel):
    student_id: str
    payment_no: Optional[int] = None
    payment_mode: Optional[str] = None
    transaction_id: Optional[str] = None
    amount: float
    total_course_fees: float
    amount_paid: float


class FeesCreate(FeesBase):
    pass


class FeesUpdate(BaseModel):
    payment_no: Optional[int] = None
    payment_mode: Optional[str] = None
    transaction_id: Optional[str] = None
    amount: Optional[float] = None
    total_course_fees: Optional[float] = None
    amount_paid: Optional[float] = None


class FeesOut(FeesBase):
    id: int
    amount_due: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("/create", response_model=FeesOut, status_code=status.HTTP_201_CREATED)
def create_fees_receipt(fees_in: FeesCreate, db: Session = Depends(get_db)):
    # Validate student
    student = db.query(Student).filter(Student.student_id == fees_in.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Ensure single receipt per student
    existing = db.query(FeesReceipt).filter(FeesReceipt.student_id == fees_in.student_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Fees receipt already exists for this student. Use update endpoint.")

    # Auto-calc amount_due
    amount_due = float(fees_in.total_course_fees) - float(fees_in.amount_paid)

    new_fees = FeesReceipt(
        student_id=fees_in.student_id,
        payment_no=fees_in.payment_no,
        payment_mode=fees_in.payment_mode,
        transaction_id=fees_in.transaction_id,
        amount=fees_in.amount,
        total_course_fees=fees_in.total_course_fees,
        amount_paid=fees_in.amount_paid,
        amount_due=amount_due
    )
    db.add(new_fees)
    db.commit()
    db.refresh(new_fees)

    # Generate PDF and store under uploads/fees/{student_id}/
    output_dir = Path("uploads/fees") / fees_in.student_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"fees_receipt_{fees_in.student_id}.pdf"
    generate_fees_receipt(student, new_fees, str(output_path))

    return new_fees


@router.put("/update-by/{fees_id}", response_model=FeesOut)
def update_fees_receipt(fees_id: int, update_data: FeesUpdate, db: Session = Depends(get_db)):
    fees = db.query(FeesReceipt).filter(FeesReceipt.id == fees_id).first()
    if not fees:
        raise HTTPException(status_code=404, detail="Fees receipt not found")

    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(fees, key, value)

    # Recalculate due if relevant fields changed
    total = fees.total_course_fees
    paid = fees.amount_paid
    fees.amount_due = float(total) - float(paid)

    db.commit()
    db.refresh(fees)

    # Regenerate PDF
    student = db.query(Student).filter(Student.student_id == fees.student_id).first()
    output_dir = Path("uploads/fees") / fees.student_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"fees_receipt_{fees.student_id}.pdf"
    generate_fees_receipt(student, fees, str(output_path))

    return fees


@router.get("/get-by/{student_id}", response_model=FeesOut)
def get_fees_by_student(student_id: str, db: Session = Depends(get_db)):
    fees = db.query(FeesReceipt).filter(FeesReceipt.student_id == student_id).first()
    if not fees:
        raise HTTPException(status_code=404, detail="Fees receipt not found")
    return fees


@router.delete("/delete-by/{fees_id}", response_model=dict)
def delete_fees_receipt(fees_id: int, db: Session = Depends(get_db)):
    fees = db.query(FeesReceipt).filter(FeesReceipt.id == fees_id).first()
    if not fees:
        raise HTTPException(status_code=404, detail="Fees receipt not found")

    student_id = fees.student_id
    db.delete(fees)
    db.commit()

    # Delete the stored file if exists
    output_path = Path("uploads/fees") / student_id / f"fees_receipt_{student_id}.pdf"
    if output_path.exists():
        output_path.unlink()

    return {"message": "Fees receipt deleted successfully"}
