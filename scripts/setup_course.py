import sys
import json
import re
import os
import requests
from pathlib import Path


CANVAS_BASE = "https://montclair.instructure.com"


def extract_course_id(url: str) -> str:
    """Extract course ID from a Canvas course URL."""
    match = re.search(r"/courses/(\d+)", url)
    if not match:
        raise ValueError(f"Could not extract course ID from URL: {url}")
    return match.group(1)


def get_canvas(endpoint: str, token: str, params: dict = None) -> list:
    """Paginated Canvas API GET."""
    headers = {"Authorization": f"Bearer {token}"}
    results = []
    url = f"{CANVAS_BASE}{endpoint}"
    while url:
        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list):
            results.extend(data)
        else:
            return data
        # handle pagination
        url = None
        if "next" in r.links:
            url = r.links["next"]["url"]
            params = None
    return results


def discover_files(course_id: str, token: str) -> list:
    """Get all files in the course filtered to PDFs and presentations."""
    files = get_canvas(f"/api/v1/courses/{course_id}/files", token, {"per_page": 100})
    relevant = []
    for f in files:
        name = f.get("display_name", "")
        ext = Path(name).suffix.lower()
        if ext in [".pdf", ".pptx", ".docx"]:
            relevant.append({
                "id": f["id"],
                "name": name,
                "url": f["url"],
                "type": "slide" if ext in [".pptx", ".docx"] else "pdf"
            })
    return relevant


def discover_assignments(course_id: str, token: str) -> list:
    """Get all file-upload assignments in the course."""
    assignments = get_canvas(f"/api/v1/courses/{course_id}/assignments", token, {"per_page": 100})
    relevant = []
    for a in assignments:
        if "online_upload" in (a.get("submission_types") or []):
            relevant.append({
                "id": a["id"],
                "name": a["name"],
            })
    return relevant


def discover_panopto_urls(course_id: str, token: str) -> list:
    """Crawl Canvas module pages and extract Panopto video URLs."""
    headers = {"Authorization": f"Bearer {token}"}
    videos = []

    # Get all modules
    modules = get_canvas(f"/api/v1/courses/{course_id}/modules", token, {"per_page": 100})

    for module in modules:
        module_id = module["id"]
        items = get_canvas(f"/api/v1/courses/{course_id}/modules/{module_id}/items", token, {"per_page": 100})

        for item in items:
            # fetch the page content if it's a page type
            if item.get("type") == "Page" and item.get("url"):
                page = get_canvas(f"/api/v1/courses/{course_id}/pages/{item['page_url']}", token)
                body = page.get("body", "") if isinstance(page, dict) else ""
                # extract Panopto URLs
                matches = re.findall(
                    r'https://[a-z]+\.hosted\.panopto\.com/Panopto/Pages/Viewer\.aspx\?id=([a-f0-9\-]+)',
                    body
                )
                for video_id in matches:
                    videos.append({
                        "title": item.get("title", "Unknown"),
                        "panopto_url": f"https://montclair.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id={video_id}",
                        "video_id": video_id
                    })

    return videos


def prompt_user(items: list, category: str) -> list:
    """Ask user to confirm which items to include."""
    if not items:
        print(f"\n[{category}] None found.")
        return []

    print(f"\n[{category}] Found {len(items)} item(s):")
    for i, item in enumerate(items, 1):
        name = item.get("name") or item.get("title")
        print(f"  {i}. {name}")

    selected = []
    for i, item in enumerate(items, 1):
        name = item.get("name") or item.get("title")
        answer = input(f"  Include '{name}'? (y/n): ").strip().lower()
        if answer == "y":
            selected.append(item)

    return selected


def setup_course(course_url: str, canvas_token: str):
    course_id = extract_course_id(course_url)
    print(f"\n[INFO] Setting up course {course_id}...")

    # discover resources
    print("[INFO] Scanning files...")
    files = discover_files(course_id, canvas_token)

    print("[INFO] Scanning assignments...")
    assignments = discover_assignments(course_id, canvas_token)

    print("[INFO] Scanning module pages for Panopto videos...")
    videos = discover_panopto_urls(course_id, canvas_token)

    # prompt user
    selected_files = prompt_user(files, "Files/Slides/PDFs")
    selected_assignments = prompt_user(assignments, "Assignments")
    selected_videos = prompt_user(videos, "Panopto Videos")

    # build config
    config = {
        "course_id": course_id,
        "canvas_course_url": course_url,
        "db_path": f"vector_store/course_{course_id}",
        "files": selected_files,
        "assignments": [
            {
                "id": str(a["id"]),
                "name": a["name"]
            }
            for a in selected_assignments
        ],
        "videos": [
            {
                "title": v["title"],
                "panopto_url": v["panopto_url"],
                "captions": f"captions/course_{course_id}_{v['video_id'][:8]}.vtt"
            }
            for v in selected_videos
        ]
    }

    # save config
    config_path = Path(f"configs/course_{course_id}.json")
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"\n[INFO] Config saved to {config_path}")

    # next steps message
    print(f"\n[NEXT] Run the following to build the vector DB and transcribe videos:")
    print(f"  python -m scripts.ingest_slides configs/course_{course_id}.json")
    print(f"  python -m scripts.ingest_captions configs/course_{course_id}.json")
    print(f"\n[DONE] Course setup complete.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.setup_course <canvas_course_url>")
        sys.exit(1)

    course_url = sys.argv[1]
    token = os.getenv("CANVAS_TOKEN", "").strip()
    if not token:
        print("[ERROR] CANVAS_TOKEN environment variable not set.")
        sys.exit(1)

    setup_course(course_url, token)