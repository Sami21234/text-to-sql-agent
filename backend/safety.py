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

    # Must start with SELECT or WITH for read-only queries
    if not sql_upper.strip().startswith(("SELECT", "WITH")):
        return False, ( f"Unsafe SQL detected: Query must start with SELECT or WITH for read-only operations. " f"Got: {sql[:50]}")     

    # Check for forbidden keywords in the SQL query
    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(r'\b' + re.escape(keyword) + r'\b', sql_upper):
            return False, f"Unsafe SQL detected: '{keyword}' operation is not allowed."
    
    # Check for forbidden keywords
    for keyword in FORBIDDEN_KEYWORDS:      
        # Use word boundary to avoid matching substrings
        pattern = r'\b' + keyword + r'\b'
        if re.search(pattern, sql_upper):
            return False, (
                f"Forbidden keyword detected: {keyword}"
            ) 
        
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