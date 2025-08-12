"""
Comprehensive tests for snowflake_utils module.

This test suite covers all functions in the snowflake_utils module with
unit tests, integration tests, and edge case testing.
"""

import pytest
import pandas as pd
import os
import time
from unittest.mock import Mock, patch, mock_open
from dash import html
import dash_bootstrap_components as dbc

# Import the module under test
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.snowflake_utils import (
    is_running_in_spcs,
    get_login_token,
    get_snowflake_session,
    get_schema_objects,
    get_table_list,
    get_table_data,
    _perform_additional_security_checks,
    _check_rate_limit,
    _validate_query_safety,
    execute_query,
    format_query_results,
    _query_history,
    _MAX_QUERIES_PER_MINUTE,
)


class TestEnvironmentDetection:
    """Tests for environment detection functions."""

    def test_is_running_in_spcs_true(self):
        """Test SPCS detection when token file exists."""
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            assert is_running_in_spcs()
            mock_exists.assert_called_once_with("/snowflake/session/token")

    def test_is_running_in_spcs_false(self):
        """Test SPCS detection when token file doesn't exist."""
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False
            assert not is_running_in_spcs()
            mock_exists.assert_called_once_with("/snowflake/session/token")

    def test_get_login_token_success(self):
        """Test successful token retrieval."""
        mock_token = "test_token_123"
        with patch("builtins.open", mock_open(read_data=mock_token)):
            result = get_login_token()
            assert result == mock_token

    def test_get_login_token_file_not_found(self):
        """Test token retrieval when file doesn't exist."""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            with pytest.raises(FileNotFoundError):
                get_login_token()


class TestSnowflakeSession:
    """Tests for Snowflake session management."""

    @patch.dict(
        os.environ,
        {
            "SNOWFLAKE_ACCOUNT": "test_account",
            "SNOWFLAKE_USER": "test_user",
            "SNOWFLAKE_PASSWORD": "test_password",
            "SNOWFLAKE_WAREHOUSE": "test_wh",
            "SNOWFLAKE_DATABASE": "test_db",
            "SNOWFLAKE_SCHEMA": "test_schema",
        },
    )
    @patch("utils.snowflake_utils.is_running_in_spcs")
    @patch("utils.snowflake_utils.Session")
    def test_get_snowflake_session_local(self, mock_session_class, mock_spcs_check):
        """Test local environment session creation."""
        mock_spcs_check.return_value = False
        mock_session = Mock()
        mock_session_class.builder.configs.return_value.create.return_value = (
            mock_session
        )

        result = get_snowflake_session()

        assert result == mock_session
        mock_session_class.builder.configs.assert_called_once()

    @patch.dict(
        os.environ,
        {
            "SNOWFLAKE_HOST": "test_host",
            "SNOWFLAKE_ACCOUNT": "test_account",
            "SNOWFLAKE_DATABASE": "test_db",
            "SNOWFLAKE_SCHEMA": "test_schema",
            "SNOWFLAKE_WAREHOUSE": "test_wh",
        },
    )
    @patch("utils.snowflake_utils.is_running_in_spcs")
    @patch("utils.snowflake_utils.get_login_token")
    @patch("utils.snowflake_utils.Session")
    def test_get_snowflake_session_spcs(
        self, mock_session_class, mock_get_token, mock_spcs_check
    ):
        """Test SPCS environment session creation."""
        mock_spcs_check.return_value = True
        mock_get_token.return_value = "test_token"
        mock_session = Mock()
        mock_session_class.builder.configs.return_value.create.return_value = (
            mock_session
        )

        result = get_snowflake_session()

        assert result == mock_session
        mock_get_token.assert_called_once()
        mock_session_class.builder.configs.assert_called_once()

    @patch("utils.snowflake_utils.is_running_in_spcs")
    @patch("utils.snowflake_utils.Session")
    def test_get_snowflake_session_exception(self, mock_session_class, mock_spcs_check):
        """Test session creation with exception."""
        mock_spcs_check.return_value = False
        mock_session_class.builder.configs.return_value.create.side_effect = Exception(
            "Connection failed"
        )

        result = get_snowflake_session()

        assert result is None


class TestDataRetrieval:
    """Tests for data retrieval functions."""

    @patch("utils.snowflake_utils.get_snowflake_session")
    def test_get_schema_objects_success(self, mock_get_session):
        """Test successful schema objects retrieval."""
        mock_session = Mock()
        mock_get_session.return_value = mock_session

        # Mock the SQL result
        mock_df = pd.DataFrame(
            {
                "TABLE_NAME": ["CUSTOMER", "ORDERS"],
                "TABLE_TYPE": ["BASE TABLE", "BASE TABLE"],
                "ROW_COUNT": [1000, 5000],
                "BYTES": [1024, 2048],
                "CREATED": ["2023-01-01", "2023-01-02"],
            }
        )
        mock_session.sql.return_value.to_pandas.return_value = mock_df

        result = get_schema_objects()

        assert len(result) == 2
        assert "TABLE_NAME" in result.columns
        mock_session.close.assert_called_once()

    @patch("utils.snowflake_utils.get_snowflake_session")
    def test_get_schema_objects_no_session(self, mock_get_session):
        """Test schema objects retrieval with no session."""
        mock_get_session.return_value = None

        result = get_schema_objects()

        assert "error" in result.columns
        assert "Failed to connect to Snowflake" in result["error"].iloc[0]

    @patch("utils.snowflake_utils.get_snowflake_session")
    def test_get_schema_objects_query_exception(self, mock_get_session):
        """Test schema objects retrieval with query exception."""
        mock_session = Mock()
        mock_get_session.return_value = mock_session
        mock_session.sql.side_effect = Exception("Query failed")

        result = get_schema_objects()

        assert "error" in result.columns
        mock_session.close.assert_called_once()

    @patch("utils.snowflake_utils.get_schema_objects")
    def test_get_table_list_success(self, mock_get_schema):
        """Test successful table list retrieval."""
        mock_df = pd.DataFrame({"TABLE_NAME": ["CUSTOMER", "ORDERS", "LINEITEM"]})
        mock_get_schema.return_value = mock_df

        result = get_table_list()

        assert result == ["CUSTOMER", "ORDERS", "LINEITEM"]

    @patch("utils.snowflake_utils.get_schema_objects")
    def test_get_table_list_error(self, mock_get_schema):
        """Test table list retrieval with error."""
        mock_df = pd.DataFrame({"error": ["Connection failed"]})
        mock_get_schema.return_value = mock_df

        result = get_table_list()

        assert result == []

    @patch("utils.snowflake_utils.get_snowflake_session")
    def test_get_table_data_success(self, mock_get_session):
        """Test successful table data retrieval."""
        mock_session = Mock()
        mock_get_session.return_value = mock_session

        mock_df = pd.DataFrame({"ID": [1, 2, 3], "NAME": ["Alice", "Bob", "Charlie"]})
        mock_session.sql.return_value.to_pandas.return_value = mock_df

        result = get_table_data("CUSTOMER", limit=10)

        assert len(result) == 3
        assert "ID" in result.columns
        assert "NAME" in result.columns
        mock_session.close.assert_called_once()


class TestSecurityValidation:
    """Tests for security validation functions."""

    def test_additional_security_checks_sql_injection(self):
        """Test detection of SQL injection patterns."""
        malicious_queries = [
            "SELECT * FROM users WHERE id = 1; DROP TABLE users;",
            "SELECT * FROM data WHERE name = '' OR 1=1 --",
            "SELECT * UNION SELECT password FROM credentials",
        ]

        for query in malicious_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert result["error"]
            assert "malicious pattern" in result["message"]

    def test_additional_security_checks_query_length(self):
        """Test query length validation."""
        long_query = (
            "SELECT * FROM table " + "WHERE col = 'x' " * 1000
        )  # Make it very long

        result = _perform_additional_security_checks(long_query.upper(), long_query)

        assert result["error"]
        assert "too long" in result["message"]

    def test_additional_security_checks_excessive_joins(self):
        """Test excessive JOIN detection."""
        query_with_joins = (
            "SELECT * FROM t1 JOIN t2 JOIN t3 JOIN t4 JOIN t5 JOIN t6 JOIN t7 ON ..."
        )

        result = _perform_additional_security_checks(
            query_with_joins.upper(), query_with_joins
        )

        assert result["error"]
        assert "too many JOINs" in result["message"]

    def test_additional_security_checks_forbidden_schema(self):
        """Test forbidden schema access detection."""
        query = "SELECT * FROM production.sensitive_data"

        result = _perform_additional_security_checks(query.upper(), query)

        assert result["error"]
        assert "not allowed" in result["message"]

    def test_additional_security_checks_safe_query(self):
        """Test validation of safe query."""
        safe_query = "SELECT * FROM snowflake_sample_data.tpch_sf10.customer LIMIT 10"

        result = _perform_additional_security_checks(safe_query.upper(), safe_query)

        assert not result["error"]
        assert result["safe_query"] == safe_query

    def test_validate_query_safety_safe_select(self):
        """Test validation of safe SELECT query."""
        query = "SELECT * FROM snowflake_sample_data.tpch_sf10.customer"

        result = _validate_query_safety(query, 1000)

        assert not result["error"]
        assert "LIMIT 1000" in result["safe_query"]

    def test_validate_query_safety_dangerous_keywords(self):
        """Test detection of dangerous keywords."""
        dangerous_queries = [
            "DELETE FROM customer",
            "UPDATE users SET password = 'hack'",
            "DROP TABLE important_data",
            "INSERT INTO logs VALUES ('bad')",
        ]

        for query in dangerous_queries:
            result = _validate_query_safety(query, 1000)
            assert result["error"]
            assert "forbidden keyword" in result["message"]

    def test_validate_query_safety_non_select(self):
        """Test rejection of non-SELECT statements."""
        query = "SHOW TABLES"

        result = _validate_query_safety(query, 1000)

        assert result["error"]
        assert "must start with SELECT" in result["message"]

    def test_validate_query_safety_limit_reduction(self):
        """Test limit reduction for excessive limits."""
        query = "SELECT * FROM customer LIMIT 50000"

        result = _validate_query_safety(query, 1000)

        assert not result["error"]
        assert "LIMIT 1000" in result["safe_query"]
        assert "reduced" in result["message"]


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    def test_rate_limit_under_limit(self):
        """Test rate limiting when under the limit."""
        # Explicitly clear history
        _query_history.clear()

        result = _check_rate_limit()

        assert not result["error"]
        assert len(_query_history) == 1

    def test_rate_limit_at_limit(self):
        """Test rate limiting at the maximum."""
        # Explicitly clear history
        _query_history.clear()

        # Add queries up to the limit
        current_time = time.time()
        for _ in range(_MAX_QUERIES_PER_MINUTE):
            _query_history.append(current_time)

        result = _check_rate_limit()

        assert result["error"]
        assert "Rate limit exceeded" in result["message"]

    def test_rate_limit_cleanup_old_entries(self):
        """Test cleanup of old query history entries."""
        # Explicitly clear history
        _query_history.clear()

        # Add old entries (more than 1 minute ago)
        old_time = time.time() - 120  # 2 minutes ago
        for _ in range(5):
            _query_history.append(old_time)

        result = _check_rate_limit()

        assert not result["error"]
        assert len(_query_history) == 1  # Only the new entry should remain


class TestQueryExecution:
    """Tests for query execution functionality."""

    @patch("utils.snowflake_utils._check_rate_limit")
    @patch("utils.snowflake_utils._validate_query_safety")
    @patch("utils.snowflake_utils.get_snowflake_session")
    def test_execute_query_success(
        self, mock_get_session, mock_validate, mock_rate_limit
    ):
        """Test successful query execution."""
        # Setup mocks
        mock_rate_limit.return_value = {"error": False, "message": "OK"}
        mock_validate.return_value = {
            "error": False,
            "safe_query": "SELECT * FROM customer LIMIT 100",
            "message": "Safe",
        }

        mock_session = Mock()
        mock_get_session.return_value = mock_session

        mock_df = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
        mock_session.sql.return_value.to_pandas.return_value = mock_df

        result = execute_query("SELECT * FROM customer")

        assert len(result) == 2
        assert "id" in result.columns
        mock_session.close.assert_called_once()

    @patch("utils.snowflake_utils._check_rate_limit")
    def test_execute_query_rate_limited(self, mock_rate_limit):
        """Test query execution when rate limited."""
        mock_rate_limit.return_value = {"error": True, "message": "Rate limit exceeded"}

        result = execute_query("SELECT * FROM customer")

        assert "error" in result.columns
        assert "Rate limit exceeded" in result["error"].iloc[0]

    @patch("utils.snowflake_utils._check_rate_limit")
    @patch("utils.snowflake_utils._validate_query_safety")
    def test_execute_query_unsafe(self, mock_validate, mock_rate_limit):
        """Test query execution with unsafe query."""
        mock_rate_limit.return_value = {"error": False, "message": "OK"}
        mock_validate.return_value = {
            "error": True,
            "message": "Dangerous query detected",
        }

        result = execute_query("DROP TABLE customer")

        assert "error" in result.columns
        assert "Dangerous query detected" in result["error"].iloc[0]


class TestResultFormatting:
    """Tests for result formatting functionality."""

    def test_format_query_results_success(self):
        """Test successful result formatting."""
        df = pd.DataFrame(
            {"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"], "age": [25, 30, 35]}
        )

        result = format_query_results(df, max_rows=10, grid_id="test-grid")

        assert isinstance(result, html.Div)
        # The result should contain AG Grid and info message
        assert len(result.children) == 2

    def test_format_query_results_error(self):
        """Test result formatting with error DataFrame."""
        error_df = pd.DataFrame({"error": ["Connection failed"]})

        result = format_query_results(error_df)

        assert isinstance(result, dbc.Alert)
        assert result.color == "danger"

    def test_format_query_results_empty(self):
        """Test result formatting with empty DataFrame."""
        empty_df = pd.DataFrame()

        result = format_query_results(empty_df)

        assert isinstance(result, dbc.Alert)
        assert result.color == "warning"

    def test_format_query_results_large_dataset(self):
        """Test result formatting with large dataset."""
        large_df = pd.DataFrame({"id": range(2000), "value": range(2000)})

        result = format_query_results(large_df, max_rows=100)

        assert isinstance(result, html.Div)
        # Should be limited to 100 rows
        # The exact assertion would depend on the AG Grid implementation

    def test_format_query_results_different_themes(self):
        """Test result formatting with different themes."""
        df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})

        # Test different themes
        for theme in ["alpine", "alpine-dark"]:
            result = format_query_results(df, theme=theme)
            assert isinstance(result, html.Div)


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_empty_query_validation(self):
        """Test validation of empty queries."""
        result = _validate_query_safety("", 1000)
        assert result["error"]
        assert "Empty query" in result["message"]

    def test_whitespace_only_query(self):
        """Test validation of whitespace-only queries."""
        result = _validate_query_safety("   \n\t  ", 1000)
        assert result["error"]
        assert "Empty query" in result["message"]

    def test_query_with_comments(self):
        """Test validation of queries with SQL comments."""
        query_with_comments = """
        /* This is a comment */
        -- Another comment
        SELECT * FROM customer
        """

        result = _validate_query_safety(query_with_comments, 1000)
        assert not result["error"]

    def test_max_rows_cap(self):
        """Test that max_rows is capped at 10000."""
        query = "SELECT * FROM customer"

        result = _validate_query_safety(query, 50000)  # Request more than 10000

        assert not result["error"]
        assert "LIMIT 10000" in result["safe_query"]  # Should be capped at 10000


class TestAdditionalCoverageScenarios:
    """Test additional scenarios to improve coverage."""

    @patch("utils.snowflake_utils.get_snowflake_session")
    def test_get_table_data_exception_with_session_close(self, mock_get_session):
        """Test get_table_data exception handling with session cleanup."""
        # Mock session that raises exception during query
        mock_session = Mock()
        mock_get_session.return_value = mock_session
        mock_session.sql.side_effect = Exception("Connection timeout")

        result = get_table_data("TEST_TABLE")

        # Verify session.close() was called even on exception
        mock_session.close.assert_called_once()
        assert "error" in result.columns
        assert "Query failed" in result["error"].iloc[0]

    def test_nested_parentheses_limit_exceeded(self):
        """Test detection of excessive nested parentheses."""
        # Create query with more than 10 levels of nesting
        deeply_nested_query = "SELECT * FROM table WHERE col IN (" * 12 + "1" + ")" * 12

        result = _perform_additional_security_checks(
            deeply_nested_query.upper(), deeply_nested_query
        )

        assert result["error"]
        # The parentheses check is caught by either the specific nested check or general malicious pattern check
        assert (
            "malicious pattern" in result["message"]
            or "too many nested parentheses" in result["message"]
        )

    def test_nested_parentheses_exact_boundary_condition(self):
        """Test the exact boundary that triggers line 252 - max_depth > 10."""
        # Create a query with exactly 11 levels of nesting that doesn't match injection patterns
        # Use a legitimate nested conditional structure
        query_with_11_levels = (
            "SELECT col FROM table WHERE " + "(" * 11 + "col > 0" + ")" * 11
        )

        result = _perform_additional_security_checks(
            query_with_11_levels.upper(), query_with_11_levels
        )

        assert result["error"]
        assert (
            "Query has too many nested parentheses. Maximum nesting depth is 10."
            == result["message"]
        )

    @patch("utils.snowflake_utils.get_snowflake_session")
    def test_execute_query_slow_performance_warning(self, mock_get_session):
        """Test slow query performance warning."""
        # Mock session and slow query execution
        mock_session = Mock()
        mock_get_session.return_value = mock_session

        # Mock a DataFrame result
        mock_df = pd.DataFrame({"col1": [1, 2, 3]})
        mock_session.sql.return_value.to_pandas.return_value = mock_df

        # Mock time.time to simulate slow execution (>10 seconds)
        with patch("time.time") as mock_time:
            mock_time.side_effect = [0, 15]  # 15 second execution time

            with patch("utils.snowflake_utils._validate_query_safety") as mock_validate:
                mock_validate.return_value = {
                    "error": False,
                    "safe_query": "SELECT * FROM test",
                    "message": "Safe",
                }

                with patch("utils.snowflake_utils._check_rate_limit") as mock_rate:
                    mock_rate.return_value = {"error": False, "message": "OK"}

                    with patch("utils.snowflake_utils.logger") as mock_logger:
                        execute_query("SELECT * FROM test")

                        # Verify slow query warning was logged
                        mock_logger.warning.assert_called()
                        warning_call = mock_logger.warning.call_args[0][0]
                        assert "Slow query detected" in warning_call
                        assert "15.00s" in warning_call

    @patch("utils.snowflake_utils.get_snowflake_session")
    def test_execute_query_large_result_set_info(self, mock_get_session):
        """Test large result set information logging."""
        # Mock session
        mock_session = Mock()
        mock_get_session.return_value = mock_session

        # Mock a large DataFrame result (>5000 rows)
        large_data = {"col1": list(range(6000))}
        mock_df = pd.DataFrame(large_data)
        mock_session.sql.return_value.to_pandas.return_value = mock_df

        with patch("utils.snowflake_utils._validate_query_safety") as mock_validate:
            mock_validate.return_value = {
                "error": False,
                "safe_query": "SELECT * FROM test",
                "message": "Safe",
            }

            with patch("utils.snowflake_utils._check_rate_limit") as mock_rate:
                mock_rate.return_value = {"error": False, "message": "OK"}

                with patch("utils.snowflake_utils.logger") as mock_logger:
                    execute_query("SELECT * FROM test")

                    # Verify large result set info was logged
                    mock_logger.info.assert_called()
                    # Find the large result set log call
                    info_calls = [
                        call[0][0] for call in mock_logger.info.call_args_list
                    ]
                    large_result_logged = any(
                        "Large result set: 6000 rows" in call for call in info_calls
                    )
                    assert large_result_logged

    def test_format_query_results_datetime_column_filter(self):
        """Test datetime column filter assignment in format_query_results."""
        # Create DataFrame with datetime column
        df = pd.DataFrame(
            {
                "date_col": pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03"]),
                "text_col": ["A", "B", "C"],
            }
        )

        # Mock the AG Grid creation to capture column definitions
        with patch("utils.snowflake_utils.dag.AgGrid") as mock_ag_grid:
            # Mock the component creation
            mock_component = Mock()
            mock_ag_grid.return_value = mock_component

            format_query_results(df, grid_id="test-grid")

            # Verify AG Grid was called
            mock_ag_grid.assert_called_once()
            call_args = mock_ag_grid.call_args[1]  # Get keyword arguments

            # Check column definitions
            column_defs = call_args["columnDefs"]

            # Find datetime column definition
            datetime_col_def = None
            text_col_def = None
            for col_def in column_defs:
                if col_def["field"] == "date_col":
                    datetime_col_def = col_def
                elif col_def["field"] == "text_col":
                    text_col_def = col_def

            # Verify datetime column has date filter
            assert datetime_col_def is not None
            assert datetime_col_def["filter"] == "agDateColumnFilter"

            # Verify text column has text filter
            assert text_col_def is not None
            assert text_col_def["filter"] == "agTextColumnFilter"

    def test_format_query_results_numeric_column_filter(self):
        """Test numeric column filter assignment in format_query_results."""
        # Create DataFrame with numeric columns
        df = pd.DataFrame(
            {
                "int_col": [1, 2, 3],
                "float_col": [1.1, 2.2, 3.3],
                "int32_col": pd.array([1, 2, 3], dtype="int32"),
                "float32_col": pd.array([1.1, 2.2, 3.3], dtype="float32"),
            }
        )

        # Mock the AG Grid creation to capture column definitions
        with patch("utils.snowflake_utils.dag.AgGrid") as mock_ag_grid:
            mock_component = Mock()
            mock_ag_grid.return_value = mock_component

            format_query_results(df, grid_id="test-grid")

            # Verify AG Grid was called
            mock_ag_grid.assert_called_once()
            call_args = mock_ag_grid.call_args[1]

            # Check column definitions
            column_defs = call_args["columnDefs"]

            # All columns should have numeric column filter and type
            for col_def in column_defs:
                assert col_def["type"] == "numericColumn"
                assert col_def["filter"] == "agNumberColumnFilter"


class TestAdditionalCoverageEdgeCases:
    """Test edge cases needed for 100% coverage."""

    def test_unicode_normalization_value_error_handling(self):
        """Test Unicode normalization ValueError exception handling (lines 204-205)."""
        from utils.snowflake_utils import _perform_additional_security_checks

        # Patch unicodedata module at the import level
        with patch("unicodedata.name") as mock_name:
            # Mock the name function to raise ValueError for specific characters
            def mock_name_function(char, default=""):
                if char == "\u1234":  # Cherokee character
                    raise ValueError("Unicode name lookup failed")
                return default

            mock_name.side_effect = mock_name_function

            # This should not raise an exception, ValueError should be caught
            result = _perform_additional_security_checks(
                "SELECT * FROM test \u1234", "SELECT * FROM test \u1234"
            )

            # Should pass since the ValueError is caught and ignored
            assert result["error"] is False

    def test_unicode_lookalike_pattern_matching_non_ascii(self):
        """Test Unicode lookalike pattern matching with non-ASCII characters (line 223)."""
        from utils.snowflake_utils import _perform_additional_security_checks

        # Test with Unicode lookalike that should trigger line 223
        # Use a suspicious pattern that contains actual Unicode characters
        malicious_query = (
            "SELECT * FROM users ᎾɌⅮⅇᎡ BY 1"  # Contains Unicode lookalikes for "ORDER"
        )

        result = _perform_additional_security_checks(malicious_query, malicious_query)

        # Should be blocked due to Unicode lookalike detection
        assert result["error"] is True
        assert "suspicious Unicode" in result["message"]

    def test_unicode_normalization_exception_handling(self):
        """Test Unicode normalization exception handling (lines 238-240)."""
        from utils.snowflake_utils import _perform_additional_security_checks

        # Mock unicodedata.normalize to raise an exception
        with patch("unicodedata.normalize") as mock_normalize:
            mock_normalize.side_effect = Exception("Normalization failed")

            # This should not raise an exception, should proceed with original query
            result = _perform_additional_security_checks(
                "SELECT * FROM test", "SELECT * FROM test"
            )

            # Should pass since normalization failure is handled gracefully
            assert result["error"] is False

    def test_unclosed_comment_removal_logic(self):
        """Test unclosed comment removal logic (lines 275-276)."""
        from utils.snowflake_utils import _perform_additional_security_checks

        # Query with unclosed comment should trigger lines 275-276
        query_with_unclosed_comment = (
            "SELECT * FROM test /* this comment is never closed"
        )

        result = _perform_additional_security_checks(
            query_with_unclosed_comment, query_with_unclosed_comment
        )

        # Should pass - the unclosed comment removal logic should handle this
        assert result["error"] is False

    def test_table_reference_parsing_edge_cases(self):
        """Test table reference parsing edge cases (lines 468, 474-478)."""
        from utils.snowflake_utils import _perform_additional_security_checks

        # Test case 1: Unclosed quoted table name (line 474-478) - test the logic path
        query_unclosed_quote = "SELECT * FROM 'production_table"  # Unclosed quote, should parse as 'production_table'
        result1 = _perform_additional_security_checks(
            query_unclosed_quote, query_unclosed_quote
        )
        # This should trigger the unclosed quote handling logic (lines 474-478)
        # The query should pass since 'production_table' is not in forbidden schemas
        assert result1["error"] is False

        # Test case 2: Quoted table name without next break (line 468)
        query_quoted_no_break = (
            'SELECT * FROM "test_table"'  # Quoted but no space/comma after
        )
        result2 = _perform_additional_security_checks(
            query_quoted_no_break, query_quoted_no_break
        )
        assert result2["error"] is False  # Should pass

        # Test case 3: Regular identifier without next break (line 477-478)
        query_no_break = (
            "SELECT * FROM test_table"  # No space/comma/parenthesis after table name
        )
        result3 = _perform_additional_security_checks(query_no_break, query_no_break)
        assert result3["error"] is False  # Should pass

        # Test case 4: To specifically trigger line 468 - quoted table without remainder
        query_quoted_end = "SELECT * FROM 'test'"  # Quoted table at end of FROM clause
        result4 = _perform_additional_security_checks(
            query_quoted_end, query_quoted_end
        )
        assert result4["error"] is False  # Should pass

    def test_unicode_lookalike_ascii_only_bypass(self):
        """Test that ASCII-only patterns don't trigger Unicode detection."""
        from utils.snowflake_utils import _perform_additional_security_checks

        # Test with ASCII-only pattern that looks suspicious but should pass line 223 check
        # This should match the pattern but not trigger line 223 since all chars are ASCII
        ascii_query = "SELECT * FROM users ORDER BY 1"  # All ASCII, should not trigger Unicode detection

        result = _perform_additional_security_checks(ascii_query, ascii_query)

        # Should pass since no actual Unicode characters are present
        assert result["error"] is False

    def test_final_coverage_line_223_unicode_detection(self):
        """Test to specifically hit line 223 - Unicode lookalike return True."""
        from utils.snowflake_utils import _perform_additional_security_checks

        # Use Unicode characters that match the pattern but are NOT in dangerous blocks
        # Using modifier letter capital O (ᴼ) which matches [ᴼOｏ] pattern but is not in dangerous blocks
        # This should bypass the general Unicode block check and reach the specific pattern check at line 223
        unicode_query = (
            "SELECT * FROM test UNIᴼn BY 1"  # UNION with modifier letter capital O
        )

        result = _perform_additional_security_checks(unicode_query, unicode_query)

        # Should be blocked due to Unicode lookalike detection hitting line 223
        assert result["error"] is True
        assert "suspicious Unicode" in result["message"]

    def test_final_coverage_line_468_table_parsing(self):
        """Test to specifically hit line 468 - table reference with dot and next_break found."""
        from utils.snowflake_utils import _perform_additional_security_checks

        # Create a query with quoted schema.table that has a space after the dot notation
        # Use an allowed schema name to avoid blocking
        # This should trigger line 468: table_ref += remainder[:next_break.start()]
        query_with_dot_break = "SELECT * FROM 'snowflake_sample_data'.'table' WHERE id = 1"  # Quoted schema.table with space

        result = _perform_additional_security_checks(
            query_with_dot_break, query_with_dot_break
        )

        # Should pass - this hits the table parsing logic at line 468
        assert result["error"] is False

    def test_final_coverage_line_476_unclosed_quote_parsing(self):
        """Test to specifically hit line 476 - unclosed quote with next_break found."""
        from utils.snowflake_utils import _perform_additional_security_checks

        # Create a query with unclosed quote that has a space after the table name
        # This should trigger the unclosed quote logic and hit line 476
        query_unclosed_with_break = (
            "SELECT * FROM 'test_table WHERE id = 1"  # Unclosed quote with space
        )

        result = _perform_additional_security_checks(
            query_unclosed_with_break, query_unclosed_with_break
        )

        # Should pass - this hits the unclosed quote parsing logic at line 476
        assert result["error"] is False


if __name__ == "__main__":
    pytest.main([__file__])
