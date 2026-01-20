from datetime import datetime
import random

def generate_class_id(now: datetime = None) -> str:
    now = now or datetime.utcnow()
    return f"CLASS{now.strftime('%Y%m%d%H%M%S')}{random.randint(100,999)}"
