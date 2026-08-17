# to rebuild the database after knowledgebase updates, delete the existing database with Remove-Item -Recurse -Force data\chroma_db 
# and run `python app/rag/ingest.py` in the terminal
#imports Python's built-in tool for working with file paths. The TS equivalent of an import statement
from pathlib import Path
import chromadb

KNOWLEDGE_DIR = Path("data/knowledge")

chunks = []  # This will hold every chunk we create, across all files

# Iterate over all Markdown files in the knowledge directory.
# file_path.read_text(encoding="utf-8") — opens the file and returns its entire contents as one string
# glob("*.md") — finds all files in the directory that match the pattern "*.md" (i.e., all Markdown files)
for file_path in KNOWLEDGE_DIR.glob("*.md"):

    # Read the file content with UTF-8 encoding, handling potential BOM
    text = file_path.read_text(encoding="utf-8-sig")

    # Split the text into sections based on the Markdown header "##"
    sections = text.split("##")
    # sections[0] is everything before the first "##" heading — in these knowledge
    # base files that's the H1 title PLUS a metadata block (Source, Retrieved date,
    # Document type, etc). We only want the H1 line itself as the "title" that gets
    # prepended to every chunk — otherwise the entire metadata block gets duplicated
    # into every single chunk from this file, wasting retrieval context budget on
    # repeated boilerplate instead of actual content.
    # split("\n")[0] takes just the first line (the H1); everything after it in
    # sections[0] (the metadata block) is intentionally dropped here.
    title = sections[0].lstrip("#").strip().split("\n")[0].strip()
    body_sections = sections[1:]  # The rest are body sections

    for section in body_sections:
        #strip also removes \n and \r characters from the beginning and end of the string, which is useful for cleaning up text data.
        heading, _, content = section.strip().partition("\n")  # Split the section into heading and content at the first newline
        heading = heading.strip()  # Remove leading and trailing whitespace from the heading
        content = content.strip()  # Remove leading and trailing whitespace from the content

        chunk_text = f"{title} - {heading}\n{content}"  # Combine title, heading, and content into a single string
        chunks.append({
            "text": chunk_text,
            "source": file_path.name,
            "heading": heading,
        })

print(f"Total chunks created: {len(chunks)}")  # Print the total number of chunks created

# Get the text from every chunk, as a plain list of strings. [EXPRESSION for ITEM in LIST]
# Equivalent to the TypeScript syntax: chunks.map(chunk => chunk.text)
chunk_texts = [chunk["text"] for chunk in chunks]

# PersistentClient both CONNECTS to and CREATES the database, depending on whether
# data/chroma_db already exists. No separate "create database" step needed —
# unlike Postgres, there's no server running beforehand; this one line does both jobs.
# Think of it like SQLite: pointing at a .db file that doesn't exist yet just creates it.
client = chromadb.PersistentClient(path="data/chroma_db")

# get_or_create_collection is the equivalent of CREATE TABLE IF NOT EXISTS —
# safe to run every time, won't duplicate or error if "pharma_knowledge" already exists.
# A collection = a table: one database (chroma_db) can hold multiple collections.
collection = client.get_or_create_collection(name="pharma_knowledge")

# Chroma's built-in embedding function handles converting text to vectors internally.
# We pass query_texts instead of query_embeddings — no manual embedding step needed.
# This removes the need for sentence-transformers and torch entirely, keeping the
# Docker image small enough to deploy comfortably.
collection.add(
    # range is the TS equivalent to Array.from({length: len(chunks)}, (_, i) => i.toString())
    ids=[str(i) for i in range(len(chunks))],  # Unique IDs for each chunk
    documents=chunk_texts,  # The actual text of each chunk — Chroma embeds these automatically
    metadatas=[{"source": chunk["source"], "heading": chunk["heading"]} for chunk in chunks]  # Metadata for each chunk, including source file and heading
)

print(f"Collection now contains {collection.count()} chunks")  # Print the total number of items in the collection