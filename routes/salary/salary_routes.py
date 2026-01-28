from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path
from db import get_db
from models.salary.salary_models import TeacherSalary
from models.auth.teacher_models import Teacher
from services.salary_slip_generator import generate_salary_slip
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class Month(str, Enum):
    JANUARY = "January"
    FEBRUARY = "February"
    MARCH = "March"
    APRIL = "April"
    MAY = "May"
    JUNE = "June"
    JULY = "July"
    AUGUST = "August"
    SEPTEMBER = "September"
    OCTOBER = "October"
    NOVEMBER = "November"
    DECEMBER = "December"

router = APIRouter(prefix="/api/salary", tags=["Salary"])

# Pydantic Schemas
class SalaryBase(BaseModel):
    teacher_id: str
    month: Month
    year: int
    basic_salary: float
    pf: float
    si: float
    da: float
    pa: float
    total_salary: float
    transaction_id: Optional[str] = None

class SalaryCreate(SalaryBase):
    pass

class SalaryUpdate(BaseModel):
    month: Optional[Month] = None
    year: Optional[int] = None
    basic_salary: Optional[float] = None
    pf: Optional[float] = None
    si: Optional[float] = None
    da: Optional[float] = None
    pa: Optional[float] = None
    total_salary: Optional[float] = None
    transaction_id: Optional[str] = None

class SalaryOut(SalaryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Create salary slips
@router.post("/create", response_model=List[SalaryOut], status_code=status.HTTP_201_CREATED)
def create_salary_slips(salary_data_list: List[SalaryCreate], db: Session = Depends(get_db)):
    if not salary_data_list:
        raise HTTPException(status_code=400, detail="At least one salary data required")
    
    # Validate all for same teacher and year
    teacher_id = salary_data_list[0].teacher_id
    year = salary_data_list[0].year
    for data in salary_data_list:
        if data.teacher_id != teacher_id or data.year != year:
            raise HTTPException(status_code=400, detail="All salaries must be for the same teacher and year")
    
    # Check if teacher exists
    teacher = db.query(Teacher).filter(Teacher.teacher_id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    created_salaries = []
    for salary_data in salary_data_list:
        # Check if salary for this month/year already exists
        existing = db.query(TeacherSalary).filter(
            TeacherSalary.teacher_id == salary_data.teacher_id,
            TeacherSalary.month == salary_data.month,
            TeacherSalary.year == salary_data.year
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Salary slip already exists for {salary_data.month} {salary_data.year}")
        
        # Create salary entry
        new_salary = TeacherSalary(**salary_data.dict())
        db.add(new_salary)
        created_salaries.append(new_salary)
    
    db.commit()
    for salary in created_salaries:
        db.refresh(salary)
    
    # Generate salary slip with all salaries for the teacher and year
    all_salaries = db.query(TeacherSalary).filter(
        TeacherSalary.teacher_id == teacher_id,
        TeacherSalary.year == year
    ).all()
    
    output_dir = Path("uploads/salary_slips") / teacher_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"salary_slip_{teacher_id}_{year}.jpeg"
    generate_salary_slip(teacher, all_salaries, str(output_path))
    
    return created_salaries

# Update salary slip
@router.put("/update-by/{salary_id}", response_model=SalaryOut)
def update_salary_slip(salary_id: int, update_data: SalaryUpdate, db: Session = Depends(get_db)):
    salary = db.query(TeacherSalary).filter(TeacherSalary.id == salary_id).first()
    if not salary:
        raise HTTPException(status_code=404, detail="Salary slip not found")
    
    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(salary, key, value)
    
    db.commit()
    db.refresh(salary)
    
    # Regenerate slip with all salaries for the teacher and year
    teacher = db.query(Teacher).filter(Teacher.teacher_id == salary.teacher_id).first()
    all_salaries = db.query(TeacherSalary).filter(
        TeacherSalary.teacher_id == salary.teacher_id,
        TeacherSalary.year == salary.year
    ).all()
    
    output_dir = Path("uploads/salary_slips") / salary.teacher_id
    output_path = output_dir / f"salary_slip_{salary.teacher_id}_{salary.year}.jpeg"
    generate_salary_slip(teacher, all_salaries, str(output_path))
    
    return salary

# Fetch salary slips for a teacher
@router.get("/get-by/{teacher_id}", response_model=List[SalaryOut])
def get_salary_slips(teacher_id: str, db: Session = Depends(get_db)):
    salaries = db.query(TeacherSalary).filter(TeacherSalary.teacher_id == teacher_id).all()
    return salaries

# Delete salary slip
@router.delete("/delete-by/{salary_id}", response_model=dict)
def delete_salary_slip(salary_id: int, db: Session = Depends(get_db)):
    salary = db.query(TeacherSalary).filter(TeacherSalary.id == salary_id).first()
    if not salary:
        raise HTTPException(status_code=404, detail="Salary slip not found")
    
    teacher_id = salary.teacher_id
    year = salary.year
    
    db.delete(salary)
    db.commit()
    
    # Regenerate slip with remaining salaries for the teacher and year
    teacher = db.query(Teacher).filter(Teacher.teacher_id == teacher_id).first()
    all_salaries = db.query(TeacherSalary).filter(
        TeacherSalary.teacher_id == teacher_id,
        TeacherSalary.year == year
    ).all()
    
    output_dir = Path("uploads/salary_slips") / teacher_id
    output_path = output_dir / f"salary_slip_{teacher_id}_{year}.jpeg"
    if all_salaries:
        generate_salary_slip(teacher, all_salaries, str(output_path))
    else:
        # If no salaries left, delete the file
        if output_path.exists():
            output_path.unlink()
    
    return {"message": "Salary slip deleted successfully"}
