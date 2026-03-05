import subprocess

ALLOWED_IMPORT_PREFIXES = {
    "java.util."  # allows java.util.* and specific java.util.X
}

BANNED_SUBSTRINGS_HARD = [
    # filesystem
    "java.io.",
    "java.nio.file.",
    "Files.",
    "FileInputStream",
    "FileOutputStream",
    "FileReader",
    "FileWriter",
    "BufferedReader",
    "BufferedWriter",
    "Scanner(",

    # networking
    "java.net.",
    "Socket",
    "HttpURLConnection",
    "URL(",

    # process execution
    "Runtime.getRuntime().exec",
    "ProcessBuilder",

    # environment / escape hatches
    "System.exit",
    "System.getenv",
    "System.setProperty",

    # reflection / dynamic loading
    "Class.forName",
    "java.lang.reflect",
]

BANNED_SUBSTRINGS_SOFT = [
    "while(true",
    "for(;;",
    "Thread.sleep",
]

def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def scan_java_source(source: str) -> dict:
    lines = source.splitlines()

    reasons = []
    warnings = []

    #import whitelist
    for idx, line in enumerate(lines, start=1):
        s = line.strip()
        if not s.startswith("import "):
            continue

        imp = s[len("import "):].rstrip(";").strip()

        allowed = any(imp.startswith(prefix) for prefix in ALLOWED_IMPORT_PREFIXES)
        if not allowed:
            reasons.append({
                "rule": "import_whitelist",
                "line": idx,
                "match": s
            })

    #hard banned substrings
    for idx, line in enumerate(lines, start=1):
        for token in BANNED_SUBSTRINGS_HARD:
            if token in line:
                reasons.append({
                    "rule": "banned_api",
                    "line": idx,
                    "match": token,
                    "text": line.strip()
                })

        for token in BANNED_SUBSTRINGS_SOFT:
            if token in line:
                warnings.append({
                    "rule": "hang_risk",
                    "line": idx,
                    "match": token,
                    "text": line.strip()
                })

    safe = (len(reasons) == 0)
    return {
        "status": "ok" if safe else "blocked",
        "safe_to_run": safe,
        "reasons": reasons,
        "warnings": warnings
    }


def compile_java(java_file: str) -> dict:
    r = subprocess.run(
        ["javac", java_file],
        capture_output=True,
        text=True
    )
    if r.returncode == 0:
        return {"status": "ok"}
    return {
        "status": "compile_error",
        "stderr": r.stderr,
        "stdout": r.stdout,
        "returncode": r.returncode
    }

def run_java(main_class: str, timeout_sec: float = 2.0) -> dict:
    try:
        r = subprocess.run(
            ["java", main_class],
            capture_output=True,
            text=True,
            timeout=timeout_sec
        )
        if r.returncode == 0:
            return {
                "status": "ok",
                "stdout": r.stdout,
                "stderr": r.stderr,
                "returncode": r.returncode
            }
        else:
            return {
                "status": "runtime_error",
                "stdout": r.stdout,
                "stderr": r.stderr,
                "returncode": r.returncode
            }
    except subprocess.TimeoutExpired as e:
        return {
            "status": "timeout",
            "timeout_sec": timeout_sec,
            "stdout": e.stdout,
            "stderr": e.stderr
        }

def main():
    java_path = "M4/Sort.java"

    source = read_text(java_path)
    scan = scan_java_source(source)
    # print("SCAN:", scan)
    if scan["status"] != "ok":
        return

    c = compile_java(java_path)
    # print("COMPILE:", c)
    if c["status"] != "ok":
        return

    r = run_java("M4.Sort", timeout_sec=2.0)
    # print("RUN:", r)

if __name__ == "__main__":
    main()
