import sys
import json
import os
import requests
import tempfile
import shutil
from pathlib import Path


CANVAS_BASE = "https://montclair.instructure.com"


def get_submissions(course_id: str, assignment_id: str, canvas_token: str) -> list:
    """Fetch all submissions for a given assignment."""
    url = f"{CANVAS_BASE}/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions"
    headers = {"Authorization": f"Bearer {canvas_token}"}
    params = {"include[]": "attachments", "per_page": 100}

    r = requests.get(url, headers=headers, params=params)
    r.raise_for_status()
    return r.json()


def download_attachment(attachment: dict, dest_path: Path, canvas_token: str) -> bool:
    """Download a single file attachment from Canvas."""
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


def grade_submissions(config_path: str):
    with open(config_path, "r") as f:
        config = json.load(f)

    canvas_token = os.getenv("CANVAS_TOKEN", "").strip()
    if not canvas_token:
        print("[ERROR] CANVAS_TOKEN environment variable not set.")
        return

    course_id = config.get("canvas_course_id")
    assignment_id = config.get("canvas_assignment_id")
    module = config.get("module", "unknown")

    if not course_id or not assignment_id:
        print("[ERROR] canvas_course_id and canvas_assignment_id must be set in config.")
        return

    print(f"[INFO] Fetching submissions for {module} (assignment {assignment_id})...")
    submissions = get_submissions(course_id, assignment_id, canvas_token)

    if not submissions:
        print("[INFO] No submissions found.")
        return

    results_dir = Path("submissions/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    for submission in submissions:
        user_id = submission.get("user_id")
        submitted_at = submission.get("submitted_at")
        attachments = submission.get("attachments", [])

        if not attachments:
            print(f"[SKIP] Student {user_id} — no attachments")
            continue

        print(f"\n[INFO] Grading student {user_id} (submitted {submitted_at})")

        # create temp directory for this student's files
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # download each submitted Java file
            downloaded = []
            for attachment in attachments:
                filename = attachment.get("display_name", "file.java")
                dest = tmpdir / filename
                if download_attachment(attachment, dest, canvas_token):
                    downloaded.append(dest)
                    print(f"  Downloaded: {filename}")
                else:
                    print(f"  Failed to download: {filename}")

            if not downloaded:
                print(f"  No files downloaded, skipping.")
                continue

            # copy files into the module directory
            module_dir = Path(config["student_files"][0]).parent
            backed_up = []
            for f in downloaded:
                dest = module_dir / f.name
                if dest.exists():
                    shutil.copy(dest, str(dest) + ".bak")
                    backed_up.append(dest)
                shutil.copy(f, dest)

            # run the driver and capture output
            import subprocess
            result = subprocess.run(
                ["python", "-u", "-m", "scripts.driver", config_path],
                capture_output=True,
                text=True,
                timeout=300
            )

            output = result.stdout
            print(output)

            # save result
            result_file = results_dir / f"{module}_student_{user_id}.txt"
            result_file.write_text(output, encoding="utf-8")
            print(f"  Result saved to {result_file}")

            # restore original files
            for dest in backed_up:
                shutil.copy(str(dest) + ".bak", dest)
                Path(str(dest) + ".bak").unlink()


if __name__ == "__main__":
    config_path = sys.argv[1] if len(sys.argv) > 1 else "configs/m4_sorts.json"
    grade_submissions(config_path)