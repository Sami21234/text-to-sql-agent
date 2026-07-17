
import os       # It lets Python communicate with your computer
import sys      # It gives access to Python's runtime.
from fastapi import FastAPI, HTTPException      
from fastapi.middleware.cors import CORSMiddleware      # CORS(Cross Origin Resource Sharing)
from fastapi.staticfiles import StaticFiles     # Files that don't change(css, html, js file, etc.)
from fastapi.responses import FileResponse      # for sending diff files.
from pydantic import BaseModel      # For sending the request that FastAPI understands. 
import uvicorn      # for running the FastAPI server.

sys.path.append(os.path.dirname(__file__))      # Adding the backend folder to the Python's search path

from database import verify_connection
from agent import ask_agent
from safety import sanitize_question, is_safe_query

app = FastAPI(      # Now, creating the FastAPI Server
    title = "SQL Analytics Agent",
    description = "Natural language to SQL for food delivery analytics",
    version = "1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    # The allowed origins are:-
    allow_origins = ["*"],      # IN PRODUCTION CANCEL THIS "*", INSTEAD USE OWN WEBSITES.
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

FRONTEND_DIR = os.path.join(      # joining the connection between backend ---> frontend.
    os.path.dirname(__file__), "..", "frontend"
)

if os.path.exists(FRONTEND_DIR):    # check if folder exists
    app.mount(      # Everything inside frontend, make them available.
        "/static",
        StaticFiles(directory = FRONTEND_DIR),
        name = "static",
    )

# Now, creating the Pydantic Models
class QuestionRequest(BaseModel):       # This class describes the incoming JSON. So that, FastAPI understand what the request does sender is sending(is it string or Number, etc)
    question: str

class AnswerResponse(BaseModel):
    answer: str
    sql: str
    success: bool
    question: str

# Now, let's write the EndPoints.

"""
There are different kinds of HTTP requests:
most of the common use are:-

GET → Read
POST → Create/Send

"""

# 1. Home endpoint
@app.get("/")     # GET --> / --> Run serve_frontend()  
async def serve_frontend():     # async function
    index_path = os.path.join(FRONTEND_DIR, "index.html")   # this becomes: C:\Projects\frontend\index.html, simply building a file path
    if os.path.exists(index_path):      # if file exists, return it.
        return FileResponse(index_path)
    return {"message": "SQL Agent API running"}     # And, if file doesn't exists, do this.

# 2. health endpoint
@app.get("/health")     # GET --> /health --> Run health_check()
async def health_check():
    return {
        "status": "healthy",
        "database": "food_delivery.db",
        "model": "mistral via ollama",
    }

# 3. Post endpoint
"""
Now, imagine our frontend has textbox:
     -----------------------------------------
    | Ask anything about food delivery data   |
    |                                         |
    | [ Which city has most orders? ]         |
    |                                         |
    |          [ Ask AI ]                     |
     ----------------------------------------- 

    User clicks Ask AI.
WHAT SHOULD HAPPEN?
    Frontend
      │
      │
      │ Question
      ▼
    Backend
      │
      │ SQL Query
      ▼
    Database
      │
      │ Result
      ▼
    Frontend

This endpoint handles that entire communication.
"""
# why post --> beacuse in the /ask endpoint the question would have to go inside the URL. 
@app.post("/ask", response_model = AnswerResponse)
async def ask_endpoint(request: QuestionRequest):       # request gets the Question stored in the QuestionRequest object created automatically by the FastAPI.

    # step 1 - Validate question
    is_valid, reason = sanitize_question(request.question)
    if not is_valid:
        raise HTTPException(status_code=400, detail=reason)     # request invalid / user made mistake.

    # step 2 - Run agent
    result = ask_agent(request.question)

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Agent failed")
        )

    return AnswerResponse(      # Final return 
        answer=result["answer"],
        sql=result.get("sql", ""),
        success=result["success"],
        question=request.question,
    )

"""
Until now, Completed Flow Diagram

                 USER
                   │
                   │ Types Question
                   ▼
             Streamlit Frontend
                   │
                   │ POST /ask
                   ▼
         +-----------------------+
         | FastAPI Route         |
         | ask_endpoint()        |
         +-----------------------+
                   │
                   ▼
        request: QuestionRequest
                   │
                   ▼
      sanitize_question(question)
                   │
        ┌──────────┴──────────┐
        │                     │
     Invalid               Valid
        │                     │
        ▼                     ▼
 HTTPException(400)     ask_agent(question)
                              │
                              ▼
                   AI + SQL + Database
                              │
                   ┌──────────┴─────────┐
                   │                    │
                Failed              Success
                   │                    │
                   ▼                    ▼
         HTTPException(500)   AnswerResponse(...)
                                      │
                                      ▼
                         FastAPI converts to JSON
                                      │
                                      ▼
                              React Frontend

"""

