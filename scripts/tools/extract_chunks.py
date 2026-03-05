import json
from pathlib import Path
import fitz

PDF_PATH = Path("course_material/M4_slides.pdf")
OUT_PATH = Path("data/chunks.jsonl")

def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    document = fitz.open(PDF_PATH)
    with OUT_PATH.open("w", encoding="utf-8") as out:
        for i, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            record = {
                "module": "M4",
                "source": PDF_PATH.name,
                "page": i,
                "text": text
            }

            out.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f'Wrote {document.page_count} chunks to {OUT_PATH}')

if __name__=="__main__":
    main()