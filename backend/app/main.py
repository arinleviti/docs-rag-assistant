# --- DEV ---
# venv\Scripts\Activate.ps1 if venv is not visible
# uvicorn app.main:app --reload

# --- DEPLOYMENT (run from the backend/ root; requires the gcloud CLI authenticated
# and pointed at the target GCP project) ---
# gcloud run deploy docs-rag-assistant-backend --source . --platform managed --region europe-west3 --allow-unauthenticated --max-instances 2 --set-env-vars GROQ_API_KEY=your_key_here
#
# This single command uploads the source, builds the container remotely via
# Cloud Build (using the Dockerfile below), pushes it to Artifact Registry,
# and deploys it to Cloud Run — no local Docker installation required.

# --- KNOWLEDGE BASE UPDATE (run this locally after editing data/knowledge/*.md) ---
# python app/rag/ingest.py
# then redeploy using steps 1-4 above so the new ChromaDB gets baked into the container

from app.schemas import Message, ChatRequest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.rag.answer import answer_question
from typing import Dict, List

app = FastAPI()

# Allow requests from the local Angular dev server, plus the deployed frontend
# once it has a real URL. Update the second origin once the frontend is deployed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "https://docs-rag-assistant-frontend-224143145108.europe-west3.run.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store: sessionId -> conversation history.
# Resets on restart and doesn't scale across multiple instances — fine for
# this project's scope, see README for the production alternative.
conversations: Dict[str, List[Message]] = {}


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.post("/chat")
def chat(request: ChatRequest):
    history: List[Message] = conversations.get(request.sessionId, [])

    answer_text = answer_question(request.message, history)

    history.append(Message(role="user", content=request.message))
    history.append(Message(role="assistant", content=answer_text))
    conversations[request.sessionId] = history

    return {
        "text": answer_text,
        "buttons": []
    }