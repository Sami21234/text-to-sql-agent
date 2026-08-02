# This is the most important safety file in the backend. It contains all the safety checks and validations to ensure that the system operates within safe parameters.

import re       # Regular expression module for pattern matching

# SQL keywords that indicate destructive operations
FORBIDDEN_KEYWORDS = [
    "DROP", "DELETE", "ALTER", "TRUNCATE", "UPDATE", "INSERT", "CREATE", "REPLACE", "ATTACH", "DETACH", "VACUUM", "PRAGMA"
]

# Function to check if a SQL query is safe (read-only)
def is_safe_query(sql: str) -> tuple[bool, str]:
    """
    Validates that a SQL query is read-only.

    Returns:
        (True, "") if safe
        (False, reason) if unsafe
    """
    # Normalize the SQL query to whitespace and uppercase for consistent checking
    sql_upper = " ".join(sql.upper().split())   # Removing extra whitespace and converting to uppercase for uniformity

    # Allow CTEs that start with WITH ... SELECT
    if sql_upper.strip().startswith("WITH"):
        if "SELECT" not in sql_upper:
            return False, "Query must contain SELECT"
        # Check for forbidden keywords
        for keyword in FORBIDDEN_KEYWORDS:
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, sql_upper):
                return False, f"Forbidden keyword: {keyword}"
        return True, ""

    # Must start with SELECT or WITH for read-only queries
    if not sql_upper.strip().startswith("SELECT"):
        return False, f"Non-SELECT query blocked"   

    # Check for forbidden keywords in the SQL query
    for keyword in FORBIDDEN_KEYWORDS:
        pattern = r'\b' + keyword + r'\b'
        if re.search(pattern, sql_upper):
            return False, f"Forbidden keyword: {keyword}" 
        
    # Prevent multiple statements
    # Semicolon in middle of query = potential injection
    stripped = sql.strip().rstrip(";")  
    if ";" in stripped:
        return False, "Multiple SQL statements not allowed"
    return True, ""

def sanitize_question(question: str) -> tuple[bool, str]:
    """
    Basic check on user input before sending to agent.
    Prevents prompt injection attempts.
    """
    if len(question) > 500:
        return False, "Question too long. Maximum 500 characters."
    
    if len(question.strip()) < 3:       
        return False, "Question too short."

    # Check for obvious SQL injection in the question
    sql_injection_patterns = [
        r";\s*DROP",
        r";\s*DELETE",
        r"--",
        r"/\*.*\*/",
    ]

    for pattern in sql_injection_patterns:
        if re.search(pattern, question, re.IGNORECASE):
            return False, "Invalid characters in question."
        
    return True, ""