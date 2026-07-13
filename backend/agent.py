

import os
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_ollama import OllamaLLM
from langchain_groq import ChatGroq
from database import get_db_path, verify_connection
from safety import is_safe_query
from dotenv import load_dotenv

load_dotenv()
USE_GROQ = os.getenv("USE_GROQ", "false").lower() == "true"

# Global instances — expensive to recreate on every request
_db = None
_agent = None


def get_db():
    """Returns cached SQLDatabase connection."""
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


def get_llm(temperature: float = 0):
    """Returns LLM based on environment."""
    if USE_GROQ:
        return ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=temperature,
        )
    return OllamaLLM(
        model="mistral",
        temperature=temperature,
        num_ctx=4096,
    )


def build_agent():
    """
    Builds LangChain SQL agent.
    Uses cached DB connection.
    Creates fresh agent per call for stateless behavior.
    """
    db = get_db()
    llm = get_llm()

    prefix = """You are an agent designed to interact with a SQLite database
containing food delivery data.

Given an input question, create a syntactically correct SQLite query,
execute it, and return the answer.

STRICT RULES — follow these exactly:
1. Never wrap SQL in markdown code blocks or backticks
2. Always provide raw SQL directly as the Action Input — no formatting
3. Use SQLite syntax only — NOT MySQL syntax
4. For dates use strftime(), NOT MONTH() or YEAR() or DATE_SUB()
5. Status values are UPPERCASE: 'DELIVERED', 'CANCELLED', 'PLACED', 'IN_PROGRESS'
6. For total spending or revenue always use SUM(), not MAX()
7. Always JOIN with users table to get customer names, not just IDs
8. Limit results to 10 rows unless the question asks for more
9. If the question asks for a percentage, calculate it in SQL directly

Available tables: users, restaurants, menu_items, orders, order_items"""

    agent = create_sql_agent(
        llm=llm,
        db=db,
        agent_type="zero-shot-react-description",
        verbose=True,
        max_iterations=8,
        handle_parsing_errors=True,
        prefix=prefix,
    )

    return agent


def ask_agent(question: str) -> dict:
    """
    Sends a question to the SQL agent.
    Returns answer with success status.
    """
    try:
        agent = build_agent()
        result = agent.invoke({"input": question})
        answer = result.get("output", "No answer generated.")

        return {
            "answer": answer,
            "success": True,
            "error": None,
        }

    except Exception as e:
        error_msg = str(e)

        if "max_iterations" in error_msg.lower():
            return {
                "answer": (
                    "I could not answer this question. "
                    "Try rephrasing or asking something simpler."
                ),
                "success": False,
                "error": "max_iterations_exceeded",
            }

        return {
            "answer": "An error occurred while processing your question.",
            "success": False,
            "error": error_msg,
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
        print(f"Answer: {result['answer']}")
        print("-" * 40)