def format_output(result):
    status = result.get("status")
    name = result.get("method") or result.get("class")
    feedback = result.get("feedback", {})
    short_explanation = feedback.get("short_explanation", "")
    next_steps = feedback.get("next_steps", [])
    
    if status == "pass":
        print(f"[PASS] {name}")
    elif status == "fail":
        print(f"[FAIL] {name}")
        print(f" {short_explanation}")
        for i, step in enumerate(next_steps, 1):
            print(f"   {i}. {step}")
    elif status == "runtime_error":
        print(f"[RUNTIME ERROR] {name}")
        print(f" {short_explanation}")
        for i, step in enumerate(next_steps, 1):
            print(f"   {i}. {step}")
    elif status == "compile_error":
        print(f"[COMPILE ERROR] {name}")
        print(f" {short_explanation}")
        for i, step in enumerate(next_steps, 1):
            print(f"   {i}. {step}")
    elif status == "blocked":
        print(f"[BLOCKED] {name}")
        print(f" {short_explanation}")
        for i, step in enumerate(next_steps, 1):
            print(f"   {i}. {step}")