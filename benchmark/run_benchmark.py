import json
import subprocess
import shutil
from pathlib import Path

CONFIG_MAP = {
    "m4": "configs/m4_sorts.json",
    "m5": "configs/m5_data_structures.json",
    "m6": "configs/m6_dp.json",
    "m7": "configs/m7_graphs.json"
}

def run_case(module: str, case_dir: Path) -> str:
    module_upper = module.upper()
    original_dir = Path(module_upper)
    backup_dir = Path(f"{module_upper}_backup")
    print(f"DEBUG: looking for {original_dir.absolute()}")

    # cleanup any leftover backup from previous crashed run
    if backup_dir.exists():
        shutil.rmtree(backup_dir)

    # backup original files
    shutil.copytree(original_dir, backup_dir)

    try:
        # copy benchmark files in
        for f in case_dir.glob("*.java"):
            shutil.copy(f, original_dir / f.name)

        # load base config
        base_config_path = Path(CONFIG_MAP[module])
        with open(base_config_path) as f:
            config = json.load(f)

        # write temp config
        temp_config = Path("benchmark/temp_config.json")
        with open(temp_config, "w") as f:
            json.dump(config, f)

        # run driver
        result = subprocess.run(
            ["python", "-m", "scripts.driver", str(temp_config)],
            capture_output=True,
            text=True,
            timeout=120
        )

        temp_config.unlink()
        print(f"DEBUG OUTPUT: {repr(result.stdout)}")
        print(f"DEBUG STDERR: {repr(result.stderr)}")
        return result.stdout

    finally:
        # always restore originals even if something crashes
        shutil.rmtree(original_dir)
        shutil.copytree(backup_dir, original_dir)
        shutil.rmtree(backup_dir)

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
            output = run_case(module, case_dir)
            actual = parse_output(output)
            
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

if __name__ == "__main__":
    main()