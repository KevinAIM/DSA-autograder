import sys
import json
import subprocess
from pathlib import Path


COOKIES_FILE = "cookies.txt"
WHISPER_MODEL = "medium"


def download_video(panopto_url: str, output_path: Path) -> bool:
    """Download a Panopto video using yt-dlp and cookies file."""
    if not Path(COOKIES_FILE).exists():
        print(f"[ERROR] cookies.txt not found. Export cookies from your browser first.")
        return False

    result = subprocess.run(
        [
            "python", "-m", "yt_dlp",
            "--cookies", COOKIES_FILE,
            "-o", str(output_path),
            panopto_url
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"[ERROR] yt-dlp failed: {result.stderr}")
        return False

    return True


def transcribe_video(video_path: Path, output_txt: Path) -> bool:
    """Run Whisper on a video file and save transcript as plain text with timestamps."""
    result = subprocess.run(
        [
            "python", "-m", "whisper",
            str(video_path),
            "--model", WHISPER_MODEL,
            "--output_format", "vtt",
            "--output_dir", str(video_path.parent)
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"[ERROR] Whisper failed: {result.stderr}")
        return False

    # find the generated vtt file
    vtt_path = video_path.with_suffix(".vtt")
    if not vtt_path.exists():
        print(f"[ERROR] VTT file not found at {vtt_path}")
        return False

    # copy to captions directory
    output_txt.parent.mkdir(parents=True, exist_ok=True)
    output_txt.write_text(vtt_path.read_text(encoding="utf-8"), encoding="utf-8")
    vtt_path.unlink()

    return True


def ingest_captions(config_path: str):
    with open(config_path, "r") as f:
        config = json.load(f)

    videos = config.get("videos", [])
    if not videos:
        print(f"[INFO] No videos found in config.")
        return

    module = config.get("module", "unknown")
    print(f"[INFO] Processing {len(videos)} videos for {module}...")

    for video in videos:
        title = video.get("title", "unknown")
        panopto_url = video.get("panopto_url")
        caption_path = Path(video.get("captions", ""))

        if not panopto_url or not caption_path:
            print(f"[SKIP] Missing URL or caption path for {title}")
            continue

        if caption_path.exists():
            print(f"[SKIP] Captions already exist for {title} at {caption_path}")
            continue

        print(f"\n[INFO] Processing: {title}")

        # temp video file in project root
        temp_video = Path(f"temp_{caption_path.stem}.mp4")

        print(f"  Downloading video...")
        if not download_video(panopto_url, temp_video):
            continue

        print(f"  Transcribing with Whisper...")
        if not transcribe_video(temp_video, caption_path):
            temp_video.unlink(missing_ok=True)
            continue

        # clean up video file
        temp_video.unlink(missing_ok=True)
        print(f"  Done -> {caption_path}")

    print(f"\n[DONE] Caption ingestion complete for {module}.")


if __name__ == "__main__":
    config_path = sys.argv[1] if len(sys.argv) > 1 else "configs/m4_sorts.json"
    ingest_captions(config_path)