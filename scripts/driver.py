import json
from pathlib import Path
from scripts.feedback import generate_feedback
from scripts.run_compile import compile_java, run_java, read_text, scan_java_source
from scripts.ingest_slides import query_slides
from openai import OpenAI
import os
from scripts.attempt_tracker import get_attempt, increment_attempt, reset_attempt
import sys
from scripts.formatter import format_output


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))




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

    student_id = "student_001"  # in real use, get this from the environment or request

    #load config
    config_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("configs/m4_sorts.json")
    with open(config_path, "r") as f:
        config = json.load(f)

    #load adapter from registry
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
            format_output(result)
            return
        
    source = "\n".join(read_text(str(f)) for f in adapter.student_files)
    

    # 2 compile student + harness
    c1 = compile_java([str(f) for f in adapter.student_files])
    if c1["status"] != "ok":
        result = {"status": "compile_error", "which": "student", "compile": c1}

        result["feedback"] = generate_feedback(result, source, adapter.name, "N/A", 1, "N/A")
        format_output(result)


        return



    for method in adapter.methods():

        # 2) generate harness
        harness_path = Path("harness/Harness.java")
        harness_path.parent.mkdir(parents=True, exist_ok=True)
        adapter.write_harness(harness_path, method)

        c2 = compile_java(str(harness_path))
        if c2["status"] != "ok":
                        #retrieve relevant slidesd
            ref_text = method.get("pseudo_code", "") #fallback if no pseudo code provided
            if adapter.db_path and adapter.db_path.exists():
                query = f"{method.get('method_name') or method.get('class_name')}"
                retrieved = query_slides(query, adapter.db_path, client)
                ref_text = "\n\n".join(retrieved)

            result = {"status": "compile_error", 
                      "which": "harness", 
                      "compile": c2, 
                      "method": method.get("method_name") or method.get("class_name")}

            attempt = get_attempt(student_id, adapter.module, method.get("method_name") or method.get("class_name"))
            result["feedback"] = generate_feedback(result, source, adapter.name, ref_text, attempt, method.get("method_name") or method.get("class_name"))
            format_output(result)

            continue

        # 4) run harness
        run = run_java(adapter.harness_main_class(), timeout_sec=adapter.timeout_sec)
        if run["status"] != "ok":
            increment_attempt(student_id, adapter.module, method.get("method_name") or method.get("class_name"))
                                #retrieve relevant slides
            ref_text = method.get("pseudo_code", "") #fallback if no pseudo code provided
            if adapter.db_path and adapter.db_path.exists():
                query = f"{method.get('method_name') or method.get('class_name')}"
                retrieved = query_slides(query, adapter.db_path, client)
                ref_text = "\n\n".join(retrieved)

            result = {"status": "runtime_error", 
                      "run": run, 
                      "method": method.get("method_name") or method.get("class_name")}

            attempt = get_attempt(student_id, adapter.module, method.get("method_name") or method.get("class_name"))
            result["feedback"] = generate_feedback(result, source, adapter.name, ref_text, attempt, method.get("method_name") or method.get("class_name"))
            format_output(result)

            continue

        # 5) parse harness result
        h = parse_harness_stdout(run.get("stdout", ""))

        if h.get("status") == "pass":
            name = method.get("method_name") or method.get("class_name")
            key = "method" if method.get("method_name") else "class"
            format_output({"status": "pass", key: name})
            reset_attempt(student_id, adapter.module, method.get("method_name") or method.get("class_name"))

            continue

        if h.get("status") == "fail":
            increment_attempt(student_id, adapter.module, method.get("method_name") or method.get("class_name"))
            # retrieve relevant slides
            ref_text = method.get("pseudo_code", "")
            if adapter.db_path and adapter.db_path.exists():
                query = f"{method.get('method_name') or method.get('class_name')}"
                retrieved = query_slides(query, adapter.db_path, client)
                ref_text = "\n\n".join(retrieved)

            result = {
                "status": "fail",
                "method": method.get("method_name") or method.get("class_name"),
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

            attempt = get_attempt(student_id, adapter.module, method.get("method_name") or method.get("class_name"))
            result["feedback"] = generate_feedback(result, source, adapter.name, ref_text, attempt, method.get("method_name") or method.get("class_name"))
            format_output(result)
            
            continue
        
        if h.get("status") == "error":
                        #retrieve relevant slides
            ref_text = method.get("pseudo_code", "") #fallback if no pseudo code provided
            if adapter.db_path and adapter.db_path.exists():
                query = f"{method.get('method_name') or method.get('class_name')}"
                retrieved = query_slides(query, adapter.db_path, client)
                ref_text = "\n\n".join(retrieved)
            increment_attempt(student_id, adapter.module, method.get("method_name") or method.get("class_name"))

            result = {
                "status": "runtime_error",
                "type": h.get("type"),
                "testIndex": h.get("testIndex"),
                "input": h.get("input"),
                "exception": h.get("exception"),
                "method": method.get("method_name") or method.get("class_name")
            }

            attempt = get_attempt(student_id, adapter.module, method.get("method_name") or method.get("class_name"))
            result["feedback"] = generate_feedback(result, source, adapter.name, ref_text, attempt, method.get("method_name") or method.get("class_name"))
            format_output(result)


            continue


        result = {"status": "unknown_harness_output", "harness": h, "raw": run}

        ref_text = method.get("pseudo_code", "")
        attempt = get_attempt(student_id, adapter.module, method.get("method_name") or method.get("class_name"))
        result["feedback"] = generate_feedback(result, source, adapter.name, ref_text, attempt, method.get("method_name") or method.get("class_name"))
        format_output(result)

if __name__ == "__main__":
    main()
