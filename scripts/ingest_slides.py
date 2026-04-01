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
    )
    
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    return [{"text": doc, "slide": meta["slide"]} for doc, meta in zip(docs, metas)]

def main():
    config_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("configs/m4_sorts.json")
    with open(config_path, "r") as f:
        config = json.load(f)
    
    slides_path = Path(config["slides_pdf"])
    db_path = Path(config["db_path"])
    extracted_path = slides_path.with_suffix("").parent / (slides_path.stem + "_extracted.json")
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # load from cache if exists, otherwise extract
    if extracted_path.exists():
        print("Loading from cached extraction...")
        with open(extracted_path, "r", encoding="utf-8") as f:
            slide_texts = json.load(f)
    else:
        images = pdf_to_images(slides_path)
        print(f"Loaded {len(images)} slides")
        slide_texts = []
        for i, image in enumerate(images):
            print(f"Processing slide {i+1}/{len(images)}...")
            text = extract_text_from_image(image, client)
            slide_texts.append({"slide": i+1, "text": text})
        with open(extracted_path, "w", encoding="utf-8") as f:
            json.dump(slide_texts, f, ensure_ascii=False, indent=2)

    print(f"Loaded {len(slide_texts)} slides")

    chroma_client = chromadb.PersistentClient(path=str(db_path))
    collection = chroma_client.get_or_create_collection(name="slides")
    if collection.count() > 0:
        print(f"Vector store already populated with {collection.count()} slides, skipping embedding.")
    else:
        embed_and_store(slide_texts, db_path, client)

if __name__ == "__main__":
    main()