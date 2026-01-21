from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from db import Base

class Classroom(Base):
    __tablename__ = "classrooms"

    class_id = Column(String, primary_key=True, index=True)
    class_name = Column(String, nullable=False)
    class_description = Column(String, nullable=True)
    class_photo = Column(String, nullable=True)  # Path to photo file
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
