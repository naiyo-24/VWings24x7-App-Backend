from sqlalchemy import Column, String, Text, Boolean, JSON
from db import Base

class Course(Base):
    __tablename__ = "courses"

    # Primary key
    course_id = Column(String, primary_key=True, index=True)

    # Common fields
    course_name = Column(String, nullable=False)
    course_description = Column(Text)
    course_code = Column(String, nullable=False, unique=True, index=True)
    weight_requirements = Column(String)
    height_requirements = Column(String)
    vision_standards = Column(String)
    medical_requirements = Column(Text)
    min_educational_qualification = Column(String)
    age_criteria = Column(String)
    internship_included = Column(Boolean, default=False)
    installment_available = Column(Boolean, default=False)
    installment_policy = Column(Text)
    course_photo = Column(String)  # File path
    course_video = Column(String)  # File path

    # JSONB columns for category-specific data
    general_data = Column(JSON, nullable=True)
    executive_data = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<Course(course_id={self.course_id}, course_name={self.course_name})>"
