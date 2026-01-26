from sqlalchemy import Column, String, Float, DateTime, JSON, ForeignKey
from datetime import datetime
from db import Base


class Fees(Base):
    __tablename__ = "fees"

    fee_id = Column(String, primary_key=True, index=True)
    student_id = Column(String, ForeignKey("students.student_id"), nullable=False, index=True)
    course_id = Column(String, ForeignKey("courses.course_id"), nullable=False, index=True)
    course_category = Column(String, nullable=True)
    total_course_fees = Column(Float, nullable=False, default=0.0)
    installments = Column(JSON, nullable=True)  # list of {installment_no, transaction_id, amount_paid, paid_at}
    total_paid = Column(Float, nullable=False, default=0.0)
    total_due = Column(Float, nullable=False, default=0.0)
    pdf_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Fees(fee_id={self.fee_id}, student_id={self.student_id}, course_id={self.course_id})>"
