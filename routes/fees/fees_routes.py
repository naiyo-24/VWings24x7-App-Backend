from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import os
import json

from db import get_db
from models.fees.fees_models import Fees
from models.auth.student_models import Student
from models.courses.course_models import Course
from services.fees_pdf_generator import generate_fees_pdf
from services.fees_pdf_generator import generate_consolidated_fees_pdf
from uuid import uuid4

router = APIRouter(prefix="/api/fees", tags=["Fees"])


class InstallmentItem(BaseModel):
    installment_no: int
    transaction_id: str
    amount_paid: float
    paid_at: Optional[str] = None


class FeesCreate(BaseModel):
    student_id: str
    course_id: str
    course_category: Optional[str] = "general"
    installments: Optional[List[InstallmentItem]] = None


class FeesResponse(BaseModel):
    fee_id: str
    student_id: str
    course_id: str
    course_category: Optional[str]
    total_course_fees: float
    installments: Optional[List[dict]]
    total_paid: float
    total_due: float
    pdf_path: Optional[str]
    consolidated_pdf_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


def _compute_totals(course: Course, category: str, installments: Optional[List[dict]]):
    # Resolve course fees from course.general_data or executive_data
    total_course_fees = 0.0
    cat_field = "general_data" if category != "executive" else "executive_data"
    data = getattr(course, cat_field, None) or {}
    try:
        total_course_fees = float(data.get("course_fees", 0) or 0)
    except Exception:
        total_course_fees = 0.0

    total_paid = 0.0
    for inst in (installments or []):
        amt = inst.get("amount_paid", 0)
        try:
            total_paid += float(amt)
        except Exception:
            pass

    total_due = max(0.0, total_course_fees - total_paid)
    return total_course_fees, total_paid, total_due


@router.post("/create", response_model=FeesResponse, status_code=status.HTTP_201_CREATED)
def create_fees(payload: FeesCreate, db: Session = Depends(get_db)):
    student = db.query(Student).filter_by(student_id=payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    course = db.query(Course).filter_by(course_id=payload.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    fee_id = f"FEES-{uuid4().hex[:8]}"
    inst_list = [i.dict() for i in (payload.installments or [])]
    total_course_fees, total_paid, total_due = _compute_totals(course, payload.course_category, inst_list)

    fee = Fees(
        fee_id=fee_id,
        student_id=payload.student_id,
        course_id=payload.course_id,
        course_category=payload.course_category,
        total_course_fees=total_course_fees,
        installments=inst_list,
        total_paid=total_paid,
        total_due=total_due,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(fee)
    db.commit()
    db.refresh(fee)

    # generate pdf
    uploads_dir = os.path.join("uploads", "fees", payload.student_id)
    pdf_path = generate_fees_pdf(uploads_dir, {
        "fee_id": fee.fee_id,
        "student": {k: getattr(student, k) for k in ["student_id", "full_name", "phone_no", "email", "address"]},
        "course": {"course_id": course.course_id, "course_name": course.course_name},
        "installments": inst_list,
        "totals": {"total_course_fees": total_course_fees, "total_paid": total_paid, "total_due": total_due},
    })

    # store relative path
    rel_pdf = os.path.relpath(pdf_path, os.getcwd())
    fee.pdf_path = rel_pdf
    db.add(fee)
    db.commit()
    db.refresh(fee)

    # regenerate consolidated pdf for student and include path in response
    consolidated = None
    try:
        consolidated = _regenerate_consolidated_pdf_for_student(payload.student_id, db)
    except Exception:
        consolidated = None

    out = {**fee.__dict__}
    out["consolidated_pdf_path"] = consolidated
    return FeesResponse(**out)


def _regenerate_consolidated_pdf_for_student(student_id: str, db: Session):
    # gather all fee records for student and combine installments
    fees = db.query(Fees).filter_by(student_id=student_id).all()
    if not fees:
        return None
    student = db.query(Student).filter_by(student_id=student_id).first()
    all_installments = []
    totals_course_fees = 0.0
    totals_paid = 0.0
    for f in fees:
        for inst in (f.installments or []):
            inst_copy = dict(inst)
            inst_copy.setdefault("course_name", None)
            # try to get course name
            try:
                course = db.query(Course).filter_by(course_id=f.course_id).first()
                inst_copy["course_name"] = course.course_name if course else None
            except Exception:
                inst_copy["course_name"] = None
            all_installments.append(inst_copy)
        totals_course_fees += float(f.total_course_fees or 0)
        totals_paid += float(f.total_paid or 0)

    totals_due = max(0.0, totals_course_fees - totals_paid)

    uploads_dir = os.path.join("uploads", "fees", student_id)
    pdf_path = generate_consolidated_fees_pdf(uploads_dir, {"student_id": student_id, **(student.__dict__ if student else {})}, all_installments, {"total_course_fees": totals_course_fees, "total_paid": totals_paid, "total_due": totals_due})
    return os.path.relpath(pdf_path, os.getcwd())


@router.get("/get-by/{fee_id}", response_model=FeesResponse)
def get_fee_by_id(fee_id: str, db: Session = Depends(get_db)):
    fee = db.query(Fees).filter_by(fee_id=fee_id).first()
    if not fee:
        raise HTTPException(status_code=404, detail="Fee record not found")

    # regenerate consolidated pdf for student and include path in response
    consolidated = None
    try:
        consolidated = _regenerate_consolidated_pdf_for_student(fee.student_id, db)
    except Exception:
        consolidated = None

    out = {**fee.__dict__}
    out["consolidated_pdf_path"] = consolidated
    return FeesResponse(**out)


@router.get("/get-by/student/{student_id}", response_model=List[FeesResponse])
def get_fees_by_student(student_id: str, db: Session = Depends(get_db)):
    items = db.query(Fees).filter_by(student_id=student_id).all()
    return [FeesResponse(**f.__dict__) for f in items]


@router.put("/put-by/{fee_id}", response_model=FeesResponse)
def update_fee(fee_id: str, payload: FeesCreate, db: Session = Depends(get_db)):
    fee = db.query(Fees).filter_by(fee_id=fee_id).first()
    if not fee:
        raise HTTPException(status_code=404, detail="Fee record not found")
    student = db.query(Student).filter_by(student_id=payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    course = db.query(Course).filter_by(course_id=payload.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    inst_list = [i.dict() for i in (payload.installments or [])]
    total_course_fees, total_paid, total_due = _compute_totals(course, payload.course_category, inst_list)

    fee.student_id = payload.student_id
    fee.course_id = payload.course_id
    fee.course_category = payload.course_category
    fee.installments = inst_list
    fee.total_course_fees = total_course_fees
    fee.total_paid = total_paid
    fee.total_due = total_due
    fee.updated_at = datetime.utcnow()

    # regenerate pdf
    uploads_dir = os.path.join("uploads", "fees", payload.student_id)
    pdf_path = generate_fees_pdf(uploads_dir, {
        "fee_id": fee.fee_id,
        "student": {k: getattr(student, k) for k in ["student_id", "full_name", "phone_no", "email", "address"]},
        "course": {"course_id": course.course_id, "course_name": course.course_name},
        "installments": inst_list,
        "totals": {"total_course_fees": total_course_fees, "total_paid": total_paid, "total_due": total_due},
    })
    fee.pdf_path = os.path.relpath(pdf_path, os.getcwd())

    db.add(fee)
    db.commit()
    db.refresh(fee)
    # regenerate consolidated pdf for student and include path in response
    consolidated = None
    try:
        consolidated = _regenerate_consolidated_pdf_for_student(payload.student_id, db)
    except Exception:
        consolidated = None
    out = {**fee.__dict__}
    out["consolidated_pdf_path"] = consolidated
    return FeesResponse(**out)


@router.get("/student/{student_id}/consolidated-pdf")
def get_consolidated_pdf(student_id: str, db: Session = Depends(get_db)):
    student = db.query(Student).filter_by(student_id=student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    path = _regenerate_consolidated_pdf_for_student(student_id, db)
    if not path:
        raise HTTPException(status_code=404, detail="No fee records for student")
    return {"pdf_path": path}
