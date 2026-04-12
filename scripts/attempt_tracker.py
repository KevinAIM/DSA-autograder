from pathlib import Path
import json
import os


def _attempt_path(student_id):
    override = os.getenv("ATTEMPT_TRACKER_PATH")
    if override:
        return Path(override)
    return Path(f"submissions/{student_id}.json")

def get_attempt(student_id, module, method):
    path = _attempt_path(student_id)
    if not path.exists():
        return 0
    else:
        with open(path, "r") as f:
            data = json.load(f)
        return data.get(module, {}).get(method, 0)

def increment_attempt(student_id, module, method):
    path = _attempt_path(student_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    data = {}
    if path.exists():
        with open(path, "r") as f:
            data = json.load(f)
    
    if module not in data:
        data[module] = {}
    data[module][method] = data.get(module, {}).get(method, 0) + 1
    
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def reset_attempt(student_id, module, method):
    path = _attempt_path(student_id)
    if path.exists():
        with open(path, "r") as f:
            data = json.load(f)
        if module in data:
            data[module][method] = 0
            if not data[module]:
                del data[module]
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
