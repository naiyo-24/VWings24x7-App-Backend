from datetime import datetime


def generate_commission_id(created_at: datetime):
    """
    Generate a commission ID in the format COMM-XXX where XXX are the last three digits of the timestamp.
    """
    timestamp = int(created_at.timestamp())
    last_three = str(timestamp)[-3:]
    return f"COMM-{last_three}"
