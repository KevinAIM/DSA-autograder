import json
import os
import subprocess
import shutil
import tempfile
import time
from pathlib import Path

CONFIG_MAP = {
    "m4": "configs/m4_sorts.json",
    "m5": "configs/m5_data_structures.json",
    "m6": "configs/m6_dp.json",
    "m7": "configs/m7_graphs.json"
}


def retry_unlink(path: Path, attempts: int = 5, delay_sec: float = 0.2):
    for i in range(attempts):
        try:
            if path.exists():
                path.unlink()
            return
        except PermissionError:
            if i == attempts - 1:
                raise
            time.sleep(delay_sec)


def retry_rmtree(path: Path, attempts: int = 5, delay_sec: float = 0.2):
    for i in range(attempts):
        try:
            if path.exists():
                shutil.rmtree(path)
            return
        except PermissionError:
            if i == attempts - 1:
                raise
            time.sleep(delay_sec)


def run_case(module: str, case_dir: Path):
    module_upper = module.upper()
    original_dir = Path(module_upper)
    backup_root = Path(tempfile.mkdtemp(prefix=f"{module_upper}_backup_", dir="benchmark"))
    case_files = list(case_dir.glob("*.java"))

    for f in case_files:
        target = original_dir / f.name
        if target.exists():
            shutil.copy2(target, backup_root / f.name)

    try:
        for f in case_files:
            shutil.copy2(f, original_dir / f.name)

        base_config_path = Path(CONFIG_MAP[module])
        with open(base_config_path) as f:
            config = json.load(f)

        temp_config = backup_root / "temp_config.json"
        with open(temp_config, "w") as f:
            json.dump(config, f)
        attempt_path = backup_root / "student_001.json"
        env = os.environ.copy()
        env["ATTEMPT_TRACKER_PATH"] = str(attempt_path)

        result = subprocess.run(
            ["python", "-u", "-m", "scripts.driver", str(temp_config)],
            capture_output=True,
            text=True,
            timeout=300,
            env=env
        )

        return result.stdout, result.stderr

    finally:
        for f in case_files:
            backup_file = backup_root / f.name
            target = original_dir / f.name
            if backup_file.exists():
                shutil.copy2(backup_file, target)
        try:
            retry_rmtree(backup_root)
        except PermissionError:
            pass

def parse_output(output: str) -> dict:
    results = {}
    for line in output.strip().split("\n"):
        if "[PASS]" in line:
            name = line.replace("[PASS]", "").strip()
            results[name] = "pass"
        elif "[FAIL]" in line:
            name = line.replace("[FAIL]", "").strip()
            results[name] = "fail"
        elif "[RUNTIME ERROR]" in line:
            name = line.replace("[RUNTIME ERROR]", "").strip()
            results[name] = "runtime_error"
        elif "[COMPILE ERROR]" in line:
            name = line.replace("[COMPILE ERROR]", "").strip()
            results[name] = "compile_error"
        elif "[BLOCKED]" in line:
            name = line.replace("[BLOCKED]", "").strip()
            results[name] = "blocked"
    return results

def main():
    cases_dir = Path("benchmark/cases")
    expected_dir = Path("benchmark/expected")

    total = 0
    passed = 0
    failed = 0

    for module_dir in sorted(cases_dir.iterdir()):
        for case_dir in sorted(module_dir.iterdir()):
            module = module_dir.name
            case = case_dir.name
            expected_file = expected_dir / f"{module}_{case}.json"

            if not expected_file.exists():
                print(f"⚠️  No expected file for {module}/{case}, skipping")
                continue

            with open(expected_file) as f:
                expected = json.load(f)

            print(f"\nRunning {module}/{case}...")
            output, errors = run_case(module, case_dir)
            actual = parse_output(output)
            if not actual:
                print(f"   RAW STDOUT: {repr(output[:300])}")
                print(f"   RAW STDERR: {repr(errors[:1000])}")

            total += 1
            if actual == expected:
                passed += 1
                print(f"✅ PASS")
            else:
                failed += 1
                print(f"❌ FAIL")
                print(f"   Expected: {expected}")
                print(f"   Got:      {actual}")

    print(f"\n{'='*40}")
    print(f"Results: {passed}/{total} passed")
    print(f"{'='*40}")


def safe_main():
    cases_dir = Path("benchmark/cases")
    expected_dir = Path("benchmark/expected")

    total = 0
    passed = 0

    for module_dir in sorted(cases_dir.iterdir()):
        for case_dir in sorted(module_dir.iterdir()):
            module = module_dir.name
            case = case_dir.name
            expected_file = expected_dir / f"{module}_{case}.json"

            if not expected_file.exists():
                print(f"WARNING: No expected file for {module}/{case}, skipping")
                continue

            with open(expected_file) as f:
                expected = json.load(f)

            print(f"\nRunning {module}/{case}...")
            output, errors = run_case(module, case_dir)
            actual = parse_output(output)
            if not actual:
                print(f"   RAW STDOUT: {repr(output[:300])}")
                print(f"   RAW STDERR: {repr(errors[:1000])}")

            total += 1
            if actual == expected:
                passed += 1
                print("PASS")
            else:
                print("FAIL")
                print(f"   Expected: {expected}")
                print(f"   Got:      {actual}")

    print(f"\n{'=' * 40}")
    print(f"Results: {passed}/{total} passed")
    print(f"{'=' * 40}")

if __name__ == "__main__":
    safe_main()
