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
CORS(app)  # Allow requests from the Chrome extension

# Map Canvas assignment IDs to configs
ASSIGNMENT_CONFIG_MAP = {
    "2371092": "configs/m4_sorts.json",
    "2371093": "configs/m5_data_structures.json",
    "2406059": "configs/m6_dp.json",
    "2406060": "configs/m7_graphs.json",
}


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

    config_path = ASSIGNMENT_CONFIG_MAP.get(assignment_id)
    if not config_path:
        return jsonify({"error": f"No config found for assignment {assignment_id}"}), 400

    # Run grade_submissions which pulls from Canvas and runs the driver
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