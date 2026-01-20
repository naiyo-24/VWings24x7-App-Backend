from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import json
from db import SessionLocal
from models.classroom.classroom_models import ClassMember, MemberRole, Message
from services.message_id_generator import generate_message_id
from services.ws_manager import manager

router = APIRouter()


@router.websocket("/ws/classes/{class_id}")
async def classroom_ws(websocket: WebSocket, class_id: str, user_id: Optional[str] = Query(None)):
    """WebSocket endpoint for classroom chat.
    Query param `user_id` is required (use your auth token system in production).
    """
    if not user_id:
        await websocket.close(code=4001)
        return

    await websocket.accept()

    db = SessionLocal()
    try:
        member = db.query(ClassMember).filter_by(class_id=class_id, user_id=user_id).first()
        if not member:
            await websocket.send_json({"type": "error", "code": 403, "detail": "Not a member of this class"})
            await websocket.close(code=4003)
            return

        # connect
        conn = await manager.connect(class_id, websocket, user_id, member.role.value)

        # send recent messages
        recent = db.query(Message).filter_by(class_id=class_id).order_by(Message.created_at.desc()).limit(50).all()
        recent_payload = [
            {
                "message_id": m.message_id,
                "class_id": m.class_id,
                "sender_id": m.sender_id,
                "sender_role": m.sender_role.value,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
            }
            for m in reversed(recent)
        ]
        await websocket.send_json({"type": "history", "messages": recent_payload})

        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
            except Exception:
                await websocket.send_json({"type": "error", "detail": "Invalid JSON"})
                continue

            action = payload.get("action")
            if action == "send":
                # only teachers/admins may send
                if member.role not in (MemberRole.teacher, MemberRole.admin):
                    await websocket.send_json({"type": "error", "code": 403, "detail": "Only teachers may send messages"})
                    continue
                content = payload.get("content")
                if not content:
                    await websocket.send_json({"type": "error", "detail": "Empty message"})
                    continue

                # persist message
                msg = Message(
                    message_id=generate_message_id(),
                    class_id=class_id,
                    sender_id=user_id,
                    sender_role=member.role,
                    content=content,
                )
                db.add(msg)
                db.commit()
                db.refresh(msg)

                out = {
                    "type": "message",
                    "message_id": msg.message_id,
                    "class_id": msg.class_id,
                    "sender_id": msg.sender_id,
                    "sender_role": msg.sender_role.value,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                }
                await manager.broadcast(class_id, out)

            else:
                await websocket.send_json({"type": "error", "detail": "Unknown action"})

    except WebSocketDisconnect:
        pass
    finally:
        try:
            await manager.disconnect(class_id, conn)
        except Exception:
            pass
        db.close()
