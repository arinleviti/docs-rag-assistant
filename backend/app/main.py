# --- DEV ---
# uvicorn app.main:app --reload

# --- DEPLOYMENT (run these in order from the backend/ root, once a container registry
# and Cloud Run/App Service target are set up for this project) ---
# 1. docker build -t docs-rag-assistant-backend .
# 2. docker tag docs-rag-assistant-backend <registry-path>/docs-rag-assistant-backend:latest
# 3. docker push <registry-path>/docs-rag-assistant-backend:latest
# 4. <deploy command for your chosen platform — e.g. gcloud run deploy, az webapp, etc.>

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
    allow_origins=["http://localhost:4200", "https://REPLACE-WITH-DEPLOYED-FRONTEND-URL"],
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