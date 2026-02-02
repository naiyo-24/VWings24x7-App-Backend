from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from datetime import datetime
from db import Base


class Fee(Base):
    __tablename__ = "fees"

    fee_id = Column(String, primary_key=True, index=True)
    student_id = Column(String, ForeignKey("students.student_id"), nullable=False, index=True)
    installment_no = Column(Integer, nullable=False)
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Fee(fee_id={self.fee_id}, student_id={self.student_id}, installment_no={self.installment_no})>"
