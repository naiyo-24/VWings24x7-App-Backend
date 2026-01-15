# from datetime import datetime

def generate_teacher_id(created_at):
	"""
	Generate a teacher ID in the format TEACH-XXX where XXX are the last three digits of the timestamp.
	created_at: datetime object
	"""
	timestamp = int(created_at.timestamp())
	last_three = str(timestamp)[-3:]
	return f"TEACH-{last_three}"
