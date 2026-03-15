import json
from pathlib import Path
from scripts.feedback import generate_feedback

from adapters.m4_sorts import M4SortsAdapter
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
    adapter = M4SortsAdapter(
        name="M4 Sorts",
        module="M4",
        student_files=[Path("M4/Sort.java")],
        package="M4",
        student_class="Sort",
        timeout_sec=5.0,  # start higher than 2.0
    )

    # 1) pre-run scan
    for file in adapter.student_files:
        source = read_text(str(file))
        scan = scan_java_source(source)
        if scan["status"] != "ok":
            result = {"status": "blocked", "scan": scan}
            result["feedback"] = generate_feedback(result, source, adapter.name, "N/A", "N/A")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return
        
    source = "\n".join(read_text(str(f)) for f in adapter.student_files)
    

    # 2 compile student + harness
    c1 = compile_java([str(f) for f in adapter.student_files])
    if c1["status"] != "ok":
        result = {"status": "compile_error", "which": "student", "compile": c1}

        result["feedback"] = generate_feedback(result, source, adapter.name, "N/A", "N/A")
        print(json.dumps(result, ensure_ascii=False, indent=2))


        return

    for method in adapter.methods():

        # 2) generate harness
        harness_path = Path("harness/Harness.java")
        harness_path.parent.mkdir(parents=True, exist_ok=True)
        adapter.write_harness(harness_path, method)

        c2 = compile_java(str(harness_path))
        if c2["status"] != "ok":
            result = {"status": "compile_error", 
                      "which": "harness", 
                      "compile": c2, 
                      "method": method["method_name"]}

            result["feedback"] = generate_feedback(result, source, adapter.name, method["pseudo_code"], method["method_name"])
            print(json.dumps(result, ensure_ascii=False, indent=2))

            continue

        # 4) run harness
        run = run_java(adapter.harness_main_class(), timeout_sec=adapter.timeout_sec)
        if run["status"] != "ok":
            result = {"status": "runtime_error", 
                      "run": run, 
                      "method": method["method_name"]}

            result["feedback"] = generate_feedback(result, source, adapter.name, method["pseudo_code"], method["method_name"])
            print(json.dumps(result, ensure_ascii=False, indent=2))

            continue

        # 5) parse harness result
        h = parse_harness_stdout(run.get("stdout", ""))

        if h.get("status") == "pass":
            print(json.dumps({"status": "pass", "tests": h.get("tests"), "method" : method["method_name"]}, ensure_ascii=False))

            continue

        if h.get("status") == "fail":
            if method.get("harness_type") == "partition":
                result = {
                    "status": "fail",
                    "method": method["method_name"],
                    "testIndex": h.get("testIndex"),
                    "reason": h.get("reason"),  # partition uses "reason" not expected/actual
                    "input": h.get("input"),
                }
            else:
                result = {
                    "status": "fail",
                    "method": method["method_name"],
                    "testIndex": h.get("testIndex"),
                    "input": h.get("input"),
                    "expected": h.get("expected"),
                    "actual": h.get("actual"),
                }

            result["feedback"] = generate_feedback(result, source, adapter.name, method["pseudo_code"], method["method_name"])
            print(json.dumps(result, ensure_ascii=False))

            continue
        
        if h.get("status") == "error":
            result = {
                "status": "runtime_error",
                "type": h.get("type"),
                "testIndex": h.get("testIndex"),
                "input": h.get("input"),
                "exception": h.get("exception"),
                "method": method["method_name"]
            }

            result["feedback"] = generate_feedback(result, source, adapter.name, method["pseudo_code"], method["method_name"])
            print(json.dumps(result, ensure_ascii=False, indent=2))


            continue


        result = {"status": "unknown_harness_output", "harness": h, "raw": run}
        result["feedback"] = generate_feedback(result, source, adapter.name, method["pseudo_code"], method["method_name"])
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
