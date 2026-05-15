import os
import sys
import json
import subprocess
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add project root to path so we can import autograder modules
sys.path.insert(0, str(Path(__file__).parent.parent))

app = Flask(__name__)
CORS(app)


def load_course_configs() -> dict:
    """
    Dynamically load all course configs from the configs/ directory.
    Returns a dict mapping assignment_id -> config_path.
    """
    assignment_map = {}
    configs_dir = Path("configs")

    for config_file in configs_dir.glob("*.json"):
        try:
            with open(config_file) as f:
                config = json.load(f)

            # handle module-style configs (m4, m5, etc.)
            assignment_id = config.get("canvas_assignment_id")
            if assignment_id and assignment_id != "TBD":
                assignment_map[str(assignment_id)] = str(config_file)

            # handle course-style configs (course_204637.json)
            for assignment in config.get("assignments", []):
                aid = str(assignment.get("id", ""))
                if aid:
                    assignment_map[aid] = str(config_file)

        except Exception:
            continue

    return assignment_map


@app.route('/ping', methods=['GET'])
def ping():
    """Health check endpoint for the extension popup."""
    return jsonify({"status": "ok"})


@app.route('/grade', methods=['POST'])
def grade():
    """
    Receive course_id and assignment_id from the extension,
    run the autograder, and return the output.
    """
    data = request.get_json()
    assignment_id = str(data.get("assignment_id", ""))
    canvas_token = os.getenv("CANVAS_TOKEN", "")

    # dynamically look up config
    assignment_map = load_course_configs()
    config_path = assignment_map.get(assignment_id)

    if not config_path:
        return jsonify({"error": f"No config found for assignment {assignment_id}"}), 400

    try:
        result = subprocess.run(
            [sys.executable, "-m", "scripts.grade_submissions", config_path],
            capture_output=True,
            text=True,
            timeout=300,
            env={**os.environ, "CANVAS_TOKEN": canvas_token}
        )
        output = result.stdout or result.stderr or "No output."
    except subprocess.TimeoutExpired:
        output = "Autograder timed out."
    except Exception as e:
        output = f"Error running autograder: {e}"

    return jsonify({"output": output})


if __name__ == "__main__":
    app.run(debug=True, port=5000)