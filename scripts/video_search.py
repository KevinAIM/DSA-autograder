import re
from pathlib import Path


def _parse_captions(caption_path: str) -> list[dict]:
    """Parse caption file — supports both VTT and Panopto copy-paste format."""
    text = Path(caption_path).read_text(encoding="utf-8")
    lines = text.splitlines()

    entries = []
    current_lines = []
    current_ts = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip VTT header and NOTE blocks
        if line == "WEBVTT" or line.startswith("NOTE"):
            continue

        # VTT timestamp: 00:00.000 --> 00:03.860 or 00:00:00.000 --> 00:00:03.860
        vtt_match = re.match(r"(\d+):(\d{2})[\.:]\d+ --> ", line)
        if vtt_match:
            minutes, seconds = int(vtt_match.group(1)), int(vtt_match.group(2))
            ts_seconds = minutes * 60 + seconds
            if current_lines:
                entries.append({
                    "text": " ".join(current_lines),
                    "start": current_ts
                })
            current_lines = []
            current_ts = ts_seconds
            continue

        # Panopto copy-paste timestamp: 0:00 or 1:23
        ts_match = re.fullmatch(r"(\d+):(\d{2})", line)
        if ts_match:
            minutes, seconds = int(ts_match.group(1)), int(ts_match.group(2))
            ts_seconds = minutes * 60 + seconds
            if current_lines:
                entries.append({
                    "text": " ".join(current_lines),
                    "start": current_ts
                })
            current_lines = []
            current_ts = ts_seconds
            continue

        # Speaker change marker
        if line.startswith(">>"):
            remainder = line[2:].strip()
            if remainder:
                current_lines.append(remainder)
            continue

        current_lines.append(line)

    if current_lines:
        entries.append({"text": " ".join(current_lines), "start": current_ts})

    return entries


def _chunk_entries(entries: list[dict], chunk_size: int = 8) -> list[dict]:
    """Group entries into overlapping chunks for better context."""
    chunks = []
    for i in range(0, len(entries), chunk_size // 2):
        group = entries[i:i + chunk_size]
        if not group:
            continue
        chunks.append({
            "text": " ".join(e["text"] for e in group).lower(),
            "start": group[0]["start"]
        })
    return chunks


def _score_chunk(chunk_text: str, keywords: list[str], negative_keywords: list[str] = None) -> int:
    score = sum(chunk_text.count(kw.lower()) for kw in keywords)
    if negative_keywords:
        score -= sum(chunk_text.count(kw.lower()) * 2 for kw in negative_keywords)
    return score


def find_timestamp(method_name: str, caption_path: str, extra_keywords: list[str] = None) -> int | None:
    """
    Search captions for the most relevant timestamp for a given method.
    Returns start time in seconds, or None if not found.
    """
    entries = _parse_captions(caption_path)
    if not entries:
        return None

    chunks = _chunk_entries(entries)

    # Build keyword list from method name + extras
    # e.g. "insertionSort" -> ["insertion", "sort", "insertionsort"]
    name_parts = re.sub(r"([A-Z])", r" \1", method_name).lower().split()
    keywords = name_parts + [method_name.lower()]
    if extra_keywords:
        keywords += [k.lower() for k in extra_keywords]

    negative = ["merge sort", "quick sort", "counting sort"]
    chunks = chunks[:20]
    best = max(chunks, key=lambda c: _score_chunk(c["text"], keywords, negative))


    # Only return if there's at least one keyword hit
    if _score_chunk(best["text"], keywords) == 0:
        return None

    return best["start"]


def get_video_url(method_name: str, config: dict, extra_keywords: list[str] = None) -> str | None:
    """
    Given a method name and config, find the right video and timestamp.
    Returns full Panopto URL with &start=X, or None.
    """
    videos = config.get("videos", [])

    for video in videos:
        if method_name in video.get("methods", []):
            caption_path = video.get("captions")
            panopto_url = video.get("panopto_url")

            if not caption_path or not panopto_url:
                return None

            ts = find_timestamp(method_name, caption_path, extra_keywords)
            if ts is not None:
                return f"{panopto_url}&start={ts}"
            else:
                # fallback — link to video start
                return f"{panopto_url}&start=0"

    return None