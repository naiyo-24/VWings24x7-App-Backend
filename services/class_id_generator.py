from datetime import datetime
import re


def _slugify(text: str) -> str:
	if not text:
		return ""
	text = text.lower()
	text = re.sub(r"[^a-z0-9]+", "-", text)
	text = re.sub(r"-+", "-", text).strip("-")
	return text[:40]


def generate_class_id(class_name: str = None) -> str:
	"""Generate a class id using a timestamp and an optional slugified class name.

	Example: CLASS-20260124123456-math-101
	"""
	ts = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")[:-3]
	name_part = _slugify(class_name) if class_name else ""
	if name_part:
		return f"CLASS-{ts}-{name_part}"
	return f"CLASS-{ts}"
