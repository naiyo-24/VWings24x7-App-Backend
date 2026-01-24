from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from datetime import datetime
from db import Base


class Classroom(Base):
	__tablename__ = "classrooms"

	class_id = Column(String, primary_key=True, index=True)
	class_name = Column(String, nullable=False)
	class_description = Column(String, nullable=True)
	class_photo = Column(String, nullable=True)  # Path to photo file
	# List of teacher ids (stored as JSON array). Use application-level checks to enforce referential integrity.
	teacher_ids = Column(JSON, nullable=True)
	# Admin who created/owns the class (FK to admins.id)
	admin_id = Column(String, ForeignKey("admins.id"), nullable=True)
	# List of student ids (stored as JSON array)
	student_ids = Column(JSON, nullable=True)
	created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
	updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

