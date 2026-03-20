from pathlib import Path
import json

def get_attempt(student_id, module, method):
    path = Path(f"submissions/{student_id}.json")
    if not path.exists():
        return 0
    else:
        with open(path, "r") as f:
            data = json.load(f)
        return data.get(module, {}).get(method, 0)

def increment_attempt(student_id, module, method):
    path = Path(f"submissions/{student_id}.json")
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
    path = Path(f"submissions/{student_id}.json")
    if path.exists():
        with open(path, "r") as f:
            data = json.load(f)
        if module in data:
            data[module][method] = 0
            if not data[module]:
                del data[module]
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
