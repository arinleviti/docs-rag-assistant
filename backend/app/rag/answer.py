from app.schemas import Message
import os
from typing import List
import chromadb
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# --- Retrieval setup ---
client = chromadb.PersistentClient(path="data/chroma_db")
collection = client.get_collection(name="pharma_knowledge")

# --- Generation setup ---
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])


def retrieve_context(question, n_results=8):
    # query_texts (not query_embeddings) — Chroma embeds the query internally
    # using the same built-in embedding function ingest.py used to build the
    # collection, so this has to stay consistent with ingest.py's approach.
    results = collection.query(
        query_texts=[question],
        n_results=n_results,
    )
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    # Zip document text together with its source metadata so the LLM can see,
    # per chunk, exactly which source document it came from — this is what
    # makes grounded citation possible in the answer (e.g. "per the SmPC for
    # the oral solution..."), rather than the model just blending everything
    # into one undifferentiated block of context.
    return list(zip(documents, metadatas))


def format_context(chunks_with_metadata):
    formatted = []
    for text, metadata in chunks_with_metadata:
        source = metadata.get("source", "unknown source")
        formatted.append(f"[Source file: {source}]\n{text}")
    return "\n\n---\n\n".join(formatted)


def answer_question(question: str, history: List[Message] = None) -> str:

    if history is None:
        history = []

    context_chunks = retrieve_context(question)
    context_text = format_context(context_chunks)

    system_prompt = (
        "You are a clinical reference assistant for healthcare professionals, answering "
        "questions about paracetamol (acetaminophen) using official EU/UK regulatory "
        "documentation: Summaries of Product Characteristics (SmPCs), a Public Assessment "
        "Report, an EMA explainer on SmPC structure, and a synthesised drug-interactions "
        "reference.\n\n"
        "GROUNDING — this is the most important rule:\n"
        "Answer ONLY using the information in the Context below. Do not add dosing, "
        "interaction, or safety information from your own general knowledge, even if you "
        "believe it to be correct — the whole point of this tool is that every answer "
        "traces back to a specific, current, cited source document, not to background "
        "training knowledge that could be outdated or unverified.\n\n"
        "CITATION:\n"
        "When you answer, name the specific source file(s) your answer draws from (shown "
        "as \"[Source file: ...]\" in the context), e.g. \"per the SmPC for the oral "
        "solution (paracetamol-oral-solution-500mg-5ml-smpc.md)...\". If two source "
        "documents differ (e.g. tablet vs oral solution formulation), state both and be "
        "explicit that they differ rather than blending them into one answer.\n\n"
        "SCOPE AND REFUSAL:\n"
        "If the Context does not contain enough information to answer the question, say so "
        "explicitly rather than guessing or inferring — for example: \"The provided "
        "reference documents don't cover this; please consult the full SmPC, the BNF, or "
        "another authoritative source.\" Do not speculate about dosing, interactions, or "
        "contraindications that are not stated in the Context.\n\n"
        "AUDIENCE AND TONE:\n"
        "Assume the reader is a healthcare professional (doctor, pharmacist, or nurse), so "
        "you can use clinical terminology directly without simplifying it for a lay "
        "audience. Be precise and concise. Use the exact figures, thresholds, and terms "
        "given in the source documents rather than paraphrasing numbers loosely.\n\n"
        "FORMATTING:\n"
        "When a table cell needs to hold more than one point, use a proper HTML list "
        "(<ul><li>...</li></ul>) inside that cell rather than separating items with dashes "
        "and line breaks — markdown tables render each cell's content as a single line, so "
        "plain dash-separated text collapses into a hard-to-read block.\n\n"
        "DISCLAIMER:\n"
        "This tool supplements, but does not replace, direct consultation of the full "
        "SmPC, the BNF, or other authoritative clinical references, and does not replace "
        "clinical judgement.\n\n"
        f"Context:\n{context_text}"
    )

    system_message = Message(role="system", content=system_prompt)
    messages = [system_message.model_dump()]
    messages.extend([m.model_dump() for m in history])
    messages.append({"role": "user", "content": question})

    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    question = "Can paracetamol be taken with warfarin, and what should a doctor watch for?"
    print(f"Question: {question}\n")
    print(f"Answer: {answer_question(question)}")