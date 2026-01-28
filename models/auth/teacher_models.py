from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base

class Teacher(Base):
	__tablename__ = "teachers"

	teacher_id = Column(String, primary_key=True, index=True)
	full_name = Column(String, nullable=False)
	phone_no = Column(String, nullable=False, unique=True)
	email = Column(String, nullable=False, unique=True)
	alternative_phone_no = Column(String)
	address = Column(String)
	qualification = Column(String)
	experience = Column(String)
	# courses_assigned: list of dicts [{course_id, course_name}]
	courses_assigned = Column(JSON, nullable=True)
	profile_photo = Column(String, nullable=True)  # File path to profile photo
	bank_account_no = Column(String)
	bank_account_name = Column(String)
	bank_branch_name = Column(String)
	ifsc_code = Column(String)
	upiid = Column(String)
	monthly_salary = Column(Float)
	created_at = Column(DateTime, default=datetime.utcnow)
	updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
	password = Column(String, nullable=False)

	# Relationship to salaries
	salaries = relationship("TeacherSalary", back_populates="teacher")

	def __repr__(self):
		return f"<Teacher(teacher_id={self.teacher_id}, full_name={self.full_name})>"
