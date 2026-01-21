from fastapi import Query
# REST endpoint: get chat message history (members/admins only)
from pydantic import BaseModel
from fastapi import status
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models.classroom.chatroom_models import ChatMessage
from models.classroom.member_models import Member
from typing import Dict, List
from datetime import datetime

router = APIRouter(prefix="/api/classrooms/chatroom", tags=["Classroom Chatroom"])

# In-memory connection manager for demo (not for production)
class ConnectionManager:
	def __init__(self):
		self.active_connections: Dict[str, List[WebSocket]] = {}  # key: classroom_id

	async def connect(self, classroom_id: str, websocket: WebSocket):
		await websocket.accept()
		if classroom_id not in self.active_connections:
			self.active_connections[classroom_id] = []
		self.active_connections[classroom_id].append(websocket)

	def disconnect(self, classroom_id: str, websocket: WebSocket):
		if classroom_id in self.active_connections:
			self.active_connections[classroom_id].remove(websocket)
			if not self.active_connections[classroom_id]:
				del self.active_connections[classroom_id]

	async def broadcast(self, classroom_id: str, message: dict):
		if classroom_id in self.active_connections:
			for connection in self.active_connections[classroom_id]:
				await connection.send_json(message)

manager = ConnectionManager()


# Helper: check if user is admin in classroom
def is_admin(classroom_id: str, user_id: str, db: Session) -> bool:
	member_row = db.query(Member).filter(Member.classroom_id == classroom_id).first()
	if not member_row:
		return False
	return user_id in member_row.admins

# Helper: check if user is member or admin in classroom
def is_member_or_admin(classroom_id: str, user_id: str, db: Session) -> bool:
	member_row = db.query(Member).filter(Member.classroom_id == classroom_id).first()
	if not member_row:
		return False
	return user_id in member_row.admins or user_id in member_row.members

# WebSocket endpoint for chatroom
@router.websocket("/ws/{classroom_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, classroom_id: str, user_id: str, db: Session = Depends(get_db)):
	# Only allow members or admins to connect
	if not is_member_or_admin(classroom_id, user_id, db):
		await websocket.accept()
		await websocket.send_json({"error": "Not authorized: Only classroom members or admins can join this chatroom."})
		await websocket.close()
		return
	await manager.connect(classroom_id, websocket)
	try:
		while True:
			data = await websocket.receive_json()
			# data should contain: {"message": "...", "sender_type": "teacher"}
			message = data.get("message")
			sender_type = data.get("sender_type")
			if not message or not sender_type:
				await websocket.send_json({"error": "Invalid message format"})
				continue
			# Only allow admins to send
			if not is_admin(classroom_id, user_id, db):
				await websocket.send_json({"error": "Only admins can send messages"})
				continue
			# Save to DB
			chat_msg = ChatMessage(
				classroom_id=classroom_id,
				sender_id=user_id,
				sender_type=sender_type,
				message=message,
				timestamp=datetime.utcnow()
			)
			db.add(chat_msg)
			db.commit()
			# Broadcast to all
			await manager.broadcast(classroom_id, {
				"user_id": user_id,
				"sender_type": sender_type,
				"message": message,
				"timestamp": chat_msg.timestamp.isoformat()
			})
	except WebSocketDisconnect:
		manager.disconnect(classroom_id, websocket)


class ChatMessageOut(BaseModel):
	id: int
	classroom_id: str
	sender_id: str
	sender_type: str
	message: str
	timestamp: datetime

	class Config:
		orm_mode = True

# REST endpoint: get chat message history (members/admins only)
@router.get("/history/{classroom_id}/{user_id}", response_model=List[ChatMessageOut])
def get_chat_history(
	classroom_id: str,
	user_id: str,
	db: Session = Depends(get_db),
	limit: int = Query(50, ge=1, le=200),
	offset: int = Query(0, ge=0)
):
	# Only allow members or admins to view
	if not is_member_or_admin(classroom_id, user_id, db):
		raise HTTPException(status_code=403, detail="Not authorized: Only classroom members or admins can view chat history.")
	messages = db.query(ChatMessage).filter(ChatMessage.classroom_id == classroom_id)
	messages = messages.order_by(ChatMessage.timestamp.desc()).offset(offset).limit(limit).all()
	return list(reversed(messages))  # Return in chronological order


# REST endpoint: delete a chat message (admin only)
@router.delete("/delete/{classroom_id}/{user_id}/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat_message(classroom_id: str, user_id: str, message_id: int, db: Session = Depends(get_db)):
	# Only allow admin to delete
	if not is_admin(classroom_id, user_id, db):
		raise HTTPException(status_code=403, detail="Only admins can delete messages")
	chat_msg = db.query(ChatMessage).filter(ChatMessage.id == message_id, ChatMessage.classroom_id == classroom_id).first()
	if not chat_msg:
		raise HTTPException(status_code=404, detail="Message not found")
	db.delete(chat_msg)
	db.commit()
	return