from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from datetime import datetime
from db import Base


class Salary(Base):
    __tablename__ = "salaries"

    salary_id = Column(String, primary_key=True, index=True)
    teacher_id = Column(String, ForeignKey("teachers.teacher_id"), nullable=False, index=True)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Salary(salary_id={self.salary_id}, teacher_id={self.teacher_id}, month={self.month}, year={self.year})>"
