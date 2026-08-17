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

#--reload — tells Uvicorn to automatically restart the server whenever you save changes to your code — equivalent to running Express with nodemon, instead of manually stopping/restarting node server.js every time you edit something.

#fastapi is like Express in that it provides a framework for defining routes and handling HTTP requests, but it also has built-in support for data validation, serialization, and automatic API documentation generation. FastAPI is designed to be fast and efficient, leveraging Python's type hints to provide better developer experience and performance.
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# BaseModel is a class from the Pydantic library, equivalent of a TS interface, except it also validates incoming data at runtime.
#this Pydantic version actually checks at runtime that incoming JSON has a message field that's genuinely a string
from app.rag.answer import answer_question
from typing import Dict, List
#creates the application object. Direct equivalent of const app = express().
app = FastAPI()

# Allow requests from the local Angular dev server, plus the deployed frontend
# once it has a real URL. Update the second origin once the frontend is deployed.
# Same role as app.use(cors()) in Express.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "https://docs-rag-assistant-frontend-224143145108.europe-west3.run.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory store: sessionId -> list of past messages
# {} means an empty dictionary, which is Python's built-in key-value store. In TypeScript, you'd use an object literal: const conversations: Record<string, any[]> = {};
conversations: Dict[str, List[Message]] = {}

#The @ symbol placed directly above a function is Python's way of "wrapping" that function with extra behavior
#conceptually it's doing the same job as:  app.get('/', (req, res) => { ... });
#FastAPI is smart enough to automatically turn a returned Python dict into a JSON HTTP response unlike Express where you'd explicitly write res.json({ status: 'ok' })
@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/chat")
def chat(request: ChatRequest):
    #TS equivalent would be:
    #const history = conversations[request.sessionId] || [];
    # get is a safe lookup. If the sessionId doesn't exist in conversations, it returns the default value (an empty list) instead of throwing an error. This is similar to using the nullish coalescing operator (??) in TypeScript.
    # get only works with dictionaries.
    history: List[Message] = conversations.get(request.sessionId, [])

    answer_text = answer_question(request.message, history)

    # Now constructing real Message objects instead of plain dicts, to match the List[Message] type above.
    history.append(Message(role="user", content=request.message))
    history.append(Message(role="assistant", content=answer_text))
    # completely replaces the old history with the new one, so that next time the user sends a message, the assistant will have the full conversation context.
    conversations[request.sessionId] = history

    return {
        "text": answer_text,
        "buttons": []
    }