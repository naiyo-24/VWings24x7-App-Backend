from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base


class FeesReceipt(Base):
    __tablename__ = "fees_receipts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, ForeignKey("students.student_id"), nullable=False, unique=True)
    payment_no = Column(Integer, nullable=True)
    payment_mode = Column(String, nullable=True)
    transaction_id = Column(String, nullable=True)
    amount = Column(Float, nullable=False, default=0.0)
    total_course_fees = Column(Float, nullable=False, default=0.0)
    amount_paid = Column(Float, nullable=False, default=0.0)
    amount_due = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # relationship to Student
    student = relationship("Student", backref="fees_receipt")

    def __repr__(self):
        return f"<FeesReceipt(id={self.id}, student_id={self.student_id}, amount_paid={self.amount_paid})>"
