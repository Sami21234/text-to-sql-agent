
import os
import re
import sqlite3
from langchain_community.utilities import SQLDatabase
from langchain_ollama import OllamaLLM
from langchain_groq import ChatGroq
from database import get_db_path, verify_connection
from schema_inspector import inspect_schema, generate_prompt
from safety import is_safe_query
from dotenv import load_dotenv

load_dotenv()

USE_GROQ = os.getenv("USE_GROQ", "false").lower() == "true"

# Global instances — expensive to recreate on every request
_db = None
_current_db_path = None


def get_db(db_path: str = None):
    global _db, _current_db_path

    target_path = db_path or get_db_path()

    # Rebuildiing if path changed or not yet initialized
    if _db is None or target_path != _current_db_path:
        db_uri = f"sqlite:///{target_path}"     # it creates the URI.
        _db = SQLDatabase.from_uri(
            db_uri,
            sample_rows_in_table_info=2,        # Inspects 2 sample rows.
        )
        _current_db_path = target_path
    return _db


def get_llm(temperature: float = 0):     # Zero temperature means fully deterministic output. The same question always generates the same SQL.
    """
     Returns the appropriate LLM based on environment.
     temperature=0 is critical for deterministic SQL generation.

    """
    if USE_GROQ:
        return ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=temperature,
        )
    return OllamaLLM(
        model="mistral",
        temperature=temperature,
        num_ctx=4096,   # Sets the size of the context window used to generate the next token
    )


def clean_sql(sql: str) -> str:
    """
    Removes markdown formatting and ensures single statement.
    """
    # Remove ```sql ... ``` blocks
    sql = re.sub(r'```sql\s*', '', sql)
    sql = re.sub(r'```\s*', '', sql)
    sql = sql.strip()

    # Take only the first SQL statement
    # Split on semicolon and take first non-empty part
    statements = [s.strip() for s in sql.split(';') if s.strip()]
    if statements:
        sql = statements[0]     # Returns only the first statement, for security practice.

    return sql.strip()


def ask_agent(question: str, db_path: str = None) -> dict:
    """
    Two-step pipeline:
    1. Generate SQL from schema-aware prompt
    2. Format result as natural language answer
    """
    target_path = db_path or get_db_path()

    try:
        # Inspect schema for this specific database
        schema = inspect_schema(target_path)
        llm = get_llm()
        db = get_db(target_path)

        # Step 1: Generate SQL
        sql_prompt = generate_prompt(schema, question)
        sql_response = llm.invoke(sql_prompt)
        sql = clean_sql(str(sql_response))

        print(f"\n[Agent] Generated SQL: {sql}")

        # Safety check before execution
        sql_upper = sql.upper().strip()
        if not sql_upper.startswith("SELECT"):
            return {
                "answer": "I can only answer questions that require reading data.",
                "sql": sql,
                "raw_result": None,
                "success": False,
                "error": "Non-SELECT query blocked",
            }

        # Step 2: Execute query
        raw_result = db.run(sql)
        print(f"[Agent] Raw result: {raw_result}")

        # Step 3: Format answer
        answer_prompt = f"""You received this question: {question}

The SQL query that ran was: {sql}

The actual database returned this exact result: {raw_result}

Now write one or two clear sentences answering the question.
Use the actual values from the result above.
Do not use placeholders like [Department Name] or [Amount].
Do not say "the result shows" or "based on the query".
Just state the answer directly using the real numbers and names.

For example if the result was [('Engineering', 85000.0)] you would say:
The average salary in Engineering is $85,000.

Write a clear, concise answer to the question based on the result.
Do not mention SQL or technical details.
Just answer naturally in one or two sentences.

Answer:"""

        answer = llm.invoke(answer_prompt)    

        return {
            "answer": str(answer).strip(),
            "sql": sql,
            "raw_result": str(raw_result),
            "success": True,
            "error": None,
        }

    except Exception as e:
        return {
            "answer": "I could not answer that question. Try rephrasing it.",
            "sql": "",
            "raw_result": None,
            "success": False,
            "error": str(e),
        }


       