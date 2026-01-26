from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base


class AdmissionEnquiry(Base):
    __tablename__ = "admission_enquiries"

    enquiry_id = Column(String, primary_key=True, index=True)

    counsellor_id = Column(String, ForeignKey("counsellors.counsellor_id"), nullable=False, index=True)

    student_name = Column(String, nullable=False)
    student_phn_no = Column(String, nullable=False)
    student_alternative_phn_no = Column(String, nullable=True)
    student_email = Column(String, nullable=True)
    student_address = Column(Text, nullable=True)

    guardian_name = Column(String, nullable=True)
    guardian_phn_no = Column(String, nullable=True)

    fit_medically = Column(Boolean, default=False)
    meets_height_requirements = Column(Boolean, default=False)
    meets_weight_requirements = Column(Boolean, default=False)
    meets_vision_standards = Column(Boolean, default=False)

    admission_code = Column(String, ForeignKey("admission_codes.admission_code"), nullable=False, index=True)

    # optional course reference
    course_id = Column(String, ForeignKey("courses.course_id"), nullable=True, index=True)

    # category of course for this enquiry: 'general' or 'executive'
    course_category = Column(String, nullable=True, default="general")

    status = Column(String, nullable=False, default="pending")  # converted/contacted/cancelled/pending

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    counsellor = relationship("Counsellor", backref="admission_enquiries")
    admission_code_rel = relationship("AdmissionCode", backref="admission_enquiries")
    course = relationship("Course", backref="admission_enquiries")

    def __repr__(self):
        return f"<AdmissionEnquiry(enquiry_id={self.enquiry_id}, student_name={self.student_name}, status={self.status})>"
