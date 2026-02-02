from datetime import datetime

def generate_fee_id(created_at: datetime):
    """
    Generate a fee ID in the format FEE-XXX where XXX are the last three digits of the timestamp.
    """
    ts = int(created_at.timestamp())
    return f"FEE-{str(ts)[-3:]}"
