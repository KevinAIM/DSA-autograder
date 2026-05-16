import sys
import json
import os
import requests
import tempfile
import shutil
import subprocess
from pathlib import Path
from openai import OpenAI
from scripts.attempt_tracker import get_attempt, increment_attempt, reset_attempt


CANVAS_BASE = "https://montclair.instructure.com"

def get_submissions(course_id: str, assignment_id: str, canvas_token: str) -> list:
    headers = {"Authorization": f"Bearer {canvas_token}"}
    params = {"include[]": "attachments"}

    # try teacher endpoint first
    url = f"{CANVAS_BASE}/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions"
    r = requests.get(url, headers=headers, params={**params, "per_page": 100})
    
    if r.status_code == 403:
        # fall back to current user's own submission
        url = f"{CANVAS_BASE}/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/self"
        r = requests.get(url, headers=headers, params=params)
    
    r.raise_for_status()
    data = r.json()
    return [data] if isinstance(data, dict) else data


def download_attachment(attachment: dict, dest_path: Path, canvas_token: str) -> bool:
    url = attachment.get("url")
    if not url:
        return False
    r = requests.get(url, headers={"Authorization": f"Bearer {canvas_token}"}, stream=True)
    if r.status_code != 200:
        return False
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dest_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    return True


def fetch_canvas_file(file_id: str, canvas_token: str) -> str:
    """Download a Canvas file by ID and return its text content."""
    url = f"{CANVAS_BASE}/files/{file_id}/download?download_frd=1"
    r = requests.get(url, headers={"Authorization": f"Bearer {canvas_token}"})
    r.raise_for_status()
    return r.text


def llm_grade(student_source: str, skeleton_source: str, solution_source: str,
              assignment_name: str, attempt: int) -> str:
    """Use LLM to grade student code statically. Returns formatted feedback string."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return "[LLM grading unavailable — no API key]"

    client = OpenAI(api_key=api_key)

    if attempt == 1:
        hint_level = "Give a vague hint only. Point to the relevant concept but do not reveal the fix."
    elif attempt == 2:
        hint_level = "Give a more specific hint referencing the relevant part of the code."
    elif attempt == 3:
        hint_level = "Give a detailed explanation of what is wrong and why, without giving the solution."
    else:
        hint_level = "Give the full solution with a complete explanation."

    solution_section = f"\nREFERENCE SOLUTION:\n{solution_source}" if solution_source else ""

    prompt = f"""You are a TA grading a programming assignment called '{assignment_name}'.

HINT LEVEL (follow strictly): {hint_level}

SKELETON (what the student was given):
{skeleton_source}
{solution_section}

STUDENT SUBMISSION:
{student_source}

Evaluate the student's code and provide feedback at the appropriate hint level.
Return JSON with keys:
- status: "pass" or "fail"
- short_explanation: string (2-4 sentences)
- next_steps: array of 1-3 concrete actions
- slide_number: null
"""

    try:
        resp = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            input=prompt
        )
        text = getattr(resp, "output_text", None)
        if not isinstance(text, str):
            text = resp.output[0].content[0].text

        text = text.strip()
        if text.startswith("```"):
            text = text.split("```", 1)[1]
            if "```" in text:
                text = text.rsplit("```", 1)[0]
            text = text.strip()
        if text.lower().startswith("json"):
            text = text[4:].lstrip()

        parsed = json.loads(text)
        status = parsed.get("status", "fail")
        explanation = parsed.get("short_explanation", "")
        next_steps = parsed.get("next_steps", [])

        lines = []
        if status == "pass":
            lines.append("[PASS]")
        else:
            lines.append("[FAIL]")
            lines.append(f" {explanation}")
            for i, step in enumerate(next_steps, 1):
                lines.append(f"   {i}. {step}")
        return "\n".join(lines)

    except Exception as e:
        return f"[ERROR] LLM grading failed: {e}"


def grade_submissions(config_path: str):
    with open(config_path, "r") as f:
        config = json.load(f)

    canvas_token = os.getenv("CANVAS_TOKEN", "").strip()
    if not canvas_token:
        print("[ERROR] CANVAS_TOKEN environment variable not set.")
        return

    course_id = config.get("canvas_course_id") or config.get("course_id")
    module = config.get("module", config.get("course_id", "unknown"))
    use_harness = "adapter" in config

    results_dir = Path("submissions/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    # get assignments to grade
    if use_harness:
        assignment_ids = [(config.get("canvas_assignment_id"), config.get("name", module))]
    else:
        assignment_ids = [(a["id"], a["name"]) for a in config.get("assignments", [])]

    for assignment_id, assignment_name in assignment_ids:
        if not assignment_id or str(assignment_id) == "TBD":
            continue

        print(f"\n[INFO] Fetching submissions for {assignment_name}...")
        submissions = get_submissions(course_id, str(assignment_id), canvas_token)

        if not submissions:
            print("[INFO] No submissions found.")
            continue

        # fetch skeleton and solution for LLM path
        skeleton_source = None
        solution_source = None
        if not use_harness:
            for sf in config.get("skeleton_files", []):
                try:
                    skeleton_source = fetch_canvas_file(str(sf["canvas_id"]), canvas_token)
                    break
                except Exception:
                    pass
            for sf in config.get("solution_files", []):
                try:
                    solution_source = fetch_canvas_file(str(sf["canvas_id"]), canvas_token)
                    break
                except Exception:
                    pass

        for submission in submissions:
            user_id = submission.get("user_id")
            submitted_at = submission.get("submitted_at")
            attachments = submission.get("attachments", [])

            if not attachments:
                print(f"[SKIP] Student {user_id} — no attachments")
                continue

            print(f"\n[INFO] Grading student {user_id} (submitted {submitted_at})")

            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir = Path(tmpdir)
                downloaded = []
                for attachment in attachments:
                    filename = attachment.get("display_name", "file")
                    dest = tmpdir / filename
                    if download_attachment(attachment, dest, canvas_token):
                        downloaded.append(dest)
                        print(f"  Downloaded: {filename}")

                if not downloaded:
                    print(f"  No files downloaded, skipping.")
                    continue

                if use_harness:
                    # harness path — copy files and run driver
                    module_dir = Path(config["student_files"][0]).parent
                    backed_up = []
                    for f in downloaded:
                        dest = module_dir / f.name
                        if dest.exists():
                            shutil.copy(dest, str(dest) + ".bak")
                            backed_up.append(dest)
                        shutil.copy(f, dest)

                    result = subprocess.run(
                        [sys.executable, "-u", "-m", "scripts.driver", config_path],
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    output = result.stdout or result.stderr or "No output."

                    for dest in backed_up:
                        shutil.copy(str(dest) + ".bak", dest)
                        Path(str(dest) + ".bak").unlink()

                else:
                    # LLM static analysis path
                    all_output = []
                    for f in downloaded:
                        try:
                            student_source = f.read_text(encoding="utf-8")
                        except Exception:
                            continue
                        attempt = get_attempt(str(user_id), assignment_name, f.name)
                        feedback = llm_grade(
                            student_source,
                            skeleton_source or "",
                            solution_source or "",
                            assignment_name,
                            attempt
                        )
                        # increment attempt if failed, reset if passed
                        if "[PASS]" in feedback:
                            reset_attempt(str(user_id), assignment_name, f.name)
                        else:
                            increment_attempt(str(user_id), assignment_name, f.name)
                        all_output.append(f"--- {f.name} ---\n{feedback}")
                    output = "\n\n".join(all_output)

                print(output)
                result_file = results_dir / f"{module}_student_{user_id}.txt"
                result_file.write_text(output, encoding="utf-8")
                print(f"  Result saved to {result_file}")


if __name__ == "__main__":
    config_path = sys.argv[1] if len(sys.argv) > 1 else "configs/m4_sorts.json"
    grade_submissions(config_path)