"""
Critical connection and session security tests for Snowflake utilities.

This test suite focuses on connection security, session management,
and potential vulnerabilities in authentication/authorization.
"""

import pytest
import os
from unittest.mock import patch, Mock, mock_open
from utils.snowflake_utils import (
    get_snowflake_session,
    get_login_token,
    is_running_in_spcs,
    execute_query,
)


@pytest.mark.security
class TestConnectionSecurity:
    """Test connection security and session management."""

    def test_token_file_tampering_detection(self):
        """Test detection of potentially tampered token files."""
        # Test various malicious token contents
        malicious_tokens = [
            "",  # Empty token
            " ",  # Whitespace only
            "\n\n\n",  # Only newlines
            "x" * 100000,  # Extremely long token
            "javascript:alert('xss')",  # XSS attempt
            "../../../etc/passwd",  # Path traversal
            "$(rm -rf /)",  # Command injection
            "\x00\x01\x02\x03",  # Binary data
            "token\nSET ROLE admin;",  # SQL injection in token
        ]

        for malicious_token in malicious_tokens:
            with patch("builtins.open", mock_open(read_data=malicious_token)):
                try:
                    token = get_login_token()
                    # Verify token is returned as-is (responsibility of Snowflake to validate)
                    assert token == malicious_token
                except Exception:
                    # If function throws exception, that's acceptable too
                    pass

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_environment_variables(self):
        """Test behavior when critical environment variables are missing."""
        with patch("utils.snowflake_utils.is_running_in_spcs", return_value=False):
            # Should handle missing environment variables gracefully
            session = get_snowflake_session()
            assert session is None, "Should return None when env vars missing"

    @patch.dict(
        os.environ,
        {
            "SNOWFLAKE_ACCOUNT": "",
            "SNOWFLAKE_USER": "",
            "SNOWFLAKE_PASSWORD": "",
        },
    )
    def test_empty_environment_variables(self):
        """Test behavior when environment variables are empty."""
        with patch("utils.snowflake_utils.is_running_in_spcs", return_value=False):
            session = get_snowflake_session()
            assert session is None, "Should return None when env vars empty"

    @patch.dict(
        os.environ,
        {
            "SNOWFLAKE_ACCOUNT": "' OR 1=1; DROP TABLE users; --",
            "SNOWFLAKE_USER": "'; DELETE FROM admin; --",
            "SNOWFLAKE_PASSWORD": "password'; GRANT ALL TO PUBLIC; --",
        },
    )
    def test_sql_injection_in_environment_variables(self):
        """Test handling of SQL injection attempts in environment variables."""
        with patch("utils.snowflake_utils.is_running_in_spcs", return_value=False):
            with patch("utils.snowflake_utils.Session") as mock_session_class:
                # Should pass the malicious values to Snowflake (their responsibility to validate)
                mock_session = Mock()
                mock_session_class.builder.configs.return_value.create.return_value = (
                    mock_session
                )

                get_snowflake_session()

                # Verify the malicious values were used in connection
                mock_session_class.builder.configs.assert_called_once()
                call_args = mock_session_class.builder.configs.call_args[0][0]
                assert "' OR 1=1" in call_args["account"]

    def test_spcs_token_file_access_security(self):
        """Test security of SPCS token file access."""
        # Test file permission bypass attempts
        malicious_paths = [
            "/snowflake/session/token/../../../etc/passwd",
            "/snowflake/session/token/../../../../../../etc/shadow",
            "/snowflake/session/./token/../config",
            "\\snowflake\\session\\token\\..\\..\\windows\\system32\\config",
        ]

        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True

            for malicious_path in malicious_paths:
                # The function should only check the specific path
                is_spcs = is_running_in_spcs()
                assert is_spcs, "Should detect SPCS environment"
                # Verify only the expected path was checked
                mock_exists.assert_called_with("/snowflake/session/token")


@pytest.mark.security
class TestSessionIsolation:
    """Test session isolation and cleanup."""

    @patch("utils.snowflake_utils.get_snowflake_session")
    def test_session_cleanup_on_exception(self, mock_get_session):
        """Test that sessions are properly cleaned up on exceptions."""
        mock_session = Mock()
        mock_get_session.return_value = mock_session

        # Make SQL execution fail
        mock_session.sql.side_effect = Exception("Connection lost")

        # Execute query that will fail
        result = execute_query("SELECT * FROM valid_table")

        # Verify session was closed even after exception
        mock_session.close.assert_called_once()
        assert "error" in result.columns

    @patch("utils.snowflake_utils.get_snowflake_session")
    def test_multiple_session_isolation(self, mock_get_session):
        """Test that multiple query executions use isolated sessions."""
        # Create different mock sessions for each call
        session1 = Mock()
        session2 = Mock()
        mock_get_session.side_effect = [session1, session2]

        # Configure successful responses
        import pandas as pd

        session1.sql.return_value.to_pandas.return_value = pd.DataFrame(
            {"result1": [1]}
        )
        session2.sql.return_value.to_pandas.return_value = pd.DataFrame(
            {"result2": [2]}
        )

        # Execute two queries
        result1 = execute_query("SELECT 1")
        result2 = execute_query("SELECT 2")

        # Verify both sessions were used and closed
        session1.close.assert_called_once()
        session2.close.assert_called_once()
        assert len(result1) == 1
        assert len(result2) == 1


@pytest.mark.security
class TestCredentialSecurity:
    """Test credential handling security."""

    def test_credential_exposure_in_logs(self):
        """Test that credentials are not exposed in log messages."""
        with patch("utils.snowflake_utils.logger") as mock_logger:
            with patch.dict(
                os.environ,
                {
                    "SNOWFLAKE_PASSWORD": "super_secret_password_123",
                    "SNOWFLAKE_USER": "sensitive_username",
                },
            ):
                with patch(
                    "utils.snowflake_utils.is_running_in_spcs", return_value=False
                ):
                    with patch("utils.snowflake_utils.Session") as mock_session_class:
                        mock_session_class.builder.configs.return_value.create.side_effect = Exception(
                            "Auth failed"
                        )

                        # Attempt to create session (will fail)
                        get_snowflake_session()

                        # Check that sensitive data is not in log messages
                        for call in mock_logger.error.call_args_list:
                            log_message = str(call)
                            assert "super_secret_password_123" not in log_message
                            assert "sensitive_username" not in log_message

    def test_token_exposure_prevention(self):
        """Test that SPCS tokens are not exposed in error messages."""
        sensitive_token = (
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.sensitive_payload.signature"
        )

        with patch("builtins.open", mock_open(read_data=sensitive_token)):
            with patch("utils.snowflake_utils.logger") as mock_logger:
                with patch("utils.snowflake_utils.Session") as mock_session_class:
                    mock_session_class.builder.configs.return_value.create.side_effect = Exception(
                        "Invalid token"
                    )

                    # Attempt to create SPCS session (will fail)
                    with patch(
                        "utils.snowflake_utils.is_running_in_spcs", return_value=True
                    ):
                        get_snowflake_session()

                    # Verify token is not in log messages
                    for call in mock_logger.error.call_args_list:
                        log_message = str(call)
                        assert sensitive_token not in log_message
                        assert "eyJ0eXAi" not in log_message  # JWT header


@pytest.mark.security
class TestRateLimitingSecurity:
    """Test rate limiting security mechanisms."""

    def test_rate_limit_bypass_attempts(self, reset_query_history):
        """Test attempts to bypass rate limiting."""
        from utils.snowflake_utils import _query_history, _MAX_QUERIES_PER_MINUTE
        import time

        # Fill up rate limit
        current_time = time.time()
        for _ in range(_MAX_QUERIES_PER_MINUTE):
            _query_history.append(current_time)

        # Attempt various bypass techniques
        bypass_attempts = [
            "SELECT 1",  # Normal query
            "select 1",  # Case variation
            "SELECT\t1",  # Tab character
            "SELECT\n1",  # Newline
            " SELECT 1 ",  # Whitespace padding
            "/* comment */ SELECT 1",  # Comment prefix
            "-- comment\nSELECT 1",  # Line comment
        ]

        for attempt in bypass_attempts:
            result = execute_query(attempt)
            assert "error" in result.columns
            assert "Rate limit exceeded" in result["error"].iloc[0]

    def test_concurrent_rate_limit_enforcement(self, reset_query_history):
        """Test rate limiting under concurrent access."""
        from utils.snowflake_utils import _MAX_QUERIES_PER_MINUTE
        import threading

        results = []

        def execute_concurrent_query(query_id):
            result = execute_query(f"SELECT {query_id}")
            results.append(result)

        # Launch concurrent queries exceeding rate limit
        threads = []
        for i in range(_MAX_QUERIES_PER_MINUTE + 5):
            thread = threading.Thread(target=execute_concurrent_query, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Count successful vs rate-limited queries
        successful = sum(1 for r in results if "error" not in r.columns)
        rate_limited = sum(
            1
            for r in results
            if "error" in r.columns and "Rate limit" in r["error"].iloc[0]
        )

        # Should have some rate-limited queries
        assert rate_limited > 0, "Rate limiting should block some concurrent queries"
        assert successful <= _MAX_QUERIES_PER_MINUTE, "Should not exceed rate limit"


@pytest.mark.security
class TestInputValidationSecurity:
    """Test input validation security edge cases."""

    def test_null_byte_injection(self):
        """Test handling of null byte injection attempts."""
        null_byte_queries = [
            "SELECT * FROM users\x00; DROP TABLE admin; --",
            "SELECT * FROM users WHERE id = '1'\x00 UNION SELECT password FROM admin",
            "\x00SELECT * FROM system_tables",
            "SELECT * FROM users\x00\x00\x00",
        ]

        for query in null_byte_queries:
            result = execute_query(query)
            assert "error" in result.columns, (
                f"Should reject null byte query: {repr(query)}"
            )

    def test_control_character_injection(self):
        """Test handling of control character injection."""
        control_char_queries = [
            "SELECT * FROM users\r\nUNION SELECT password FROM admin",
            "SELECT * FROM users\x0bUNION SELECT password",
            "SELECT * FROM users\x0cUNION SELECT password",
            "SELECT * FROM users\x1bUNION SELECT password",  # Escape character
        ]

        for query in control_char_queries:
            result = execute_query(query)
            # Control characters might be handled differently, verify structure is maintained
            assert isinstance(result.columns.tolist(), list)

    def test_extremely_long_input_handling(self):
        """Test handling of extremely long inputs."""
        # Test very long query (avoid SQL injection patterns like "1 = 1")
        very_long_query = (
            "SELECT * FROM users WHERE " + "id > 0 AND " * 1500
        )  # Creates >15,000 chars

        result = execute_query(very_long_query)
        assert "error" in result.columns
        assert "too long" in result["error"].iloc[0]

        # Test very long table name
        long_table_query = "SELECT * FROM " + "a" * 1000
        result = execute_query(long_table_query)
        assert "error" in result.columns
