# DSA Autograder

An automated grading and feedback system for a Java Data Structures and Algorithms course. Designed to evaluate student code submissions and generate meaningful, assignment-specific feedback powered by an LLM.

---

## Overview

Students submit Java files through Canvas. The autograder compiles and runs each submission against a test harness, then uses the OpenAI API to generate targeted feedback explaining what went wrong and how to fix it — referencing the same pseudocode taught in lecture.

The system is modular by design: each course module (sorting algorithms, graph algorithms, dynamic programming, etc.) has its own adapter that defines the methods to test, the test logic, and the reference pseudocode.

---

## How It Works

1. **Security scan** — The student's `.java` file is scanned for banned APIs (filesystem access, networking, `System.exit`, etc.) before anything runs.
2. **Compilation** — The student's file is compiled with `javac`. Compile errors are caught and fed to the feedback system.
3. **Harness generation** — A Java test harness is dynamically generated for each method in the assignment. The harness runs the student's method against a set of test cases and compares output to a known correct answer (`Arrays.sort` as oracle for sorting).
4. **Execution** — The harness is compiled and run with a timeout. Runtime errors and exceptions are caught and reported.
5. **Feedback generation** — Results (pass/fail/error + evidence) along with the student's source code and lecture pseudocode are sent to an LLM with a structured prompt. The LLM returns a short explanation and concrete next steps in JSON format.

---

## Project Structure

```
DSA-autograder/
├── adapters/
│   ├── base.py              # Base adapter class (interface)
│   └── m4_sorts.py          # Module 4: Insertion Sort, Merge Sort, Quick Sort
├── scripts/
│   ├── driver.py            # Main entry point
│   ├── feedback.py          # LLM feedback generation
│   └── run_compile.py       # Java compile, run, and security scan
├── harness/
│   └── Harness.java         # Auto-generated test harness (do not edit)
└── M4/
    └── Sort.java            # Student submission (example)
```

---

## Running

```bash
python -m scripts.driver
```

Requires Python 3.9+, Java JDK, and an `OPENAI_API_KEY` environment variable set for feedback generation. Feedback will fall back to a template message if the key is missing.

To change the OpenAI model:
```bash
set OPENAI_MODEL=gpt-4.1-mini   # Windows
export OPENAI_MODEL=gpt-4.1-mini # Mac/Linux
```

---

## Output

Each method in the assignment produces a JSON result:

```json
{
  "status": "fail",
  "method": "merge_sort",
  "testIndex": 2,
  "input": "[2, 1]",
  "expected": "[1, 2]",
  "actual": "[2, 1]",
  "feedback": {
    "short_explanation": "...",
    "next_steps": ["...", "..."],
    "references": [{ "id": "...", "reason": "..." }]
  }
}
```

Possible statuses: `pass`, `fail`, `runtime_error`, `compile_error`, `blocked`, `unknown_harness_output`.

---

## Adding a New Module

1. Create `adapters/mX_name.py` with a class extending `Adapter`
2. Implement `methods()` — return a list of method dicts with `method_name`, `pseudo_code`, `call_args`, and optionally `harness_type`
3. Implement `write_harness()` — or rely on the default `_sort_main()` for standard sorting methods
4. Import and instantiate your adapter in `driver.py`

For methods that are helpers rather than standalone sorts (e.g. `merge`, `partition`), set `harness_type` to `"merge"` or `"partition"` to use custom harness logic.

---

## Modules Covered

| Module | Assignment | Methods |
|--------|------------|---------|
| M4 | Sorting Algorithms | `insertionSort`, `merge_sort`, `merge`, `quick_sort`, `partition` |

---

## Planned Features

- **Canvas integration** — automatically pull student submissions from Canvas via API
- **Batch grading** — run the autograder across an entire class roster and aggregate results
- **Auto-routing** — detect which module a submission belongs to based on class/method names
- **Result export** — output grades and feedback as CSV or push directly back to Canvas gradebook
- **Extended module coverage** — graph algorithms (BFS, Dijkstra, Bellman-Ford), dynamic programming, search trees, and other DSA topics