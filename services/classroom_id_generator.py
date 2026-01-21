import time

def generate_class_id():
    """
    Generate a unique class ID in the format: CLASS-<timestamp>
    """
    timestamp = int(time.time() * 1000)
    return f"CLASS-{timestamp}"
