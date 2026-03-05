import json
from pathlib import Path
from scripts.feedback import generate_feedback

from adapters.m4_sorting import M4InsertionSortAdapter
from scripts.run_compile import compile_java, run_java, read_text, scan_java_source



def parse_harness_stdout(stdout: str) -> dict:
    s = stdout or ""
    # Find the first JSON object start
    start = s.find("{")
    if start == -1:
        return {"status": "unknown", "raw": stdout}

    s2 = s[start:]
    try:
        obj, _ = json.JSONDecoder().raw_decode(s2)
        return obj
    except Exception:
        return {"status": "unknown", "raw": stdout}



def main():
    adapter = M4InsertionSortAdapter(
        name="M4 Insertion Sort",
        module="M4",
        student_java=Path("M4/Sort.java"),
        package="M4",
        student_class="Sort",
        timeout_sec=5.0,  # start higher than 2.0
    )

    # 1) pre-run scan
    source = read_text(str(adapter.student_java))
    scan = scan_java_source(source)
    if scan["status"] != "ok":
        result = {"status": "blocked", "scan": scan}

        result["feedback"] = generate_feedback(result, source, adapter.name)
        print(json.dumps(result, ensure_ascii=False, indent=2))


        return

    # 2) generate harness
    harness_path = Path("harness/Harness.java")
    harness_path.parent.mkdir(parents=True, exist_ok=True)
    adapter.write_harness(harness_path)

    # 3) compile student + harness
    c1 = compile_java(str(adapter.student_java))
    if c1["status"] != "ok":
        result = {"status": "compile_error", "which": "student", "compile": c1}

        result["feedback"] = generate_feedback(result, source, adapter.name)
        print(json.dumps(result, ensure_ascii=False, indent=2))


        return

    c2 = compile_java(str(harness_path))
    if c2["status"] != "ok":
        result = {"status": "compile_error", "which": "harness", "compile": c2}

        result["feedback"] = generate_feedback(result, source, adapter.name)
        print(json.dumps(result, ensure_ascii=False, indent=2))


        return

    # 4) run harness
    run = run_java(adapter.harness_main_class(), timeout_sec=adapter.timeout_sec)
    if run["status"] != "ok":
        result = {"status": "runtime_error", "run": run}

        result["feedback"] = generate_feedback(result, source, adapter.name)
        print(json.dumps(result, ensure_ascii=False, indent=2))


        return

    # 5) parse harness result
    h = parse_harness_stdout(run.get("stdout", ""))

    if h.get("status") == "pass":
        print(json.dumps({"status": "pass", "tests": h.get("tests")}, ensure_ascii=False))
        return

    if h.get("status") == "fail":
        result = {
            "status": "fail",
            "testIndex": h.get("testIndex"),
            "input": h.get("input"),
            "expected": h.get("expected"),
            "actual": h.get("actual"),
        }

        result["feedback"] = generate_feedback(result, source, adapter.name)
        print(json.dumps(result, ensure_ascii=False))

        return
    
    if h.get("status") == "error":
        result = {
            "status": "runtime_error",
            "type": h.get("type"),
            "testIndex": h.get("testIndex"),
            "input": h.get("input"),
            "exception": h.get("exception"),
        }

        result["feedback"] = generate_feedback(result, source, adapter.name)
        print(json.dumps(result, ensure_ascii=False, indent=2))


        return


    result = {"status": "unknown_harness_output", "harness": h, "raw": run}
    result["feedback"] = generate_feedback(result, source, adapter.name)
    print(json.dumps(result, ensure_ascii=False, indent=2))





if __name__ == "__main__":
    main()
