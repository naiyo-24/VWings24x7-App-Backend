from datetime import datetime
import random

def generate_message_id(now: datetime = None) -> str:
    now = now or datetime.utcnow()
    return f"MSG{now.strftime('%Y%m%d%H%M%S')}{random.randint(1000,9999)}"
