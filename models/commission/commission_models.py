from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from db import Base
from datetime import datetime


class Commission(Base):
    __tablename__ = "commissions"

    commission_id = Column(String, primary_key=True, index=True)
    counsellor_id = Column(String, ForeignKey("counsellors.counsellor_id"), nullable=False, index=True)
    enquiry_id = Column(String, ForeignKey("admission_enquiries.enquiry_id"), nullable=False, index=True)

    student_name = Column(String, nullable=False)
    course_id = Column(String, nullable=False)
    course_name = Column(String, nullable=True)

    commission_percentage = Column(Float, nullable=False, default=0.0)
    course_fees = Column(Float, nullable=False, default=0.0)
    commission_amount = Column(Float, nullable=False, default=0.0)

    pdf_path = Column(String, nullable=True)

    transaction_id = Column(String, nullable=True)
    payment_status = Column(String, nullable=True, default='pending')

    month_year = Column(String, nullable=False)  # format YYYY-MM

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Commission(commission_id={self.commission_id}, counsellor_id={self.counsellor_id}, amount={self.commission_amount})>"
