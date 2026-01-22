from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from db import get_db
from models.salary.salary_models import SalarySlip
from models.auth.teacher_models import Teacher
from services.salary_slip_generator import generate_salary_slip_pdf
from datetime import datetime
import os
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/salary-slips", tags=["Salary Slips"])

# Pydantic Schemas
from pydantic import BaseModel

class SalarySlipBase(BaseModel):
	teacher_id: str
	transaction_id: str
	month: str
	year: int
	basic_salary: float
	# percentages
	pa_percent: Optional[float] = 0.0
	da_percent: Optional[float] = 0.0
	pf_percent: Optional[float] = 0.0
	si_percent: Optional[float] = 0.0
	# absolute amount deductions
	deductions: Optional[float] = 0.0

class SalarySlipCreate(SalarySlipBase):
	pass

class SalarySlipUpdate(BaseModel):
	transaction_id: Optional[str] = None
	month: Optional[str] = None
	year: Optional[int] = None
	basic_salary: Optional[float] = None
	pa: Optional[float] = None
	da: Optional[float] = None
	deductions: Optional[float] = None
	provident_fund: Optional[float] = None

class SalarySlipOut(SalarySlipBase):
	id: int
	total_compensation: float
	pdf_path: str
	created_at: datetime
	updated_at: datetime
	class Config:
		orm_mode = True

# Helper to get teacher info
def get_teacher_info(db: Session, teacher_id: str):
	teacher = db.query(Teacher).filter_by(teacher_id=teacher_id).first()
	if not teacher:
		raise HTTPException(status_code=404, detail="Teacher not found")
	return teacher

# POST: Create salary slip
@router.post("/create", response_model=SalarySlipOut, status_code=status.HTTP_201_CREATED)
def create_salary_slip(
	teacher_id: str = Form(...),
	transaction_id: str = Form(...),
	month: str = Form(...),
	year: int = Form(...),
	basic_salary: float = Form(...),
	pa_percent: float = Form(0.0),
	da_percent: float = Form(0.0),
	pf_percent: float = Form(0.0),
	si_percent: float = Form(0.0),
	deductions: float = Form(0.0),
	db: Session = Depends(get_db),
):
	teacher = get_teacher_info(db, teacher_id)
	# compute component amounts from percentages
	pa_amount = (pa_percent / 100.0) * basic_salary
	da_amount = (da_percent / 100.0) * basic_salary
	pf_amount = (pf_percent / 100.0) * basic_salary
	si_amount = (si_percent / 100.0) * basic_salary
	total_comp = basic_salary + da_amount + pa_amount - pf_amount - si_amount - deductions
	# Generate PDF
	# Use single shared PDF per teacher. Regenerate the whole PDF from DB rows.
	pdf_dir = f"uploads/salary_slips/{teacher_id}"
	os.makedirs(pdf_dir, exist_ok=True)
	pdf_filename = f"salary_slip_{teacher_id}.pdf"
	pdf_path = os.path.join(pdf_dir, pdf_filename)

	# create and persist the slip first
	slip = SalarySlip(
		teacher_id=teacher_id,
		transaction_id=transaction_id,
		month=month,
		year=year,
		basic_salary=basic_salary,
		pa=pa_amount,
		da=da_amount,
		deductions=deductions,
		provident_fund=pf_amount,
		si=si_amount,
		total_compensation=total_comp,
		pdf_path=pdf_path,
		created_at=datetime.utcnow(),
		updated_at=datetime.utcnow(),
	)
	db.add(slip)
	db.commit()
	db.refresh(slip)

	# regenerate a single PDF containing all slips for this teacher
	slips = db.query(SalarySlip).filter_by(teacher_id=teacher_id).order_by(SalarySlip.created_at).all()
	slips_data = []
	for s in slips:
		slips_data.append({
			'month': s.month,
			'year': s.year,
			'basic_salary': s.basic_salary,
			'da_amount': s.da,
			'pa_amount': s.pa,
			'deductions': s.deductions,
			'pf_amount': s.provident_fund,
			'si_amount': s.si,
			'transaction_id': s.transaction_id,
			'total_amount': s.total_compensation,
		})

	generate_salary_slip_pdf(pdf_path=pdf_path, teacher=teacher, slips=slips_data)

	# update all slips to point to the shared pdf path
	for s in slips:
		s.pdf_path = pdf_path
	db.commit()

	return slip

# GET: All salary slips
@router.get("/get-all", response_model=List[SalarySlipOut])
def get_all_salary_slips(db: Session = Depends(get_db)):
	return db.query(SalarySlip).all()

# GET: By id
@router.get("/get-by/{id}", response_model=SalarySlipOut)
def get_salary_slip_by_id(id: int, db: Session = Depends(get_db)):
	slip = db.query(SalarySlip).filter_by(id=id).first()
	if not slip:
		raise HTTPException(status_code=404, detail="Salary slip not found")
	return slip


# GET: Serve teacher's shared salary PDF
@router.get("/view/{teacher_id}")
def view_salary_pdf(teacher_id: str, db: Session = Depends(get_db)):
	# Try to obtain a slip for the teacher to read the shared pdf_path
	slip = db.query(SalarySlip).filter_by(teacher_id=teacher_id).order_by(SalarySlip.created_at.desc()).first()
	if not slip or not slip.pdf_path:
		raise HTTPException(status_code=404, detail="Salary PDF not found")
	pdf_path = slip.pdf_path
	if not os.path.exists(pdf_path):
		raise HTTPException(status_code=404, detail="Salary PDF file missing on disk")
	return FileResponse(path=pdf_path, media_type="application/pdf", filename=os.path.basename(pdf_path))

# PUT: Update by id
@router.put("/put-by/{id}", response_model=SalarySlipOut)
def update_salary_slip(
	id: int,
	transaction_id: Optional[str] = Form(None),
	month: Optional[str] = Form(None),
	year: Optional[int] = Form(None),
	basic_salary: Optional[float] = Form(None),
	pa_percent: Optional[float] = Form(None),
	da_percent: Optional[float] = Form(None),
	pf_percent: Optional[float] = Form(None),
	si_percent: Optional[float] = Form(None),
	deductions: Optional[float] = Form(None),
	db: Session = Depends(get_db),
):
	slip = db.query(SalarySlip).filter_by(id=id).first()
	if not slip:
		raise HTTPException(status_code=404, detail="Salary slip not found")
	# Update fields
	if transaction_id is not None:
		slip.transaction_id = transaction_id
	if month is not None:
		slip.month = month
	if year is not None:
		slip.year = year
	# Update fields and recompute amounts if percentages provided
	if basic_salary is not None:
		slip.basic_salary = basic_salary
	# Use provided percentages to compute component amounts
	pa_amount = slip.pa
	da_amount = slip.da
	pf_amount = slip.provident_fund
	si_amount = slip.si
	if pa_percent is not None and slip.basic_salary is not None:
		pa_amount = (pa_percent / 100.0) * slip.basic_salary
		slip.pa = pa_amount
	if da_percent is not None and slip.basic_salary is not None:
		da_amount = (da_percent / 100.0) * slip.basic_salary
		slip.da = da_amount
	if pf_percent is not None and slip.basic_salary is not None:
		pf_amount = (pf_percent / 100.0) * slip.basic_salary
		slip.provident_fund = pf_amount
	if si_percent is not None and slip.basic_salary is not None:
		si_amount = (si_percent / 100.0) * slip.basic_salary
		slip.si = si_amount
	if deductions is not None:
		slip.deductions = deductions
	# Recalculate total (subtract deductions as well)
	slip.total_compensation = (
		(slip.basic_salary or 0) + (slip.da or 0) + (slip.pa or 0) - (slip.provident_fund or 0) - (slip.si or 0) - (slip.deductions or 0)
	)
	slip.updated_at = datetime.utcnow()

	db.commit()
	db.refresh(slip)

	# regenerate the shared PDF for the teacher using all rows
	teacher = get_teacher_info(db, slip.teacher_id)
	pdf_dir = f"uploads/salary_slips/{slip.teacher_id}"
	os.makedirs(pdf_dir, exist_ok=True)
	pdf_filename = f"salary_slip_{slip.teacher_id}.pdf"
	pdf_path = os.path.join(pdf_dir, pdf_filename)

	slips = db.query(SalarySlip).filter_by(teacher_id=slip.teacher_id).order_by(SalarySlip.created_at).all()
	slips_data = []
	for s in slips:
		slips_data.append({
			'month': s.month,
			'year': s.year,
			'basic_salary': s.basic_salary,
			'da_amount': s.da,
			'pa_amount': s.pa,
			'deductions': s.deductions,
			'pf_amount': s.provident_fund,
			'si_amount': s.si,
			'transaction_id': s.transaction_id,
			'total_amount': s.total_compensation,
		})

	generate_salary_slip_pdf(pdf_path=pdf_path, teacher=teacher, slips=slips_data)

	for s in slips:
		s.pdf_path = pdf_path
	db.commit()

	return slip

# DELETE: By id
@router.delete("/delete-by/{id}", response_model=dict)
def delete_salary_slip(id: int, db: Session = Depends(get_db)):
	slip = db.query(SalarySlip).filter_by(id=id).first()
	if not slip:
		raise HTTPException(status_code=404, detail="Salary slip not found")
	# Delete PDF file
	db.delete(slip)
	db.commit()

	# After deletion, regenerate the shared PDF for the teacher (or remove if no slips remain)
	slips = db.query(SalarySlip).filter_by(teacher_id=slip.teacher_id).order_by(SalarySlip.created_at).all()
	pdf_path = None
	if slips:
		pdf_dir = f"uploads/salary_slips/{slip.teacher_id}"
		os.makedirs(pdf_dir, exist_ok=True)
		pdf_filename = f"salary_slip_{slip.teacher_id}.pdf"
		pdf_path = os.path.join(pdf_dir, pdf_filename)
		slips_data = []
		# fetch teacher for header
		teacher = get_teacher_info(db, slip.teacher_id)
		for s in slips:
			slips_data.append({
				'month': s.month,
				'year': s.year,
				'basic_salary': s.basic_salary,
				'da_amount': s.da,
				'pa_amount': s.pa,
				'deductions': s.deductions,
				'pf_amount': s.provident_fund,
				'si_amount': s.si,
				'transaction_id': s.transaction_id,
				'total_amount': s.total_compensation,
			})
		generate_salary_slip_pdf(pdf_path=pdf_path, teacher=teacher, slips=slips_data)
		for s in slips:
			s.pdf_path = pdf_path
		db.commit()
	else:
		# no slips remain: remove pdf file if present
		pdf_dir = f"uploads/salary_slips/{slip.teacher_id}"
		pdf_filename = f"salary_slip_{slip.teacher_id}.pdf"
		pdf_path = os.path.join(pdf_dir, pdf_filename)
		if os.path.exists(pdf_path):
			os.remove(pdf_path)

	return {"message": "Salary slip deleted and PDF regenerated"}
