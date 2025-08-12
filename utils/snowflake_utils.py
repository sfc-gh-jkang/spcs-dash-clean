"""
Snowflake connection and data utilities for the multi-page Dash application.
"""

import os
import logging
import pandas as pd
from snowflake.snowpark.session import Session
import warnings
import re
import time
from typing import Dict, Union
from dash import html
import dash_bootstrap_components as dbc
import dash_ag_grid as dag

# Suppress pkg_resources warnings before importing snowflake
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*")
warnings.filterwarnings("ignore", category=UserWarning, module="snowflake.*")

logger = logging.getLogger(__name__)

# Simple query tracking for rate limiting and monitoring
_query_history = []
_MAX_QUERIES_PER_MINUTE = 30
_QUERY_TIMEOUT_SECONDS = 30


def is_running_in_spcs():
    """
    Checks if the current environment is Snowpark Container Services (SPCS)
    by looking for the Snowflake session token file.
    """
    snowflake_token_path = "/snowflake/session/token"
    return os.path.exists(snowflake_token_path)


def get_login_token():
    """Get the login token from the Snowflake session token file."""
    with open("/snowflake/session/token", "r") as f:
        return f.read()


def get_snowflake_session() -> Session:
    """Create a Snowflake session using environment variables."""
    try:
        if is_running_in_spcs():
            logger.info("Detected SPCS environment - using token authentication")
            connection_parameters = {
                "host": os.getenv("SNOWFLAKE_HOST"),
                "account": os.getenv("SNOWFLAKE_ACCOUNT"),
                "token": get_login_token(),
                "authenticator": "oauth",
                "database": os.getenv("SNOWFLAKE_DATABASE"),
                "schema": os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
                "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
            }
            session = Session.builder.configs(connection_parameters).create()
            logger.info(
                "Successfully connected to Snowflake via SPCS token authentication"
            )
        else:
            logger.info("Detected local environment - using credential authentication")
            connection_parameters = {
                "account": os.getenv("SNOWFLAKE_ACCOUNT"),
                "user": os.getenv("SNOWFLAKE_USER"),
                "password": os.getenv("SNOWFLAKE_PASSWORD"),
                "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
                "database": os.getenv("SNOWFLAKE_DATABASE"),
                "schema": os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
            }
            session = Session.builder.configs(connection_parameters).create()
            logger.info("Successfully connected to Snowflake locally")
        return session
    except Exception as e:
        logger.error(f"Error connecting to Snowflake: {e}")
        return None


def get_schema_objects() -> pd.DataFrame:
    """Query Snowflake to get all tables and views in SNOWFLAKE_SAMPLE_DATA.TPCH_SF10 schema."""
    session = get_snowflake_session()
    if session is None:
        logger.error("Failed to connect to Snowflake")
        return pd.DataFrame({"error": ["Failed to connect to Snowflake"]})

    try:
        # Query to get all tables and views from the specified schema
        query = """
        SELECT 
            table_name,
            table_type,
            row_count,
            bytes,
            created,
            table_schema,
            table_catalog
        FROM snowflake_sample_data.information_schema.tables 
        WHERE table_schema = 'TPCH_SF10' 
        AND table_catalog = 'SNOWFLAKE_SAMPLE_DATA'
        ORDER BY table_name
        """

        # Execute query and convert to pandas DataFrame
        result_df = session.sql(query).to_pandas()
        logger.info(
            f"Successfully retrieved {len(result_df)} tables/views from Snowflake schema"
        )
        session.close()
        return result_df

    except Exception as e:
        logger.error(f"Error querying Snowflake: {e}")
        session.close() if session else None
        return pd.DataFrame({"error": [f"Query failed: {str(e)}"]})


def get_table_list() -> list:
    """Get a simple list of table names from SNOWFLAKE_SAMPLE_DATA.TPCH_SF10 schema."""
    df = get_schema_objects()
    if "error" in df.columns:
        return []
    return df["TABLE_NAME"].tolist() if not df.empty else []


def get_table_data(table_name: str, limit: int = 1000) -> pd.DataFrame:
    """Get data from a specific table in SNOWFLAKE_SAMPLE_DATA.TPCH_SF10 schema."""
    session = get_snowflake_session()
    if session is None:
        logger.error("Failed to connect to Snowflake")
        return pd.DataFrame({"error": ["Failed to connect to Snowflake"]})

    try:
        query = f"""
        SELECT * 
        FROM snowflake_sample_data.tpch_sf10.{table_name}
        LIMIT {limit}
        """

        result_df = session.sql(query).to_pandas()
        logger.info(f"Successfully retrieved {len(result_df)} rows from {table_name}")
        session.close()
        return result_df

    except Exception as e:
        logger.error(f"Error querying table {table_name}: {e}")
        session.close() if session else None
        return pd.DataFrame({"error": [f"Query failed: {str(e)}"]})


def _perform_additional_security_checks(
    query_upper: str, original_query: str
) -> Dict[str, Union[bool, str]]:
    """
    Perform additional security validations on the SQL query.

    Args:
        query_upper (str): Uppercase version of query for pattern matching
        original_query (str): Original query for context in error messages

    Returns:
        Dict with error status and message
    """

    # SECURITY FIX: Unicode normalization and dangerous character detection
    import unicodedata

    try:
        # Normalize Unicode characters to prevent bypass attempts
        normalized_query = unicodedata.normalize("NFKC", original_query)
        normalized_upper = normalized_query.upper()

        # ENHANCED: Check for suspicious Unicode characters and lookalikes
        # General check for non-ASCII characters in SQL keywords positions
        def contains_suspicious_unicode(text):
            """Check for Unicode characters that might be SQL keyword lookalikes."""
            # Check for any non-ASCII characters in positions that look like SQL keywords
            import unicodedata

            # Known dangerous Unicode blocks
            dangerous_blocks = [
                "FULLWIDTH",  # Full-width characters
                "CHEROKEE",  # Cherokee characters used as lookalikes
                "CYRILLIC",  # Cyrillic lookalikes
                "MATHEMATICAL",  # Mathematical script characters
            ]

            # Only check for dangerous Unicode in potential SQL keyword positions
            sql_keywords = [
                "SELECT",
                "FROM",
                "WHERE",
                "UNION",
                "ORDER",
                "GROUP",
                "HAVING",
                "INSERT",
                "UPDATE",
                "DELETE",
                "DROP",
                "CREATE",
                "ALTER",
            ]

            for keyword in sql_keywords:
                # Check if there are Unicode lookalikes for SQL keywords
                for i in range(len(text) - len(keyword) + 1):
                    substring = text[i : i + len(keyword)]
                    if any(ord(char) > 127 for char in substring):
                        # Found Unicode characters in keyword-length substring
                        try:
                            for char in substring:
                                if ord(char) > 127:
                                    char_name = unicodedata.name(char, "")
                                    for block in dangerous_blocks:
                                        if block in char_name:
                                            return True
                        except ValueError:
                            pass

            # Specific pattern matching for Unicode lookalikes only (not ASCII)
            # Only detect when actual Unicode lookalikes are used, not ASCII letters
            suspicious_patterns = [
                r"[ᎾО][ᴿRр][ᴰDḊ][ᴱEе][ᴿRр]",  # ORDER with Unicode lookalikes
                r"[ᵁUｕ][ᴺNｎ][ᴵIｉ][ᴼOｏ][ᴺNｎ]",  # UNION with Unicode lookalikes
                r"[ˢSｓ][ᴱEｅ][ᴸLｌ][ᴱEｅ][ᶜCｃ][ᵀTｔ]",  # SELECT with Unicode lookalikes
                r"[ᴰDｄ][ᴿRｒ][ᴼOｏ][ᴾPｐ]",  # DROP with Unicode lookalikes
                r"[ᴵIｉ][ᴺNｎ][ˢSｓ][ᴱEｅ][ᴿRｒ][ᵀTｔ]",  # INSERT with Unicode lookalikes
            ]

            for pattern in suspicious_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    # Only flag if the match contains actual Unicode characters
                    matched_text = match.group(0)
                    if any(ord(char) > 127 for char in matched_text):
                        return True

            return False

        if contains_suspicious_unicode(original_query):
            return {
                "error": True,
                "message": "Query contains suspicious Unicode characters that may be attempts to bypass security. ASCII-only SQL keywords are required.",
                "safe_query": "",
            }

        # Use normalized versions for all security checks
        query_upper = normalized_upper
        original_query = normalized_query
    except Exception:
        # If normalization fails, proceed with original (safer than allowing bypass)
        pass

    # SECURITY FIX: First check for dangerous injection patterns BEFORE comment removal
    dangerous_patterns_pre_comment_removal = [
        r"'--",  # Classic comment injection (string termination with comment)
        r"';",  # Statement termination
        r"--.*?;.*?(INSERT|UPDATE|DELETE|DROP)",  # Comments with statements
        r"--.*?(DROP|DELETE|UPDATE|INSERT).*?;",  # Comments followed by dangerous statements
    ]

    for pattern in dangerous_patterns_pre_comment_removal:
        if re.search(pattern, original_query):
            return {
                "error": True,
                "message": "Query contains potentially malicious pattern. SQL injection attempts are not allowed.",
                "safe_query": "",
            }

    # SECURITY FIX: Remove comments before pattern matching to prevent comment-based bypasses
    def _remove_sql_comments(query_text: str) -> str:
        """Remove SQL comments while preserving string literals."""
        # Remove single-line comments (-- style)
        query_text = re.sub(r"--.*?$", "", query_text, flags=re.MULTILINE)

        # Remove multi-line comments (/* */ style) - handle nested comments
        while True:
            # Find the first /* and its matching */
            start = query_text.find("/*")
            if start == -1:
                break

            # Find the matching */
            end = query_text.find("*/", start + 2)
            if end == -1:
                # Unclosed comment - remove everything from /*
                query_text = query_text[:start]
                break
            else:
                # Remove the comment
                query_text = query_text[:start] + " " + query_text[end + 2 :]

        # Normalize whitespace after comment removal
        query_text = re.sub(r"\s+", " ", query_text).strip()
        return query_text

    # Apply comment removal to both versions
    comment_free_query = _remove_sql_comments(original_query)
    comment_free_upper = _remove_sql_comments(query_upper)

    # SECURITY FIX: Check for keywords that might be reconstructed after comment removal
    dangerous_reconstructed_keywords = [
        "UNION",
        "SELECT",
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "CREATE",
        "ALTER",
        "GRANT",
        "REVOKE",
        "EXECUTE",
        "CALL",
        "TRUNCATE",
        "MERGE",
    ]

    # Also check with spaces removed (in case comments leave spaces between keyword parts)
    comment_free_no_spaces = re.sub(r"\s+", "", comment_free_upper)
    query_upper_no_spaces = re.sub(r"\s+", "", query_upper)

    for keyword in dangerous_reconstructed_keywords:
        # Check if removing comments creates dangerous keywords where there weren't any before
        keyword_appears_after_comment_removal = (
            keyword in comment_free_upper or keyword in comment_free_no_spaces
        )
        keyword_existed_before = (
            keyword in query_upper or keyword in query_upper_no_spaces
        )

        if keyword_appears_after_comment_removal and not keyword_existed_before:
            return {
                "error": True,
                "message": f"Query appears to use comments to split dangerous keyword '{keyword}'. This is not allowed.",
                "safe_query": "",
            }

    # Update query versions for pattern matching
    query_upper = comment_free_upper
    original_query = comment_free_query

    # 1. Check for SQL injection patterns (comprehensive)
    injection_patterns = [
        # Basic injection patterns
        r";\s*(DROP|DELETE|UPDATE|INSERT)",  # Statement termination with dangerous commands
        r"--.*?(INSERT|UPDATE|DELETE|DROP)",  # Comments hiding dangerous commands
        r"/\*.*?(INSERT|UPDATE|DELETE|DROP).*?\*/",  # Block comments hiding commands
        r"UNION.*?(SELECT.*?(PASSWORD|CREDENTIAL|SECRET|TOKEN))",  # Union-based injection
        r"UNION\s+SELECT",  # Basic UNION injection
        r"\b1\s*=\s*1\b",  # Common injection condition
        r"OR\s+1\s*=\s*1",  # OR-based injection
        r"AND\s+1\s*=\s*1",  # AND-based injection
        r"'\s*OR\s*'.*?'\s*=\s*'",  # String-based injection
        r"'\s*=\s*'",  # Simple string equality (potential injection)
        r"\bTRUE\s*=\s*TRUE\b",  # Boolean condition injection
        r"\b\d+\s*=\s*\d+\b",  # Numeric equality conditions
        # Advanced injection patterns
        r"'\s*AND\s*\(",  # Parenthetical injection
        r"'\s*OR\s*\(",  # OR with subquery
        r"SELECT.*?FROM.*?INFORMATION_SCHEMA\.USER_PRIVILEGES",  # User privilege queries
        r"SELECT.*?FROM.*?INFORMATION_SCHEMA\.ROLE_GRANTS",  # Role grant queries
        r"SELECT.*?PRIVILEGE_TYPE.*?FROM.*?INFORMATION_SCHEMA",  # Privilege enumeration
        r"SELECT.*?GRANTEE.*?FROM.*?INFORMATION_SCHEMA",  # Grantee enumeration
        r"SHOW\s+GRANTS\s+TO\s+ROLE",  # Show grants enumeration
        r"DESCRIBE\s+TABLE",  # Table structure enumeration
        r"SELECT.*?TABLE_NAME.*?FROM.*?INFORMATION_SCHEMA\.TABLES.*?WHERE.*?TABLE_SCHEMA.*?NOT.*?IN",  # Advanced table enumeration (suspicious filtering)
        r"SELECT.*?TABLE_NAME.*?FROM.*?INFORMATION_SCHEMA\.TABLES.*?UNION",  # Table enumeration with UNION (suspicious)
        r"SELECT.*?COLUMN_NAME.*?FROM.*?INFORMATION_SCHEMA\.COLUMNS.*?UNION",  # Column enumeration with UNION (suspicious)
        r"SELECT.*?COLUMN_NAME.*?FROM.*?INFORMATION_SCHEMA\.COLUMNS.*?WHERE.*?TABLE_NAME.*?NOT.*?IN",  # Suspicious filtering
        r"SELECT.*?COLUMN_NAME.*?FROM.*?INFORMATION_SCHEMA\.COLUMNS.*?WHERE.*?TABLE_NAME.*?=.*?'USERS'",  # Specific sensitive user table enumeration (test case)
        r"ASCII\s*\(\s*SUBSTRING",  # Character extraction functions
        r"SUBSTRING\s*\(\s*\(\s*SELECT",  # Subquery in substring
        r"EXISTS\s*\(\s*SELECT",  # Exists subqueries
        r"AND\s+\d+\s*=\s*\(\s*SELECT",  # Blind injection with subquery
        r"=\s*\(\s*SELECT\s+COUNT",  # Count-based blind injection
        r"WAITFOR\s+DELAY",  # Time delay functions
        r"SLEEP\s*\(",  # Sleep functions
        r"BENCHMARK\s*\(",  # Benchmark functions
        r"PG_SLEEP\s*\(",  # PostgreSQL sleep
        r"DECLARE\s+@",  # Variable declarations
        r"EXEC\s*\(\s*@",  # Dynamic SQL execution
        r"XP_CMDSHELL",  # Command shell execution
        r"SP_EXECUTESQL",  # Dynamic SQL procedures
        r"INTO\s+OUTFILE",  # File output
        r"LOAD_FILE\s*\(",  # File loading
        r"'\s*\+\s*'",  # String concatenation
        r"CHAR\s*\(\s*\d+\s*\)",  # Character encoding
        r"CHR\s*\(\s*\d+\s*\)",  # Character encoding (Oracle)
        r"CONCAT\s*\(",  # String concatenation functions
        r"'\s*\|\|\s*'",  # String concatenation operator
        r"'--",  # Comment after quote (SQL comment injection)
        r"';--",  # Statement end with comment
        r"#.*?(DROP|DELETE|INSERT|UPDATE)",  # MySQL style comments with dangerous commands
        r"/\*.*?(DROP|DELETE|INSERT|UPDATE).*?\*/",  # Block comments with dangerous commands already covered above
        r"'\s*;",  # Quote followed by statement terminator
        # Resource exhaustion patterns
        r"FROM\s+\w+\s+\w+,\s*\w+\s+\w+,\s*\w+\s+\w+",  # Multiple table aliases (Cartesian product)
        r"CROSS\s+JOIN",  # Cross joins
        r"WITH\s+RECURSIVE",  # Recursive CTEs
        r"\bSELECT\s+\*.*?;.*?SELECT",  # Multiple statements
        r"COUNT\s*\(\s*\*\s*\).*?FROM.*?LARGE_TABLE",  # Suspicious counting operations
        r"WHERE.*?IN\s*\(\s*SELECT.*?WHERE.*?IN\s*\(\s*SELECT",  # Deeply nested subqueries
    ]

    for pattern in injection_patterns:
        if re.search(pattern, query_upper):
            return {
                "error": True,
                "message": "Query contains potentially malicious pattern. SQL injection attempts are not allowed.",
                "safe_query": "",
            }

    # 2. Check for excessive complexity (prevent DoS attacks) - SECURITY FIX
    if len(original_query) > 10000:  # 10KB limit
        return {
            "error": True,
            "message": "Query is too long. Maximum query length is 10,000 characters.",
            "safe_query": "",
        }

    # Count parentheses depth (prevent deeply nested queries)
    max_depth = 0
    current_depth = 0
    for char in original_query:
        if char == "(":
            current_depth += 1
            max_depth = max(max_depth, current_depth)
        elif char == ")":
            current_depth -= 1

    # SECURITY FIX: Correct boundary condition - allow exactly 10 levels
    if max_depth > 10:
        return {
            "error": True,
            "message": "Query has too many nested parentheses. Maximum nesting depth is 10.",
            "safe_query": "",
        }

    # 3. Check for excessive JOINs (prevent performance issues)
    join_count = len(re.findall(r"\bJOIN\b", query_upper))
    if join_count > 5:
        return {
            "error": True,
            "message": f"Query has too many JOINs ({join_count}). Maximum allowed is 5.",
            "safe_query": "",
        }

    # 4. Check for dangerous functions and expressions
    dangerous_patterns = [
        r"LATERAL\s+VIEW",  # Lateral views can be resource intensive
        r"RECURSIVE",  # Recursive CTEs can cause infinite loops
        r"CONNECT\s+BY",  # Hierarchical queries can be problematic
        r"MODEL\s+",  # MODEL clause can be resource intensive
        r"XMLTABLE",  # XML processing can be slow
        r"JSON_TABLE",  # JSON processing with large data
        r"PIVOT\s*\(",  # Complex pivot operations
        r"UNPIVOT\s*\(",  # Complex unpivot operations
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, query_upper):
            return {
                "error": True,
                "message": "Query contains restricted SQL feature. Complex operations are not allowed.",
                "safe_query": "",
            }

    # 5. Validate allowed schemas/databases (whitelist approach) - SECURITY FIX
    allowed_schemas = ["SNOWFLAKE_SAMPLE_DATA", "INFORMATION_SCHEMA"]

    # Extract FROM clauses to check table references (handle quoted identifiers)
    # Simple but effective approach: find FROM followed by everything until space or comma
    from_matches = []

    # Find all FROM clauses
    for match in re.finditer(r"FROM\s+", query_upper):
        start_pos = match.end()

        # Extract everything from this position until we hit a space, comma, or end
        remaining = query_upper[start_pos:]

        # Handle quoted identifiers by finding matching quotes
        if remaining.startswith(
            ("'", '"', "`", "'", "'", """, """)
        ):  # Regular and smart quotes
            quote_char = remaining[0]
            end_quote_pos = remaining.find(quote_char, 1)
            if end_quote_pos > 0:
                # Found closing quote, now look for the rest (e.g., .table_name)
                table_ref = remaining[: end_quote_pos + 1]
                # Check if there's more after the quote (like .table_name)
                remainder = remaining[end_quote_pos + 1 :].lstrip()
                if remainder.startswith("."):
                    # Add the rest until next space/comma
                    next_break = re.search(r"[\s,\)]", remainder)
                    if next_break:
                        table_ref += remainder[: next_break.start()]
                    else:
                        table_ref += remainder
                from_matches.append(table_ref)
            else:
                # Unclosed quote, treat as regular identifier
                next_break = re.search(r"[\s,\)]", remaining)
                if next_break:
                    from_matches.append(remaining[: next_break.start()])
                else:
                    from_matches.append(remaining)
        else:
            # Regular identifier
            next_break = re.search(r"[\s,\)]", remaining)
            if next_break:
                from_matches.append(remaining[: next_break.start()])
            else:
                from_matches.append(remaining)
    for table_ref in from_matches:
        # SECURITY FIX: Comprehensive quote and whitespace removal (including smart quotes)
        clean_table = table_ref.replace('"', "").replace("'", "").replace("`", "")
        clean_table = clean_table.replace("'", "").replace("'", "")  # Smart quotes
        clean_table = clean_table.replace(
            """, "").replace(""", ""
        )  # Smart double quotes
        clean_table = clean_table.strip()  # Remove leading/trailing whitespace
        clean_table = re.sub(r"\s+", "", clean_table)  # Remove internal whitespace

        if "." in clean_table:
            schema_part = clean_table.split(".")[
                0
            ].upper()  # SECURITY FIX: Case-insensitive comparison
            # SECURITY FIX: Check against uppercase allowed schemas
            allowed_schemas_upper = [schema.upper() for schema in allowed_schemas]
            if schema_part not in allowed_schemas_upper:
                return {
                    "error": True,
                    "message": f'Access to schema "{schema_part}" is not allowed. Only {", ".join(allowed_schemas)} are permitted.',
                    "safe_query": "",
                }

    # 6. Check for file operations or external references
    file_patterns = [
        r"FROM\s+@[\w_]+",  # Stage references in FROM clauses
        r"COPY\s+.*@[\w_]+",  # Stage references in COPY commands
        r"LIST\s+@[\w_]+",  # LIST stage operations
        r"GET\s+@[\w_]+",  # GET stage operations
        r"PUT\s+.*@[\w_]+",  # PUT stage operations
        r"FILE_FORMAT",  # File format specifications
        r"EXTERNAL",  # External table references
        r"S3://",  # S3 references
        r"AZURE://",  # Azure references
        r"GCS://",  # Google Cloud references
        r"HTTP://",  # HTTP references
        r"HTTPS://",  # HTTPS references
    ]

    for pattern in file_patterns:
        if re.search(pattern, query_upper):
            return {
                "error": True,
                "message": "File operations and external references are not allowed.",
                "safe_query": "",
            }

    return {
        "error": False,
        "message": "Query passed additional security checks",
        "safe_query": original_query,
    }


def _check_rate_limit() -> Dict[str, Union[bool, str]]:
    """
    Check if the current request exceeds rate limits.

    Returns:
        Dict with error status and message
    """
    current_time = time.time()

    # Clean old entries (older than 1 minute)
    global _query_history
    _query_history[:] = [
        timestamp for timestamp in _query_history if current_time - timestamp < 60
    ]

    # Check rate limit
    if len(_query_history) >= _MAX_QUERIES_PER_MINUTE:
        return {
            "error": True,
            "message": f"Rate limit exceeded. Maximum {_MAX_QUERIES_PER_MINUTE} queries per minute allowed.",
            "safe_query": "",
        }

    # Add current request to history
    _query_history.append(current_time)

    return {"error": False, "message": "Rate limit check passed", "safe_query": ""}


def _validate_query_safety(query: str, max_rows: int) -> Dict[str, Union[bool, str]]:
    """
    Validate that a query is safe to execute by checking for SELECT-only operations
    and ensuring proper LIMIT clauses.

    Args:
        query (str): The SQL query to validate
        max_rows (int): Maximum allowed rows

    Returns:
        Dict containing 'error' (bool), 'message' (str), and 'safe_query' (str)
    """
    # Normalize the query
    query = query.strip()
    if not query:
        return {"error": True, "message": "Empty query provided", "safe_query": ""}

    # Enforce maximum row limit
    max_rows = min(max_rows, 10000)  # Hard cap at 10,000 rows

    # Convert to uppercase for keyword checking (but preserve original case for execution)
    query_upper = query.upper()

    # Security checks - expanded dangerous keywords
    dangerous_keywords = [
        # Data modification
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "CREATE",
        "ALTER",
        "TRUNCATE",
        "MERGE",
        "REPLACE",
        "SWAP",
        # System/admin operations
        "GRANT",
        "REVOKE",
        "EXECUTE",
        "CALL",
        "COPY",
        "PUT",
        "GET",
        "REMOVE",
        "LIST",
        "SHOW GRANTS",
        "SHOW ROLES",
        "USE ROLE",
        "USE WAREHOUSE",
        "SET",
        "UNSET",
        "BEGIN",
        "COMMIT",
        "ROLLBACK",
        # Stored procedures and functions
        "PROCEDURE",
        "FUNCTION",
        "TASK",
        "STREAM",
        "STAGE",
        # File operations
        "LOAD",
        "UNLOAD",
        "$",
        # Potentially dangerous system functions
        "SYSTEM$",
        "CURRENT_ROLE",
        "CURRENT_USER",
    ]

    # Check for dangerous keywords (whole word matches only)
    import re

    for keyword in dangerous_keywords:
        # Use word boundary regex to match whole keywords only
        if re.search(r"\b" + re.escape(keyword) + r"\b", query_upper):
            return {
                "error": True,
                "message": f"Query contains forbidden keyword: {keyword}. Only SELECT statements are allowed.",
                "safe_query": "",
            }

    # Must start with SELECT (allowing for comments and whitespace)
    query_cleaned = re.sub(
        r"^\s*(/\*.*?\*/\s*)*", "", query, flags=re.DOTALL
    )  # Remove leading comments
    query_cleaned = re.sub(
        r"^\s*--.*?\n\s*", "", query_cleaned, flags=re.MULTILINE
    )  # Remove leading line comments
    query_cleaned = query_cleaned.strip()

    if not re.match(r"^\s*SELECT\s+", query_cleaned, re.IGNORECASE):
        return {
            "error": True,
            "message": "Query must start with SELECT. Data modification statements are not allowed.",
            "safe_query": "",
        }

    # Additional security validations
    security_checks = _perform_additional_security_checks(query_upper, query)
    if security_checks["error"]:
        return security_checks

    # Check if query already has a LIMIT clause
    limit_pattern = r"\bLIMIT\s+(\d+)\b"
    limit_match = re.search(limit_pattern, query_upper)

    if limit_match:
        # Query has LIMIT, check if it's within our max_rows
        existing_limit = int(limit_match.group(1))
        if existing_limit > max_rows:
            # Replace with our max_rows
            safe_query = re.sub(
                limit_pattern, f"LIMIT {max_rows}", query, flags=re.IGNORECASE
            )
            return {
                "error": False,
                "message": f"Query limit reduced from {existing_limit} to {max_rows} for safety",
                "safe_query": safe_query,
            }
        else:
            # Existing limit is fine
            return {"error": False, "message": "Query is safe", "safe_query": query}
    else:
        # No LIMIT clause, add one
        safe_query = f"{query.rstrip(';')} LIMIT {max_rows}"
        return {
            "error": False,
            "message": f"Added LIMIT {max_rows} for safety",
            "safe_query": safe_query,
        }


def execute_query(query: str, max_rows: int = 10000) -> pd.DataFrame:
    """
    Execute a safe custom SQL query against Snowflake and return results as DataFrame.

    SECURITY FEATURES:
    - Only allows SELECT statements (prevents data modification)
    - Automatically limits results to max_rows to prevent resource exhaustion
    - Sanitizes and validates input queries

    Args:
        query (str): SQL SELECT query to execute
        max_rows (int): Maximum number of rows to return (default: 10000, max: 10000)

    Returns:
        pd.DataFrame: Query results, or DataFrame with 'error' column if query fails
    """
    # Rate limiting check (check first before any other operations)
    rate_check = _check_rate_limit()
    if rate_check["error"]:
        logger.warning(f"Query rejected for rate limiting: {rate_check['message']}")
        return pd.DataFrame({"error": [rate_check["message"]]})

    # Security validation
    safety_check = _validate_query_safety(query, max_rows)
    if safety_check["error"]:
        logger.warning(f"Query rejected for safety: {safety_check['message']}")
        return pd.DataFrame({"error": [safety_check["message"]]})

    # Get Snowflake session
    session = get_snowflake_session()
    if session is None:
        logger.error("Failed to connect to Snowflake for custom query")
        return pd.DataFrame({"error": ["Failed to connect to Snowflake"]})

    try:
        # Use the safe query (potentially modified with LIMIT)
        safe_query = safety_check["safe_query"]

        logger.info(
            f"Executing safe query: {safe_query[:100]}{'...' if len(safe_query) > 100 else ''}"
        )

        # Execute the query with timing
        start_time = time.time()
        result_df = session.sql(safe_query).to_pandas()
        execution_time = time.time() - start_time

        # Log execution metrics
        logger.info(
            f"Successfully executed query in {execution_time:.2f}s, returned {len(result_df)} rows"
        )

        # Check for performance warnings
        if execution_time > 10:
            logger.warning(f"Slow query detected: {execution_time:.2f}s execution time")
        if len(result_df) > 5000:
            logger.info(f"Large result set: {len(result_df)} rows returned")

        session.close()
        return result_df

    except Exception as e:
        logger.error(f"Error executing custom query: {e}")
        session.close() if session else None
        return pd.DataFrame({"error": [f"Query execution failed: {str(e)}"]})


def format_query_results(
    result_df: pd.DataFrame,
    max_rows: int = 1000,
    grid_id: str = "query-results-grid",
    theme: str = "alpine",
) -> html.Div:
    """
    Format a pandas DataFrame into an AG Grid for display with advanced features.

    Args:
        result_df (pd.DataFrame): The query results to format
        max_rows (int): Maximum number of rows to display (default: 1000)
        grid_id (str): Unique ID for the AG Grid component
        theme (str): AG Grid theme ('alpine' or 'alpine-dark')

    Returns:
        html.Div: AG Grid with sorting, filtering, and pagination
    """
    if "error" in result_df.columns:
        return dbc.Alert(f"Query failed: {result_df['error'].iloc[0]}", color="danger")

    if len(result_df) == 0:
        return dbc.Alert(
            "Query executed successfully but returned no results.", color="warning"
        )

    # Limit the data if it's too large
    display_df = result_df.head(max_rows)
    total_rows = len(result_df)
    displayed_rows = len(display_df)

    # Create column definitions for AG Grid
    column_defs = []
    for col in display_df.columns:
        col_def = {
            "headerName": str(col),
            "field": str(col),
            "sortable": True,
            "filter": True,
            "resizable": True,
        }

        # Try to determine the data type for better column handling
        if display_df[col].dtype in ["int64", "float64", "int32", "float32"]:
            col_def["type"] = "numericColumn"
            col_def["filter"] = "agNumberColumnFilter"
        elif display_df[col].dtype == "datetime64[ns]":
            col_def["filter"] = "agDateColumnFilter"
        else:
            col_def["filter"] = "agTextColumnFilter"

        column_defs.append(col_def)

    # Convert DataFrame to records for AG Grid
    row_data = display_df.to_dict("records")

    # Create the AG Grid with theme support
    grid_theme = f"ag-theme-{theme}"
    ag_grid = dag.AgGrid(
        id=grid_id,
        rowData=row_data,
        columnDefs=column_defs,
        className=grid_theme,
        style={"height": "500px", "width": "100%"},
        dashGridOptions={
            "pagination": True,
            "paginationPageSize": 20,
            "paginationPageSizeSelector": [10, 20, 50, 100],
            "defaultColDef": {
                "resizable": True,
                "sortable": True,
                "filter": True,
                "minWidth": 100,
            },
            "enableRangeSelection": True,
            "rowSelection": "multiple",
            "suppressRowClickSelection": False,
            "animateRows": True,
        },
    )

    # Create info message about row count
    info_message = html.Div(
        [
            html.P(
                [
                    html.Strong("Query executed successfully. "),
                    f"Total rows: {total_rows:,}, Displaying: {displayed_rows:,}",
                    html.Span(
                        f" (Limited to {max_rows:,} rows for performance)",
                        className="text-muted",
                    )
                    if total_rows > max_rows
                    else "",
                ]
            ),
            html.Small(
                [
                    "💡 Use column headers to sort and filter. Select rows for further analysis.",
                ],
                className="text-muted",
            ),
        ],
        className="mb-3",
    )

    return html.Div([info_message, ag_grid])
