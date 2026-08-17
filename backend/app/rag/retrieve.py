# to run this file: python app/rag/retrieve.py
# Standalone debug script — lets you check what chunks get retrieved for a given
# question without going through the full answer_question() / LLM pipeline.

import chromadb

# Open the existing database — note: get_collection, not get_or_create_collection,
# since we expect it to already exist from running ingest.py
client = chromadb.PersistentClient(path="data/chroma_db")
collection = client.get_collection(name="pharma_knowledge")

# NOTE: no manual embedding model here (previously used sentence-transformers).
# ingest.py relies on ChromaDB's built-in embedding function to embed documents
# at write time, so retrieval must use the same pathway — passing query_texts
# lets Chroma embed the query with that same built-in function. Loading a
# separate sentence-transformers model here would risk using a different
# embedding space than the one the collection was actually built with, and it
# would reintroduce the sentence-transformers/torch dependency we deliberately
# dropped to keep the Docker image small (see ingest.py).

query = "Can paracetamol be taken with warfarin?"

results = collection.query(
    query_texts=[query],
    n_results=5,
)

documents = results["documents"][0]  # Get the documents from the results
metadatas = results["metadatas"][0]  # Get the metadata from the results

for doc, metadata in zip(documents, metadatas):
    print(f"--- from {metadata['source']} ({metadata['heading']}) ---")
    print(doc)
    print()