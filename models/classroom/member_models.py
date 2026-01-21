from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.mutable import MutableList
from db import Base

class Member(Base):
	__tablename__ = "classroom_members"

	id = Column(String, primary_key=True, index=True)
	classroom_id = Column(String, ForeignKey("classrooms.class_id"), nullable=False, index=True)
	members = Column(MutableList.as_mutable(JSONB), nullable=False, default=list)  # List of student IDs
	admins = Column(MutableList.as_mutable(JSONB), nullable=False, default=list)   # List of teacher IDs
	created_at = Column(DateTime(timezone=True), server_default=func.now())
	updated_at = Column(DateTime(timezone=True), onupdate=func.now())

	classroom = relationship("Classroom", backref="classroom_members")
