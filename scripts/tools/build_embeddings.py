import json
from pathlib import Path
from openai import OpenAI

IN_PATH = Path("data/chunks.jsonl")
OUT_PATH = Path("data/chunks_with_embeddings.jsonl")
MODEL = "text-embedding-3-small"

client = OpenAI()

def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with IN_PATH.open("r", encoding="utf-8") as input_file, OUT_PATH.open("w", encoding="utf-8") as out:
        for line in input_file:
            record = json.loads(line)

            text = record.get("text", "").strip()
            if not text:
                record["embedding"] = None
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                continue

            resp = client.embeddings.create(
                model=MODEL,
                input=text
            )
            record["embedding"] = resp.data[0].embedding

            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1

    print(f"Embedded {count} chunks into {OUT_PATH}")

if __name__ == "__main__":
    main()
