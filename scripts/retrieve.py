import json
import math
from pathlib import Path
from openai import OpenAI

EMB_PATH = Path("data/chunks_with_embeddings.jsonl")
MODEL = "text-embedding-3-small"

client = None

def _client():
    global client
    if client is None:
        client = OpenAI()
    return client


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
            emb = rec.get("embedding")
            if emb is None:
                continue
            chunks.append(rec)
    return chunks

def embed_query(q: str):
    resp = _client().embeddings.create(model=MODEL, input=q)
    return resp.data[0].embedding

def top_k(query: str, k: int = 5):
    q_emb = embed_query(query)
    chunks = load_chunks()

    scored = []
    for rec in chunks:
        score = cosine(q_emb, rec["embedding"])
        scored.append((score, rec))

    scored.sort(key=lambda t: t[0], reverse=True)
    return scored[:k]

def main():
    query = "insertion sort pseudocode"
    results = top_k(query, k=5)

    for score, rec in results:
        snippet = rec["text"].replace("\n", " ")
        snippet = snippet[:160] + ("..." if len(snippet) > 160 else "")
        print(f"{score:.4f} | {rec['module']} | page {rec['page']} | {snippet}")


def retrieve(query: str, k: int = 5, data_path: str = "data/chunks_with_embeddings.jsonl"):
    """
    Return top-k chunk dicts (not (score, rec) tuples).
    Adds a stable 'chunk_id' field if missing.
    """
    global EMB_PATH
    EMB_PATH = Path(data_path)

    results = top_k(query, k=k)  # list of (score, rec)
    out = []
    for score, rec in results:
        # copy so we don't mutate cached recs
        d = dict(rec)
        d["score"] = float(score)

        # normalize identifiers
        if "chunk_id" not in d:
            # best-effort stable id
            mod = d.get("module", "unknown")
            page = d.get("page", "unknown")
            d["chunk_id"] = f"{mod}_p{page}_s{len(out)+1}"

        out.append(d)
    return out


if __name__ == "__main__":
    main()
