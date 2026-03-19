import os
import base64
from pathlib import Path
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
    
    return results["documents"][0]

def main():
    slides_path = Path("slides/CSITBG2 Module 4.pdf")
    db_path = Path("vector_store/dsa_m4")
    extracted_path = Path("slides/CSITBG2 Module 4_extracted.json")
    
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

    embed_and_store(slide_texts, db_path, client)

    results = query_slides("insertion sort pseudocode", db_path, client)
    for r in results:
        print("---")
        print(r[:300]) #print first 300 chars of each result

if __name__ == "__main__":
    main()