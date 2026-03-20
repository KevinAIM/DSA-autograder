import json
from pathlib import Path
from scripts.feedback import generate_feedback
from scripts.run_compile import compile_java, run_java, read_text, scan_java_source
from scripts.ingest_slides import query_slides
from openai import OpenAI
import os
from scripts.attempt_tracker import get_attempt, increment_attempt, reset_attempt

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

    MODULE = "M4"  # change to "M_" to grade M4 sorts, "M5" for M5 data structures, etc...

    if MODULE == "M4":
        from adapters.m4_sorts import M4SortsAdapter
        adapter = M4SortsAdapter(
            name="M4 Sorts",
            module="M4",
            student_files=[Path("M4/Sort.java")],
            package="M4",
            student_class="Sort",
            timeout_sec=5.0,
            db_path=Path("vector_store/dsa_m4")
        )
    elif MODULE == "M5":
        from adapters.m5_data_structures import M5DataStructuresAdapter
        adapter = M5DataStructuresAdapter(
            name="M5 Data Structures",
            module="M5",
            student_files=[
                Path("M5/Stack.java"),
                Path("M5/Queue.java"),
                Path("M5/ListNode.java"),
                Path("M5/LinkedList.java"),
                Path("M5/TreeNode.java"),
                Path("M5/BinarySearchTree.java"),
            ],
            package="M5",
            student_class="",
            timeout_sec=5.0,
        )


    # 1) pre-run scan
    for file in adapter.student_files:
        source = read_text(str(file))
        scan = scan_java_source(source)
        if scan["status"] != "ok":
            result = {"status": "blocked", "scan": scan}
            result["feedback"] = generate_feedback(result, source, adapter.name, "N/A", 1, "N/A")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return
        
    source = "\n".join(read_text(str(f)) for f in adapter.student_files)
    

    # 2 compile student + harness
    c1 = compile_java([str(f) for f in adapter.student_files])
    if c1["status"] != "ok":
        result = {"status": "compile_error", "which": "student", "compile": c1}

        result["feedback"] = generate_feedback(result, source, adapter.name, "N/A", 1, "N/A")
        print(json.dumps(result, ensure_ascii=False, indent=2))


        return



    for method in adapter.methods():

        # 2) generate harness
        harness_path = Path("harness/Harness.java")
        harness_path.parent.mkdir(parents=True, exist_ok=True)
        adapter.write_harness(harness_path, method)

        c2 = compile_java(str(harness_path))
        if c2["status"] != "ok":
                        #retrieve relevant slides
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
            print(json.dumps(result, ensure_ascii=False, indent=2))

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
            print(json.dumps(result, ensure_ascii=False, indent=2))

            continue

        # 5) parse harness result
        h = parse_harness_stdout(run.get("stdout", ""))

        if h.get("status") == "pass":
            name = method.get("method_name") or method.get("class_name")
            key = "method" if method.get("method_name") else "class"
            print(json.dumps({"status": "pass", key: name}, ensure_ascii=False))
            reset_attempt(student_id, adapter.module, method.get("method_name") or method.get("class_name"))

            continue

        if h.get("status") == "fail":
            increment_attempt(student_id, adapter.module, method.get("method_name") or method.get("class_name"))
                    #retrieve relevant slides
            ref_text = method.get("pseudo_code", "") #fallback if no pseudo code provided
            if adapter.db_path and adapter.db_path.exists():
                query = f"{method.get('method_name') or method.get('class_name')}"
                retrieved = query_slides(query, adapter.db_path, client)
                ref_text = "\n\n".join(retrieved)
                

            if method.get("harness_type") == "partition":
                result = {
                    "status": "fail",
                    "method": method.get("method_name") or method.get("class_name"),
                    "testIndex": h.get("testIndex"),
                    "reason": h.get("reason"),  # partition uses "reason" not expected/actual
                    "input": h.get("input"),
                }
            else:
                result = {
                    "status": "fail",
                    "method": method.get("method_name") or method.get("class_name"),
                    "testIndex": h.get("testIndex"),
                    "input": h.get("input"),
                    "expected": h.get("expected"),
                    "actual": h.get("actual"),
                }
                
            attempt = get_attempt(student_id, adapter.module, method.get("method_name") or method.get("class_name"))
            result["feedback"] = generate_feedback(result, source, adapter.name, ref_text, attempt, method.get("method_name") or method.get("class_name"))
            print(json.dumps(result, ensure_ascii=False))

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
            print(json.dumps(result, ensure_ascii=False, indent=2))


            continue


        result = {"status": "unknown_harness_output", "harness": h, "raw": run}
        result["feedback"] = generate_feedback(result, source, adapter.name, ref_text, attempt, method.get("method_name") or method.get("class_name"))
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
