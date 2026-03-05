import json
import math
import subprocess
from pathlib import Path
from openai import OpenAI

# ---------- config ----------
EMB_MODEL = "text-embedding-3-small"   # embeddings
CHAT_MODEL = "gpt-4.1-mini"            # feedback model
EMB_PATH = Path("data/chunks_with_embeddings.jsonl")

client = OpenAI()

# ---------- java toolchain ----------
def compile_java(java_file: str) -> dict:
    cmd = ["javac", java_file]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        return {"status": "compile_error", "stdout": p.stdout, "stderr": p.stderr, "returncode": p.returncode}
    return {"status": "ok", "stdout": p.stdout, "stderr": p.stderr, "returncode": p.returncode}

def run_java(main_class: str, timeout_sec: float = 2.0) -> dict:
    cmd = ["java", main_class]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
    except subprocess.TimeoutExpired as e:
        return {"status": "timeout", "stdout": e.stdout or "", "stderr": e.stderr or "", "returncode": None}
    if p.returncode != 0:
        return {"status": "runtime_error", "stdout": p.stdout, "stderr": p.stderr, "returncode": p.returncode}
    return {"status": "ok", "stdout": p.stdout, "stderr": p.stderr, "returncode": p.returncode}

# ---------- retrieval ----------
def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)

def load_chunks():
    chunks = []
    with EMB_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            if rec.get("embedding") is None:
                continue
            chunks.append(rec)
    return chunks

def embed_text(s: str):
    resp = client.embeddings.create(model=EMB_MODEL, input=s)
    return resp.data[0].embedding

def retrieve(query: str, k: int = 5):
    q = embed_text(query)
    chunks = load_chunks()
    scored = []
    for rec in chunks:
        scored.append((cosine(q, rec["embedding"]), rec))
    scored.sort(key=lambda t: t[0], reverse=True)
    return scored[:k]

# ---------- prompt + gpt ----------
def build_prompt(error_kind: str, error_text: str, top_chunks):
    refs = []
    for score, rec in top_chunks:
        refs.append(
            f"[M{rec['module'][1:]} slide {rec['page']}] {rec['text']}"
        )
    refs_block = "\n\n".join(refs)

    return f"""You are a TA for a Data Structures & Algorithms (Java) course.

Student issue type: {error_kind}

Error output (verbatim):
{error_text}

Relevant course slides (verbatim text extracts):
{refs_block}

Rules:
- Explain the error cause in plain Java terms.
- Point the student to 1–2 relevant slides by number.
- Do NOT give a full solution implementation.
- If the error output is vague, ask 1 targeted question.

Output format exactly:
Summary:
Likely cause:
Where to look:
Next action:
"""

def gpt_feedback(prompt: str) -> str:
    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": "You write short, direct course feedback."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content

def main():
    java_file = "M4/Sort.java"
    main_class = "M4.Sort"  # package M4; class Sort

    c = compile_java(java_file)
    if c["status"] != "ok":
        query = c["stderr"]
        top = retrieve(query, k=5)
        prompt = build_prompt("compile_error", c["stderr"], top)
        print(gpt_feedback(prompt))
        return

    r = run_java(main_class, timeout_sec=2.0)
    if r["status"] != "ok":
        query = r["stderr"]
        top = retrieve(query, k=5)
        prompt = build_prompt(r["status"], r["stderr"], top)
        print(gpt_feedback(prompt))
        return

    print("Program ran successfully. (No feedback generated.)")

if __name__ == "__main__":
    main()
