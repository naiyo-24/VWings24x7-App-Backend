from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base
import enum


class MemberRole(enum.Enum):
    admin = "admin"
    teacher = "teacher"
    student = "student"


class Classroom(Base):
    __tablename__ = "classrooms"

    class_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    photo = Column(String, nullable=True)
    creator_admin_id = Column(String, ForeignKey("admins.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    members = relationship("ClassMember", back_populates="classroom", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="classroom", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Classroom(class_id={self.class_id}, name={self.name})>"


class ClassMember(Base):
    __tablename__ = "class_members"

    id = Column(String, primary_key=True, index=True)
    class_id = Column(String, ForeignKey("classrooms.class_id"), nullable=False)
    user_id = Column(String, nullable=False)
    role = Column(Enum(MemberRole), nullable=False)
    added_by = Column(String, nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    classroom = relationship("Classroom", back_populates="members")

    def __repr__(self):
        return f"<ClassMember(id={self.id}, class_id={self.class_id}, user_id={self.user_id}, role={self.role})>"


class Message(Base):
    __tablename__ = "class_messages"

    message_id = Column(String, primary_key=True, index=True)
    class_id = Column(String, ForeignKey("classrooms.class_id"), nullable=False)
    sender_id = Column(String, nullable=False)
    sender_role = Column(Enum(MemberRole), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    classroom = relationship("Classroom", back_populates="messages")

    def __repr__(self):
        return f"<Message(message_id={self.message_id}, class_id={self.class_id}, sender_id={self.sender_id})>"
