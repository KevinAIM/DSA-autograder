def format_output(result):
    status = result.get("status")
    name = result.get("method") or result.get("class")
    feedback = result.get("feedback", {})
    short_explanation = feedback.get("short_explanation", "")
    next_steps = feedback.get("next_steps", [])
    
    if status == "pass":
        print(f"\u2705 {name} — PASSED")
    elif status == "fail":
        print(f"\u274c {name} — FAILED")
        print(f" {short_explanation}")
        for i, step in enumerate(next_steps, 1):
            print(f"   {i}. {step}")
    elif status == "runtime_error":
        print(f"\u274c {name} — RUNTIME ERROR")
        print(f" {short_explanation}")
        for i, step in enumerate(next_steps, 1):
            print(f"   {i}. {step}")
    elif status == "compile_error":
        print(f"\u274c {name} — COMPILE ERROR")
        print(f" {short_explanation}")
        for i, step in enumerate(next_steps, 1):
            print(f"   {i}. {step}")
    elif status == "blocked":
        print(f"\u26d4 {name} — BLOCKED")
        print(f" {short_explanation}")
        for i, step in enumerate(next_steps, 1):
            print(f"   {i}. {step}")