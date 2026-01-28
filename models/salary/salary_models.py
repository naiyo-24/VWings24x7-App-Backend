from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base

class TeacherSalary(Base):
    __tablename__ = "teacher_salaries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    teacher_id = Column(String, ForeignKey("teachers.teacher_id"), nullable=False)
    month = Column(String, nullable=False)  # Month name: January, February, etc.
    year = Column(Integer, nullable=False)
    basic_salary = Column(Float, nullable=False)
    pf = Column(Float, nullable=False)
    si = Column(Float, nullable=False)
    da = Column(Float, nullable=False)
    pa = Column(Float, nullable=False)
    total_salary = Column(Float, nullable=False)
    transaction_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    teacher = relationship("Teacher", back_populates="salaries")

    def __repr__(self):
        return f"<TeacherSalary(id={self.id}, teacher_id={self.teacher_id}, month={self.month}, year={self.year})>"
