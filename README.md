# DSA Autograder

An automated grading and feedback system for programming assignments. Designed to evaluate student code submissions, retrieve relevant course material from lecture slides, and generate adaptive, escalating feedback powered by an LLM. Originally built for a Java Data Structures and Algorithms course, with an architecture designed to generalize across CS courses.

---

## Overview

Students submit Java files through Canvas. The autograder compiles and runs each submission against a test harness, retrieves relevant content from course slides via a vector store, and uses the OpenAI API to generate targeted feedback — escalating from vague hints to full solutions based on how many times the student has attempted the assignment.

The system is modular by design: each assignment has a config file and an adapter that defines what to test and how. Everything else — slide ingestion, retrieval, feedback generation, attempt tracking — is course-agnostic.

---

## How It Works

1. **Slide ingestion (one-time setup)** — Course slides are ingested as a PDF. Each slide is processed by GPT-4o vision to extract text including pseudocode from diagrams, embedded into vectors, and stored in a local Chroma vector database.
2. **Security scan** — The student's `.java` file is scanned for banned APIs (filesystem access, networking, `System.exit`, etc.) before anything runs.
3. **Compilation** — The student's file is compiled with `javac`. Compile errors are caught and fed to the feedback system.
4. **Harness generation** — A Java test harness is dynamically generated for each method in the assignment. The harness runs the student's method against test cases and compares output to a known correct answer.
5. **Execution** — The harness is compiled and run with a timeout. Runtime errors and exceptions are caught and reported.
6. **Retrieval** — The student's error is used to query the vector store, retrieving the most relevant slide content to use as context for feedback.
7. **Adaptive feedback** — The attempt count for this student and method determines the hint level. The LLM returns a short explanation and concrete next steps in JSON format, escalating from vague hints to full solutions across attempts.

---

## Project Structure

```
DSA-autograder/
├── adapters/
│   ├── base.py                        # Base adapter class (interface)
│   ├── registry.py                    # Adapter registry for dynamic loading
│   ├── m4_sorts.py                    # Module 4: Sorting Algorithms
│   ├── m5_data_structures.py          # Module 5: Stack, Queue, LinkedList, BST
│   ├── m6_dynamic_programming.py      # Module 6: Rod Cutting, LCS
│   └── m7_graphs.py                   # Module 7: BFS, Bellman-Ford, Dijkstra
├── configs/
│   ├── m4_sorts.json                  # Config for M4
│   ├── m5_data_structures.json        # Config for M5
│   ├── m6_dp.json                     # Config for M6
│   └── m7_graphs.json                 # Config for M7
├── scripts/
│   ├── driver.py                      # Main entry point
│   ├── feedback.py                    # LLM feedback generation
│   ├── ingest_slides.py               # Slide ingestion and vector retrieval
│   ├── attempt_tracker.py             # Per-student attempt tracking
│   └── run_compile.py                 # Java compile, run, and security scan
├── slides/                            # Course slide PDFs
├── vector_store/                      # Chroma vector databases (generated)
├── submissions/                       # Student attempt history (generated)
├── harness/
│   └── Harness.java                   # Auto-generated test harness (do not edit)
├── M4/                                # Student submission files (example)
├── M5/                                # Student submission files (example)
├── M6/                                # Student submission files (example)
└── M7/                                # Student submission files (example)
```

---

## Setup

### Dependencies

```bash
pip install -r requirements.txt
```

Also requires **Poppler** for PDF processing (Windows: download from [poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases) and add `bin/` to PATH).

### Environment Variables

```bash
set OPENAI_API_KEY=your_key_here   # Windows
export OPENAI_API_KEY=your_key_here # Mac/Linux
```

To change the OpenAI model:
```bash
set OPENAI_MODEL=gpt-4.1-mini
```

### Slide Ingestion (one-time per assignment)

```bash
python -m scripts.ingest_slides configs/m4_sorts.json
python -m scripts.ingest_slides configs/m5_data_structures.json
python -m scripts.ingest_slides configs/m6_dp.json
python -m scripts.ingest_slides configs/m7_graphs.json
```

This processes each slide PDF, extracts text via GPT-4o vision, and stores embeddings in the vector store. Only needs to run once per assignment setup.

---

## Running

```bash
python -m scripts.driver configs/m4_sorts.json
python -m scripts.driver configs/m5_data_structures.json
python -m scripts.driver configs/m6_dp.json
python -m scripts.driver configs/m7_graphs.json
```

Defaults to `configs/m4_sorts.json` if no config is specified.

---

## Output

Each method or class in the assignment produces a JSON result:

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

Feedback escalates across attempts:
- **Attempt 1** — vague hint pointing to the relevant concept
- **Attempt 2** — more specific, referencing pseudocode
- **Attempt 3** — detailed explanation of what is wrong
- **Attempt 4+** — full solution with explanation

---

## Adding a New Assignment

1. Create a config file in `configs/` — copy an existing one and update the fields
2. Create `adapters/mX_name.py` with a class extending `Adapter`
3. Implement `methods()` and `write_harness()`
4. Add the adapter to `adapters/registry.py`
5. Run slide ingestion for the new assignment's PDF
6. Run with `python -m scripts.driver configs/your_config.json`

---

## Modules Covered

| Module | Assignment | Classes/Methods |
|--------|------------|-----------------|
| M4 | Sorting Algorithms | `insertionSort`, `merge_sort`, `merge`, `quick_sort`, `partition` |
| M5 | Basic Data Structures | `Stack` (empty, push, pop), `Queue` (enqueue, dequeue), `LinkedList` (insert, search, delete), `BinarySearchTree` (insert, inorder_tree_walk, search, iterative_search, minimum, maximum, successor) |
| M6 | Dynamic Programming | `RodCut` (memoized_cut_rod, bottom_up_cut_rod, extended_bottom_up_cut_rod), `LCS` (lcs_length) |
| M7 | Graph Algorithms | `Graph` (bfs, bellman_ford, dijkstra) |

---

## Planned Features

- **Canvas integration** — automatically pull student submissions and push feedback/grades back
- **Batch grading** — grade an entire class roster in one run
- **Auto-routing** — detect which assignment a submission belongs to automatically
- **Level 1 harness generation** — professor specifies test cases in config file, system generates harness automatically
- **Non-programming assignment support** — extend to courses beyond programming (discrete math, theory, etc.)
- **Course agnostic expansion** — support any CS course with slides and assignments, not just DSA