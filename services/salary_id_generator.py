from datetime import datetime

def generate_salary_id(created_at: datetime):
	"""
	Generate a salary ID in the format SAL-XXX where XXX are the last three digits of the timestamp.
	"""
	ts = int(created_at.timestamp())
	return f"SAL-{str(ts)[-3:]}"

