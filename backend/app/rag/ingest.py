# to rebuild the database after knowledgebase updates, delete the existing database with Remove-Item -Recurse -Force data\chroma_db 
# and run `python app/rag/ingest.py` in the terminal
from pathlib import Path
import chromadb

KNOWLEDGE_DIR = Path("data/knowledge")

chunks = []

for file_path in KNOWLEDGE_DIR.glob("*.md"):

    text = file_path.read_text(encoding="utf-8-sig")

    # Split into sections on "##" headings.
    sections = text.split("##")
    # sections[0] is everything before the first "##" heading — in these knowledge
    # base files that's the H1 title PLUS a metadata block (Source, Retrieved date,
    # Document type, etc). We only want the H1 line itself as the "title" that gets
    # prepended to every chunk — otherwise the entire metadata block gets duplicated
    # into every single chunk from this file, wasting retrieval context budget on
    # repeated boilerplate instead of actual content.
    title = sections[0].lstrip("#").strip().split("\n")[0].strip()
    body_sections = sections[1:]

    for section in body_sections:
        heading, _, content = section.strip().partition("\n")
        heading = heading.strip()
        content = content.strip()

        chunk_text = f"{title} - {heading}\n{content}"
        chunks.append({
            "text": chunk_text,
            "source": file_path.name,
            "heading": heading,
        })

print(f"Total chunks created: {len(chunks)}")

chunk_texts = [chunk["text"] for chunk in chunks]

client = chromadb.PersistentClient(path="data/chroma_db")

collection = client.get_or_create_collection(name="pharma_knowledge")

# Chroma's built-in embedding function handles converting text to vectors
# internally, so we pass query_texts instead of query_embeddings. This
# removes the need for sentence-transformers/torch, keeping the Docker
# image small enough to deploy comfortably. Any script that later queries
# this collection needs to use the same query_texts approach to stay in
# the same embedding space (see answer.py / retrieve.py).
collection.add(
    ids=[str(i) for i in range(len(chunks))],
    documents=chunk_texts,
    metadatas=[{"source": chunk["source"], "heading": chunk["heading"]} for chunk in chunks]
)

print(f"Collection now contains {collection.count()} chunks")