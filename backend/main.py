
import os       # It lets Python communicate with your computer
import sys      # It gives access to Python's runtime.
import shutil
import sqlite3
import csv
import io
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, HTTPException, UploadFile, File      
from fastapi.middleware.cors import CORSMiddleware      # CORS(Cross Origin Resource Sharing)
from fastapi.staticfiles import StaticFiles     # Files that don't change(css, html, js file, etc.)
from fastapi.responses import FileResponse, StreamingResponse      # for sending diff files.
from pydantic import BaseModel      # For sending the request that FastAPI understands. 
import uvicorn      # for running the FastAPI server.

sys.path.append(os.path.dirname(__file__))      # Adding the backend folder to the Python's search path

from database import verify_connection, get_db_path
from agent import ask_agent, get_llm
from safety import sanitize_question
from schema_inspector import(
    inspect_schema,
    generate_sample_questions,
    validate_sqlite_file
)

app = FastAPI(      # Now, creating the FastAPI Server
    title = "SQL Analytics Agent",
    description = "Natural language to SQL for any SQLite database",
    version = "2.0.0",
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

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

if os.path.exists(FRONTEND_DIR):    # check if folder exists
    app.mount(      # Everything inside frontend, make them available.
        "/static",
        StaticFiles(directory = FRONTEND_DIR),
        name = "static",
    )

executor = ThreadPoolExecutor(max_workers=2)

# Application state
_state = {
    "active_db_path": None,
    "active_db_name": "food_delivery.db",
    "schema": None,
    "sample_questions": [],
    "query_history": [],
}

# Now, creating the Pydantic Models
class QuestionRequest(BaseModel):       # This class describes the incoming JSON. So that, FastAPI understand what the request does sender is sending(is it string or Number, etc)
    question: str

class AnswerResponse(BaseModel):
    answer: str
    sql: str
    success: bool
    question: str
    history_id: int

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
    return {"message": "QueryPilot API running"}     # And, if file doesn't exists, do this.

# 2. health endpoint
@app.get("/health")     # GET --> /health --> Run health_check()
async def health_check():
    return {
        "status": "healthy",
        "database": _state["active_db_name"],
        "schema_loaded": _state["schema"] is not None,
    }

# 3. database information
@app.get("/db-info")
async def db_info():
    """Returns current database schema information."""
    db_path = _state["active_db_name"] or get_db_path()

    schema = inspect_schema(db_path)

    tables_summary = {}
    for table_name, info in schema["tables"].items():
        tables_summary[table_name] = {
            "row_count": info["row_count"],
            "columns": [col["name"] for col in info["columns"]],
            "primary_keys": info["primary_keys"],
            "foreign_keys": [
                f"{fk['from_column']} → "
                f"{fk['to_table']}.{fk['to_column']}"
                for fk in info["foreign_keys"]
            ]
        }

    return {
        "database": _state["active_db_name"],
        "tables": tables_summary,
        "relationships": schema["relationships"],
    }

# 4. Post endpoint
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

@app.post("/upload-db")
async def upload_database(file: UploadFile = File(...)):
    """
    Accepts a SQLite database file upload.
    Validates magic bytes, saves securely, inspects schema.
    """
    # Validate filename
    if not file.filename:
        raise HTTPException(
            status_code=400, detail="No filename provided"
        )

    # Read file content
    file_bytes = await file.read()

    # Validate SQLite magic bytes
    is_valid, reason = validate_sqlite_file(file_bytes)
    if not is_valid:
        raise HTTPException(status_code=400, detail=reason)

    # Save to uploads directory
    safe_filename = os.path.basename(file.filename)
    save_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(save_path, "wb") as f:
        f.write(file_bytes)

    # Verify it is actually queryable
    try:
        conn = sqlite3.connect(save_path)
        conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        conn.close()
    except Exception:
        os.remove(save_path)
        raise HTTPException(
            status_code=400,
            detail="File could not be opened as a SQLite database"
        )

    # Inspect schema
    schema = inspect_schema(save_path)

    if not schema["tables"]:
        os.remove(save_path)
        raise HTTPException(
            status_code=400,
            detail="Database contains no tables"
        )

    # Update application state
    _state["active_db_path"] = save_path
    _state["active_db_name"] = safe_filename
    _state["schema"] = schema
    _state["query_history"] = []

    # Generate sample questions in background
    loop = asyncio.get_event_loop()

    # Function to generate the questions
    def generate_questions():
        try:
            llm = get_llm
            questions = generate_sample_questions(schema, llm)
            _state["sample_questions"] = questions
        except Exception as e:
            print(f"[Warning] Could not generate questions: {e}")
            _state["sample_questions"] = []

    loop.run_in_executor(executor, generate_questions)

    tables_info = {
        name: info["row_count"]
        for name, info in schema["tables"].items()
    }

    return {
        "success": True,
        "filename": safe_filename,
        "tables": tables_info,
        "relationships": schema["relationships"],
        "message": (
            f"Database loaded successfully. "
            f"{len(schema['tables'])} tables found. "
            f"Generating sample questions..."
        )
    }

@app.post("/ask", response_model = AnswerResponse)
async def ask_endpoint(request: QuestionRequest):       # request gets the Question stored in the QuestionRequest object created automatically by the FastAPI.

    # step 1 - Validate question
    is_valid, reason = sanitize_question(request.question)
    if not is_valid:
        raise HTTPException(status_code=400, detail=reason)     # request invalid / user made mistake.

    db_path = _state["active_db_path"] or get_db_path()

    loop = asyncio.get_event_loop()

    # step 2 - Run agent
    result = await loop.run_in_executor(
        executor,
        lambda: ask_agent(request.question, db_path)
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Agent failed")
        )

    # Save to history
    history_entry = {
        "id": len(_state["query_history"]),
        "question": request.question,
        "answer": result["answer"],
        "sql": result.get("sql", ""),
        "raw_result": result.get("raw_result", ""),
    }

    _state["query_history"].append(history_entry)

    return AnswerResponse(      # Final return 
        answer=result["answer"],
        sql=result.get("sql", ""),
        success=result["success"],
        question=request.question,
        history_id=history_entry["id"],
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

# 4. Sample Question Endpoint
@app.get("/sample-questions")
async def sample_questions():
    """
    Returns schema-aware sample questions.
    Falls back to defaults for food delivery DB.
    """
    if _state["sample_questions"]:
        return {"questions": _state["sample_questions"]}

    # Default questions for food delivery database
    return {
        "questions": [
            "How many orders were placed in total?",
            "Which restaurant has the highest rating?",
            "What is the most popular cuisine type by number of orders?",
            "Which customer has spent the most money overall?",
            "What percentage of orders were cancelled?",
            "Which city has the most orders?",
            "What is the average order value?",
            "Which delivery agent completed the most orders?",
            "What are the top 5 most expensive menu items?",
            "How many customers are registered in Mumbai?",
        ]
    }

@app.get("/history")
async def get_history():
    """Returns all queries made in the current session."""
    return {
        "history": list(reversed(_state["query_history"])),
        "count": len(_state["query_history"]),
    }

@app.get("/export/{history_id}")
async def export_csv(history_id: int):
    """
    Exports the raw result of a specific query as CSV.
    """
    history = _state["query_history"]

    if history_id >= len(history) or history_id < 0:
        raise HTTPException(
            status_code=404, detail="Query not found in history"
        )

    entry = history[history_id]
    raw_result = entry.get("raw_result", "")

    if not raw_result:
        raise HTTPException(
            status_code=400,
            detail="No data available to export"
        )

    try:
        # Re-run the query to get structured data
        db_path = _state["active_db_path"] or get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(entry["sql"])

        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()

        # Write CSV to memory
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        writer.writerows(rows)
        output.seek(0)

        filename = (
            f"querypilot_export_{history_id}.csv"
        )

        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={
                "Content-Disposition":
                    f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Export failed: {str(e)}"
        )

@app.delete("/reset")
async def reset():
    # If reset, move to default food delivery database
    _state["active_db_path"] = None
    _state["active_db_name"] = "food_delivery.db"
    _state["schema"] = None
    _state["sample_questions"] = []
    _state["query_history"] = []
    return {"success": True, "message": "Reset to default database"}

if __name__ == "__main__":
    print("[Startup] Verifying database connection...")
    verify_connection()
    print("[Startup] Database OK. Starting server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )