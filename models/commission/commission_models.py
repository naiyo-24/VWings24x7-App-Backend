from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UniqueConstraint
from datetime import datetime
from db import Base


class CommissionSlip(Base):
    __tablename__ = "commission_slips"
    __table_args__ = (UniqueConstraint('counsellor_id', 'month', 'year', name='uix_counsellor_month_year'),)

    commission_id = Column(String, primary_key=True, index=True)
    counsellor_id = Column(String, ForeignKey("counsellors.counsellor_id"), nullable=False, index=True)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    file_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<CommissionSlip(commission_id={self.commission_id}, counsellor_id={self.counsellor_id}, month={self.month}, year={self.year})>"
