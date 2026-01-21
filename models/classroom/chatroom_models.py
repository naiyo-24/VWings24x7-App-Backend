
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.sql import func
from db import Base

class ChatMessage(Base):
	__tablename__ = "classroom_chat_messages"

	id = Column(Integer, primary_key=True, autoincrement=True)
	classroom_id = Column(String, ForeignKey("classrooms.class_id"), nullable=False, index=True)
	sender_id = Column(String, nullable=False)
	sender_type = Column(String, nullable=False)  # 'teacher' or 'student'
	message = Column(String, nullable=False)
	timestamp = Column(DateTime(timezone=True), server_default=func.now())
