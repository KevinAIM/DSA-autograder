import os
import base64
from pathlib import Path
import sys
from pdf2image import convert_from_path
from openai import OpenAI
import chromadb
import io
import json


def pdf_to_images(pdf_path: Path) -> list:
    images = convert_from_path(str(pdf_path))
    return images

def extract_text_from_image(image, client: OpenAI) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    image_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_data}"}
                    },
                    {
                        "type": "text",
                        "text": "Extract all text from this slide including any pseudocode, algorithms, or code in diagrams. Return only the extracted text, no commentary."
                    }
                ]
            }
        ]
    )
    return response.choices[0].message.content


def embed_and_store(slide_texts: list, db_path: Path, client: OpenAI) -> None:
    # create chroma client and collection
    chroma_client = chromadb.PersistentClient(path=str(db_path))
    collection = chroma_client.get_or_create_collection(name="slides")

    print("Embedding and storing slides...")
    for slide in slide_texts:
        slide_num = slide["slide"]
        text = slide["text"]

        #skip empty slide
        if not text.strip():
            continue

        #embed the text
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        embedding = response.data[0].embedding

        #store in chroma. Upsert will update if exists, otherwise insert
        collection.upsert(
            ids=[f"slide_{slide_num}"],
            embeddings=[embedding],
            documents=[text],
            metadatas=[{"slide": slide_num}]
        )

    print(f"Stored {len(slide_texts)} slides in Chroma")

def query_slides(query: str, db_path: Path, client: OpenAI, n_results: int = 3) -> list:
    chroma_client = chromadb.PersistentClient(path=str(db_path))
    collection = chroma_client.get_or_create_collection(name="slides")
    
    # embed the query
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    query_embedding = response.data[0].embedding
    
    # search
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results #return top n results
        include=["documents", "metadatas", "distances"]
    )
    
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    return [
        {
            "text": doc,
            "slide": meta["slide"],
            "distance": round(dist, 4),
            "retrieval_confidence": round(max(0, 1 - dist), 4)
        }
        for doc, meta, dist in zip(docs, metas, distances)
    ]

def main():
    config_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("configs/m4_sorts.json")
    with open(config_path, "r") as f:
        config = json.load(f)

    db_path = Path(config["db_path"])
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # collect all slide files to process
    slide_files = []

    # old style config — single slides_pdf
    if "slides_pdf" in config:
        slide_files.append(Path(config["slides_pdf"]))

    # new style config — files array from setup_course
    for f in config.get("files", []):
        path = f.get("url") or f.get("name")
        local_path = Path("slides") / f["name"]
        if not local_path.exists():
            # download from Canvas if not already local
            print(f"Downloading {f['name']}...")
            import requests
            token = os.getenv("CANVAS_TOKEN", "")
            r = requests.get(f["url"], headers={"Authorization": f"Bearer {token}"})
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(r.content)
        slide_files.append(local_path)

    if not slide_files:
        print("[ERROR] No slide files found in config.")
        return

    # check if vector store already populated
    chroma_client = chromadb.PersistentClient(path=str(db_path))
    collection = chroma_client.get_or_create_collection(name="slides")
    if collection.count() > 0:
        print(f"Vector store already populated with {collection.count()} slides, skipping.")
        return

    # process each file
    all_slide_texts = []
    slide_offset = 0

    for slide_file in slide_files:
        print(f"\nProcessing {slide_file.name}...")
        extracted_path = slide_file.with_suffix("").parent / (slide_file.stem + "_extracted.json")

        if extracted_path.exists():
            print("Loading from cached extraction...")
            with open(extracted_path, "r", encoding="utf-8") as f:
                slide_texts = json.load(f)
        else:
            images = pdf_to_images(slide_file)
            print(f"Loaded {len(images)} slides")
            slide_texts = []
            for i, image in enumerate(images):
                print(f"Processing slide {i+1}/{len(images)}...")
                text = extract_text_from_image(image, client)
                slide_texts.append({"slide": slide_offset + i + 1, "text": text})
            with open(extracted_path, "w", encoding="utf-8") as f:
                json.dump(slide_texts, f, ensure_ascii=False, indent=2)

        all_slide_texts.extend(slide_texts)
        slide_offset += len(slide_texts)

    print(f"\nTotal slides processed: {len(all_slide_texts)}")
    embed_and_store(all_slide_texts, db_path, client)

if __name__ == "__main__":
    main()