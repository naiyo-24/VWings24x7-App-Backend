from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import os
from uuid import uuid4

from db import get_db
from models.commission.commission_models import Commission
from models.auth.counsellor_models import Counsellor
from models.courses.course_models import Course
from models.admission.admission_enquiry_models import AdmissionEnquiry
from services.commission_pdf_generator import generate_commission_pdf
from routes.auth.counsellor_routes import format_per_courses_commission_for_output

router = APIRouter(prefix="/api/commissions", tags=["Commissions"])


class CommissionOut(BaseModel):
    commission_id: str
    counsellor_id: str
    enquiry_id: str
    student_name: str
    course_id: str
    course_name: Optional[str]
    commission_percentage: float
    course_fees: float
    commission_amount: float
    pdf_path: Optional[str]
    month_year: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


def create_commission_for_enquiry(enquiry: AdmissionEnquiry, db: Session) -> Optional[str]:
    # build commission using enquiry + counsellor config
    if not enquiry or not enquiry.counsellor_id:
        return None

    counsellor = db.query(Counsellor).filter_by(counsellor_id=enquiry.counsellor_id).first()
    course = db.query(Course).filter_by(course_id=enquiry.course_id).first() if enquiry.course_id else None

    # resolve course fees (take general_data.course_fees by default)
    course_fees = 0.0
    if course:
        data = getattr(course, 'general_data', None) or {}
        try:
            course_fees = float(data.get('course_fees', 0) or 0)
        except Exception:
            course_fees = 0.0

    # resolve commission percentage
    commission_pct = 0.0
    if counsellor:
        per_courses = format_per_courses_commission_for_output(db, getattr(counsellor, 'per_courses_commission', None))
        entry = per_courses.get(enquiry.course_id) if per_courses else None
        if entry:
            commission_pct = float(entry.get('commission', 0) or 0)

    commission_amount = (course_fees * commission_pct / 100.0) if course_fees and commission_pct else 0.0

    month_year = datetime.utcnow().strftime("%Y-%m")
    commission_id = f"COM-{uuid4().hex[:8]}"

    comm = Commission(
        commission_id=commission_id,
        counsellor_id=enquiry.counsellor_id,
        enquiry_id=enquiry.enquiry_id,
        student_name=enquiry.student_name,
        course_id=enquiry.course_id,
        course_name=course.course_name if course else None,
        commission_percentage=commission_pct,
        course_fees=course_fees,
        commission_amount=commission_amount,
        month_year=month_year,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(comm)
    db.commit()
    db.refresh(comm)

    # generate pdf into uploads/commission/{counsellor_id}/{YYYY-MM}/
    uploads_dir = os.path.join('uploads', 'commission', comm.counsellor_id, comm.month_year)
    pdf_path = generate_commission_pdf(uploads_dir, {
        'commission_id': comm.commission_id,
        'student_name': comm.student_name,
        'enquiry_id': comm.enquiry_id,
        'course_id': comm.course_id,
        'course_name': comm.course_name,
        'commission_percentage': comm.commission_percentage,
        'course_fees': comm.course_fees,
        'commission_amount': comm.commission_amount,
        'month_year': comm.month_year,
    })

    rel = os.path.relpath(pdf_path, os.getcwd())
    comm.pdf_path = rel
    db.add(comm)
    db.commit()
    db.refresh(comm)

    return rel


@router.get('/get-by/{commission_id}', response_model=CommissionOut)
def get_commission(commission_id: str, db: Session = Depends(get_db)):
    c = db.query(Commission).filter_by(commission_id=commission_id).first()
    if not c:
        raise HTTPException(status_code=404, detail='Commission not found')
    return CommissionOut(**c.__dict__)


@router.get('/get-by/counsellor/{counsellor_id}', response_model=List[CommissionOut])
def get_commissions_by_counsellor(counsellor_id: str, month: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Commission).filter_by(counsellor_id=counsellor_id)
    if month:
        q = q.filter_by(month_year=month)
    items = q.all()
    return [CommissionOut(**i.__dict__) for i in items]
