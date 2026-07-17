
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
class QuestionRequest(BaseModel):       # So, that FastAPI understand what the request does sender is sending(is it string or Number, etc)
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


