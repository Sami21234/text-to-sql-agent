
import os
import re
from langchain_community.utilities import SQLDatabase
from langchain_ollama import OllamaLLM
from langchain_groq import ChatGroq
from database import get_db_path, verify_connection
from safety import is_safe_query
from dotenv import load_dotenv

load_dotenv()
USE_GROQ = os.getenv("USE_GROQ", "false").lower() == "true"

# Global instances — expensive to recreate on every request
_db = None


def get_db():
    global _db
    if _db is None:
        db_path = get_db_path()
        db_uri = f"sqlite:///{db_path}"
        _db = SQLDatabase.from_uri(
            db_uri,
            include_tables=[
                "users",
                "restaurants",
                "menu_items",
                "orders",
                "order_items",
            ],
            sample_rows_in_table_info=3,
        )
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
        sql = statements[0]

    return sql.strip()


def ask_agent(question: str) -> dict:
    """
    Sends question to SQL agent using direct DB query approach.
    More reliable than create_sql_agent for Mistral.
    """
    try:
        db = get_db()
        llm = get_llm()

        # Get database schema info
        table_info = db.get_table_info()

        # Build a direct prompt that asks for SQL only
        prompt = f"""You are a SQLite expert. Given a question about a food delivery database, write a single SQLite SELECT query to answer it.

DATABASE SCHEMA:
{table_info}

RULES:
- Write ONLY the SQL query, nothing else
- No markdown, no backticks, no explanation
- Use SQLite syntax only
- Status values are UPPERCASE: 'DELIVERED', 'CANCELLED', 'PLACED', 'IN_PROGRESS'
- "How many" questions use COUNT(*) not SUM()
- SUM() is only for money amounts like revenue or total spending
- For cuisine type queries join orders to restaurants using restaurant_id directly
- Do not reference orders.item_id — that column does not exist
- JOIN with users table when the answer needs customer names
- Use strftime() for date functions, never MONTH() or YEAR()
- Write exactly ONE SELECT statement, nothing else
- Always prefix column names with their table name when joining tables
- Write restaurants.name not just name when joining with menu_items
- Write menu_items.name not just name when joining with restaurants
- Write users.name not just name in any query involving joins
- To find average order value by cuisine type, join orders to restaurants only using restaurant_id
- Do not join menu_items or order_items when the question is about order totals
- order_items is only needed when the question asks about specific dishes or menu items

FOOD DELIVERY SCHEMA RELATIONSHIPS:
- orders.customer_id → users.user_id
- orders.restaurant_id → restaurants.restaurant_id
- orders.agent_id → users.user_id
- order_items.order_id → orders.order_id
- order_items.item_id → menu_items.item_id
- menu_items.restaurant_id → restaurants.restaurant_id

QUESTION: {question}

SQL QUERY (raw SQL only, no formatting):"""

        # Get SQL from LLM
        sql_response = llm.invoke(prompt)

        # Clean any markdown formatting
        sql = clean_sql(str(sql_response))

        # Safety check:
        is_safe, reason = is_safe_query(sql)
        if not is_safe:
            return {
                "answer": "I cannot execute that type of query for security resons.",
                "sql": sql,
                "success": False,
                "error": f"Safety check failed: {reason}",
            }

        print(f"\n[Agent] Generated SQL: {sql}")

        # Execute the query
        result = db.run(sql)

        print(f"[Agent] Query result: {result}")

        # Now ask LLM to format the answer
        answer_prompt = f"""Question: {question}

SQL Query used: {sql}

Query Result: {result}

Based on the query result above, provide a clear, concise answer to the question.
Do not mention SQL or technical details. Just answer the question naturally."""

        answer = llm.invoke(answer_prompt)

        return {
            "answer": str(answer),
            "sql": sql,
            "success": True,
            "error": None,
        }

    except Exception as e:
        return {
            "answer": "I could not answer that question. Please try rephrasing it.",
            "sql": "",
            "success": False,
            "error": str(e),
        }


if __name__ == "__main__":
    verify_connection()

    test_questions = [
        "How many orders were placed in total?",
        "Which restaurant has the highest rating?",
        "What is the most popular cuisine type by number of orders?",
        "Which customer has spent the most money overall?",
        "What percentage of orders were cancelled?",
    ]

    print("\n" + "="*60)
    print("SQL AGENT TEST")
    print("="*60)

    for question in test_questions:
        print(f"\nQuestion: {question}")
        print("-" * 40)
        result = ask_agent(question)
        print(f"SQL: {result.get('sql', 'N/A')}")
        print(f"Answer: {result['answer']}")
        print("-" * 40)