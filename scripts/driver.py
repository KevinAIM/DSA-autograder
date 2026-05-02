import json
from pathlib import Path
from scripts.feedback import generate_feedback
from scripts.run_compile import compile_java, run_java, read_text, scan_java_source
from scripts.ingest_slides import query_slides
from openai import OpenAI
import os
from scripts.attempt_tracker import get_attempt, increment_attempt, reset_attempt
import sys
from scripts.output_formatter import format_output
from scripts.video_search import get_video_url
from scripts.malware_check import run_malware_checks


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def parse_harness_stdout(stdout: str) -> dict:
    s = stdout or ""
    start = s.find("{")
    if start == -1:
        return {"status": "unknown", "raw": stdout}
    s2 = s[start:]
    try:
        obj, _ = json.JSONDecoder().raw_decode(s2)
        return obj
    except Exception:
        return {"status": "unknown", "raw": stdout}


def method_name(method: dict) -> str:
    return method.get("method_name") or method.get("class_name")


def build_reference_text(adapter, method: dict, client: OpenAI) -> str:
    ref_text = method.get("pseudo_code", "")
    if not adapter.db_path or not adapter.db_path.exists():
        return ref_text

    try:
        retrieved = query_slides(method_name(method), adapter.db_path, client)
    except Exception:
        return ref_text

    if not retrieved:
        return ref_text

    return "\n\n".join([f"Slide {r['slide']}] {r['text']}" for r in retrieved])


def build_video_url(name: str, config: dict, attempt: int, extra_keywords=None) -> str | None:
    if attempt != 3:
        return None
    try:
        return get_video_url(name, config, extra_keywords=extra_keywords)
    except Exception:
        return None


def main():

    student_id = "student_001"

    config_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("configs/m4_sorts.json")
    with open(config_path, "r") as f:
        config = json.load(f)

    from adapters.registry import REGISTRY
    adapter_class = REGISTRY[config["adapter"]]
    adapter = adapter_class(
        name=config["name"],
        module=config["module"],
        student_files=[Path(f) for f in config["student_files"]],
        package=config["package"],
        student_class=config["student_class"],
        timeout_sec=config["timeout_sec"],
        db_path=Path(config["db_path"])
    )

    # 1) pre-run scan
    for file in adapter.student_files:
        source = read_text(str(file))
        scan = scan_java_source(source)
        if scan["status"] != "ok":
            result = {"status": "blocked", "scan": scan}
            result["feedback"] = generate_feedback(result, source, adapter.name, "N/A", 1, "N/A")
            result["attempt"] = 1
            format_output(result, config)
            return

    source = "\n".join(read_text(str(f)) for f in adapter.student_files)

    canvas_token = os.getenv("CANVAS_TOKEN", "").strip()
    if canvas_token and config.get("skeleton_files"):
        student_file_sources = [{"file": str(f), "source": read_text(str(f))} for f in adapter.student_files]
        malware_result = run_malware_checks(student_file_sources, config["skeleton_files"], canvas_token)
        if malware_result["status"] == "malware_suspected":
            result = {"status": "blocked", "scan": {"status": "blocked", "safe_to_run": False, "reasons": [{"rule": "malware_suspected", "match": r.get("reason", ""), "line": 0} for r in malware_result["files"] if r.get("status") == "malware_suspected"], "warnings": []}}
            result["feedback"] = generate_feedback(result, source, adapter.name, "N/A", 1, "N/A")
            result["attempt"] = 1
            format_output(result, config)
            return

    # 2) compile student
    c1 = compile_java([str(f) for f in adapter.student_files])
    if c1["status"] != "ok":
        result = {"status": "compile_error", "which": "student", "compile": c1}
        result["feedback"] = generate_feedback(result, source, adapter.name, "N/A", 1, "N/A")
        result["attempt"] = 1
        format_output(result, config)
        return

    for method in adapter.methods():
        name = method_name(method)

        harness_path = Path("harness/Harness.java")
        harness_path.parent.mkdir(parents=True, exist_ok=True)
        adapter.write_harness(harness_path, method)

        c2 = compile_java(str(harness_path))
        if c2["status"] != "ok":
            result = {"status": "compile_error",
                      "which": "harness",
                      "compile": c2,
                      "method": name}

            attempt = get_attempt(student_id, adapter.module, name)
            result["feedback"] = generate_feedback(result, source, adapter.name, build_reference_text(adapter, method, client), attempt, name)
            result["attempt"] = attempt
            result["video_url"] = build_video_url(name, config, attempt)
            format_output(result, config)
            continue

        run = run_java(adapter.harness_main_class(), timeout_sec=adapter.timeout_sec)
        if run["status"] != "ok":
            increment_attempt(student_id, adapter.module, name)

            result = {"status": "runtime_error",
                      "run": run,
                      "method": name}

            attempt = get_attempt(student_id, adapter.module, name)
            result["feedback"] = generate_feedback(result, source, adapter.name, build_reference_text(adapter, method, client), attempt, name)
            result["attempt"] = attempt
            result["video_url"] = build_video_url(name, config, attempt)
            format_output(result, config)
            continue

        h = parse_harness_stdout(run.get("stdout", ""))

        if h.get("status") == "pass":
            key = "method" if method.get("method_name") else "class"
            format_output({"status": "pass", key: name}, config)
            reset_attempt(student_id, adapter.module, name)
            continue

        if h.get("status") == "fail":
            increment_attempt(student_id, adapter.module, name)

            result = {
                "status": "fail",
                "method": name,
            }
            if h.get("testIndex") is not None:
                result["testIndex"] = h.get("testIndex")
            if h.get("input") is not None:
                result["input"] = h.get("input")
            if h.get("expected") is not None:
                result["expected"] = h.get("expected")
            if h.get("actual") is not None:
                result["actual"] = h.get("actual")
            if h.get("reason") is not None:
                result["reason"] = h.get("reason")

            attempt = get_attempt(student_id, adapter.module, name)
            result["feedback"] = generate_feedback(result, source, adapter.name, build_reference_text(adapter, method, client), attempt, name)
            result["attempt"] = attempt
            result["video_url"] = build_video_url(
                name,
                config,
                attempt,
                extra_keywords=["key", "shift", "index", "pseudocode", "array", "while"]
            )
            format_output(result, config)
            continue

        if h.get("status") == "error":
            increment_attempt(student_id, adapter.module, name)

            result = {
                "status": "runtime_error",
                "type": h.get("type"),
                "testIndex": h.get("testIndex"),
                "input": h.get("input"),
                "exception": h.get("exception"),
                "method": name
            }

            attempt = get_attempt(student_id, adapter.module, name)
            result["feedback"] = generate_feedback(result, source, adapter.name, build_reference_text(adapter, method, client), attempt, name)
            result["attempt"] = attempt
            result["video_url"] = build_video_url(name, config, attempt)
            format_output(result, config)
            continue

        result = {"status": "unknown_harness_output", "harness": h, "raw": run}
        attempt = get_attempt(student_id, adapter.module, name)
        result["feedback"] = generate_feedback(result, source, adapter.name, build_reference_text(adapter, method, client), attempt, name)
        result["attempt"] = attempt
        result["video_url"] = build_video_url(name, config, attempt)
        format_output(result, config)

if __name__ == "__main__":
    main()
