# DSA Autograder

An automated grading and feedback system for programming assignments. Designed to evaluate student code submissions, retrieve relevant course material from lecture slides, and generate adaptive, escalating feedback powered by an LLM. Originally built for a Java Data Structures and Algorithms course, with an architecture designed to generalize across CS courses.



## Overview

Students submit Java files through Canvas. The autograder compiles and runs each submission against a test harness, retrieves relevant content from course slides via a vector store, and uses the OpenAI API to generate targeted feedback — escalating from vague hints to full solutions based on how many times the student has attempted the assignment.

The system is modular by design: each assignment has a config file and an adapter that defines what to test and how. Everything else — slide ingestion, retrieval, feedback generation, attempt tracking — is course-agnostic.



## How It Works

1. **Slide ingestion (one-time setup)** — Course slides are ingested as a PDF. Each slide is processed by GPT-4o vision to extract text including pseudocode from diagrams, embedded into vectors, and stored in a local Chroma vector database.
2. **Security scan** — The student's `.java` file is scanned for banned APIs (filesystem access, networking, `System.exit`, etc.) before anything runs.
3. **Compilation** — The student's file is compiled with `javac`. Compile errors are caught and fed to the feedback system.
4. **Harness generation** — A Java test harness is dynamically generated for each method in the assignment. The harness runs the student's method against test cases and compares output to a known correct answer.
5. **Execution** — The harness is compiled and run with a timeout. Runtime errors and exceptions are caught and reported.
6. **Retrieval** — The student's error is used to query the vector store, retrieving the most relevant slide content to use as context for feedback.
7. **Adaptive feedback** — The attempt count for this student and method determines the hint level. The LLM returns a short explanation, concrete next steps, and resource links in JSON format, escalating across attempts.



## Hint Escalation

Feedback escalates across attempts, with resource links tied to each hint level:

| Attempt | Hint Level | Resource |
|---------|------------|----------|
| 1 | Vague hint pointing to the relevant concept | Link to full slide PDF |
| 2 | Specific hint referencing the relevant pseudocode line and slide number | Link to exact slide page |
| 3 | Detailed explanation of what is wrong and why (no solution given) | Panopto video link at relevant timestamp |
| 4+ | Full solution with complete explanation | No link |



## Project Structure

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
│   ├── formatter.py                   # Student-facing terminal output formatting
│   ├── output_formatter.py            # Windows-safe ASCII output formatter
│   ├── ingest_slides.py               # Slide ingestion and vector retrieval
│   ├── video_search.py                # Caption-based Panopto timestamp search
│   ├── attempt_tracker.py             # Per-student attempt tracking
│   └── run_compile.py                 # Java compile, run, and security scan
├── slides/                            # Course slide PDFs
├── captions/                          # Panopto caption files per video (M4-M7)
├── vector_store/                      # Chroma vector databases (generated)
├── submissions/                       # Student attempt history (generated)
├── benchmark/
│   ├── cases/                         # Test case Java files per module
│   ├── expected/                      # Expected output JSON per case
│   └── run_benchmark.py               # Benchmark runner (20 test cases, M4-M7)
├── harness/
│   └── Harness.java                   # Auto-generated test harness (do not edit)
├── M4/                                # Student submission files (example)
├── M5/                                # Student submission files (example)
├── M6/                                # Student submission files (example)
└── M7/                                # Student submission files (example)

## Setup

### Dependencies

pip install -r requirements.txt


Also requires **Poppler** for PDF processing (Windows: download from [poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases) and add `bin/` to PATH).

### Environment Variables

set OPENAI_API_KEY=your_key_here   # Windows
export OPENAI_API_KEY=your_key_here # Mac/Linux


To change the OpenAI model:
set OPENAI_MODEL=gpt-4.1-mini


### Slide Ingestion (one-time per assignment)

python -m scripts.ingest_slides configs/m4_sorts.json
python -m scripts.ingest_slides configs/m5_data_structures.json
python -m scripts.ingest_slides configs/m6_dp.json
python -m scripts.ingest_slides configs/m7_graphs.json

This processes each slide PDF, extracts text via GPT-4o vision, and stores embeddings in the vector store. Only needs to run once per assignment setup.

## Running

python -m scripts.driver configs/m4_sorts.json
python -m scripts.driver configs/m5_data_structures.json
python -m scripts.driver configs/m6_dp.json
python -m scripts.driver configs/m7_graphs.json

Defaults to `configs/m4_sorts.json` if no config is specified.

## Benchmark

A regression test suite of 20 cases across M4-M7 covering correct submissions, common errors, compile errors, runtime errors, and banned API usage.

python benchmark/run_benchmark.py


Expected output: `Results: 20/20 passed`

## Output

Each method or class produces a result printed to the terminal:

[FAIL] insertionSort
 Your index calculation at the insertion step is incorrect, causing an ArrayIndexOutOfBoundsException.
   1. Review the line where the key is placed after the while loop.
   2. Compare your index to the pseudocode on Slide 4.
   3. Ensure the index stays within array bounds.

   Slides: https://kevinaim.github.io/DSA-autograder/slides/CSITBG2%20Module%204.pdf#page=4


Possible statuses: `[PASS]`, `[FAIL]`, `[RUNTIME ERROR]`, `[COMPILE ERROR]`, `[BLOCKED]`.

## Config File Format

Each module config includes:

{
  "name": "M4 Sorting Algorithms",
  "module": "M4",
  "adapter": "M4SortsAdapter",
  "student_files": ["M4/Sort.java"],
  "db_path": "vector_store/dsa_m4",
  "slides_pdf": "slides/CSITBG2 Module 4.pdf",
  "slides_url": "https://kevinaim.github.io/DSA-autograder/slides/CSITBG2%20Module%204.pdf",
  "package": "M4",
  "student_class": "Sort",
  "timeout_sec": 5.0,
  "videos": [
    {
      "title": "M4a: Insertion Sort",
      "panopto_url": "https://montclair.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=...",
      "captions": "captions/m4a_insertion_sort.txt",
      "methods": ["insertionSort"]
    }
  ]
}


## Adding a New Assignment

1. Create a config file in `configs/` — copy an existing one and update the fields
2. Create `adapters/mX_name.py` with a class extending `Adapter`
3. Implement `methods()` and `write_harness()`
4. Add the adapter to `adapters/registry.py`
5. Run slide ingestion for the new assignment's PDF
6. Add caption files for each video under `captions/`
7. Run with `python -m scripts.driver configs/your_config.json`


## Modules Covered

| Module | Assignment | Classes/Methods |
|--------|------------|-----------------|
| M4 | Sorting Algorithms | `insertionSort`, `merge_sort`, `merge`, `quick_sort`, `partition` |
| M5 | Basic Data Structures | `Stack` (empty, push, pop), `Queue` (enqueue, dequeue), `LinkedList` (insert, search, delete), `BinarySearchTree` (insert, inorder_tree_walk, search, iterative_search, minimum, maximum, successor) |
| M6 | Dynamic Programming | `RodCut` (memoized_cut_rod, bottom_up_cut_rod, extended_bottom_up_cut_rod), `LCS` (lcs_length) |
| M7 | Graph Algorithms | `Graph` (bfs, bellman_ford, dijkstra) |



## Planned Features

- **Canvas integration** — automatically pull student submissions and push feedback/grades back
- **Batch grading** — grade an entire class roster in one run
- **Auto-routing** — detect which assignment a submission belongs to automatically
- **Level 1 harness generation** — professor specifies test cases in config file, system generates harness automatically
- **Non-programming assignment support** — extend to courses beyond programming (discrete math, theory, etc.)
- **Course agnostic expansion** — support any CS course with slides and assignments, not just DSA
