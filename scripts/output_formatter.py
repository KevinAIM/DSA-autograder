def format_output(result, config=None):
    status = result.get("status")
    name = result.get("method") or result.get("class")
    feedback = result.get("feedback", {})
    short_explanation = feedback.get("short_explanation", "")
    next_steps = feedback.get("next_steps", [])
    slide_number = feedback.get("slide_number")
    slides_url = (config or {}).get("slides_url", "")

    attempt = result.get("attempt", 1)
    video_url = result.get("video_url")

    def slides_link():
        if not slides_url:
            return None
        if attempt == 1:
            return slides_url
        if attempt == 2 and slide_number:
            return f"{slides_url}#page={slide_number}"
        return None

    if status == "pass":
        print(f"[PASS] {name}", flush=True)

    elif status == "fail":
        print(f"[FAIL] {name}", flush=True)
        print(f" {short_explanation}", flush=True)
        for i, step in enumerate(next_steps, 1):
            print(f"   {i}. {step}", flush=True)
        link = slides_link()
        if link:
            print(f"\n   Slides: {link}", flush=True)
        if video_url and attempt == 3:
            print(f"\n   Video: {video_url}", flush=True)

    elif status == "runtime_error":
        print(f"[RUNTIME ERROR] {name}", flush=True)
        print(f" {short_explanation}", flush=True)
        for i, step in enumerate(next_steps, 1):
            print(f"   {i}. {step}", flush=True)
        link = slides_link()
        if link:
            print(f"\n   Slides: {link}", flush=True)
        if video_url and attempt == 3:
            print(f"\n   Video: {video_url}", flush=True)

    elif status == "compile_error":
        print(f"[COMPILE ERROR] {name}", flush=True)
        print(f" {short_explanation}", flush=True)
        for i, step in enumerate(next_steps, 1):
            print(f"   {i}. {step}", flush=True)
        link = slides_link()
        if link:
            print(f"\n   Slides: {link}", flush=True)
        if video_url and attempt == 3:
            print(f"\n   Video: {video_url}", flush=True)

    elif status == "blocked":
        print(f"[BLOCKED] {name}", flush=True)
        print(f" {short_explanation}", flush=True)
        for i, step in enumerate(next_steps, 1):
            print(f"   {i}. {step}", flush=True)
