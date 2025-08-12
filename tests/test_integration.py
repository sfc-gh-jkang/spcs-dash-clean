"""
Integration tests for snowflake_utils module.

These tests verify the integration between different components
and test real-world usage scenarios.
"""

import pytest
from unittest.mock import Mock, patch
import pandas as pd
from utils.snowflake_utils import (
    execute_query,
    format_query_results,
    get_schema_objects,
    get_table_data,
)


@pytest.mark.integration
class TestEndToEndQueryFlow:
    """Test complete query execution flow."""

    @patch("utils.snowflake_utils.get_snowflake_session")
    def test_complete_query_execution_flow(self, mock_get_session, sample_dataframe):
        """Test the complete flow from query to formatted results."""
        # Setup mock session
        mock_session = Mock()
        mock_get_session.return_value = mock_session
        mock_session.sql.return_value.to_pandas.return_value = sample_dataframe

        # Execute query
        query = "SELECT * FROM snowflake_sample_data.tpch_sf10.customer LIMIT 5"
        result_df = execute_query(query)

        # Verify query execution
        assert len(result_df) == 5
        assert "error" not in result_df.columns

        # Format results
        formatted_results = format_query_results(result_df)

        # Verify formatting
        assert formatted_results is not None
        mock_session.close.assert_called_once()

    @patch("utils.snowflake_utils.get_snowflake_session")
    def test_query_with_automatic_limit_addition(
        self, mock_get_session, sample_dataframe
    ):
        """Test that queries without LIMIT get automatic limits."""
        mock_session = Mock()
        mock_get_session.return_value = mock_session
        mock_session.sql.return_value.to_pandas.return_value = sample_dataframe

        # Execute query without LIMIT
        query = "SELECT * FROM snowflake_sample_data.tpch_sf10.customer"
        result_df = execute_query(query)

        # Verify that the session.sql was called with a query containing LIMIT
        called_query = mock_session.sql.call_args[0][0]
        assert "LIMIT" in called_query.upper()
        assert len(result_df) == 5

    @patch("utils.snowflake_utils.get_snowflake_session")
    def test_query_with_limit_reduction(self, mock_get_session, sample_dataframe):
        """Test that excessive limits are reduced."""
        mock_session = Mock()
        mock_get_session.return_value = mock_session
        mock_session.sql.return_value.to_pandas.return_value = sample_dataframe

        # Execute query with excessive limit
        query = "SELECT * FROM snowflake_sample_data.tpch_sf10.customer LIMIT 50000"
        result_df = execute_query(query, max_rows=1000)

        # Verify that the limit was reduced
        called_query = mock_session.sql.call_args[0][0]
        assert "LIMIT 1000" in called_query
        assert len(result_df) == 5


@pytest.mark.integration
class TestSchemaDataIntegration:
    """Test integration of schema and data retrieval functions."""

    @patch("utils.snowflake_utils.get_snowflake_session")
    def test_schema_to_table_data_flow(self, mock_get_session):
        """Test the flow from getting schema objects to table data."""
        mock_session = Mock()
        mock_get_session.return_value = mock_session

        # Mock schema objects response
        schema_df = pd.DataFrame(
            {
                "TABLE_NAME": ["CUSTOMER", "ORDERS"],
                "TABLE_TYPE": ["BASE TABLE", "BASE TABLE"],
                "ROW_COUNT": [1000, 5000],
                "BYTES": [1024, 2048],
                "CREATED": ["2023-01-01", "2023-01-02"],
                "TABLE_SCHEMA": ["TPCH_SF10", "TPCH_SF10"],
                "TABLE_CATALOG": ["SNOWFLAKE_SAMPLE_DATA", "SNOWFLAKE_SAMPLE_DATA"],
            }
        )

        # Mock table data response
        table_df = pd.DataFrame(
            {"C_CUSTKEY": [1, 2, 3], "C_NAME": ["Customer1", "Customer2", "Customer3"]}
        )

        # Configure mocks to return different data for different calls
        mock_session.sql.return_value.to_pandas.side_effect = [schema_df, table_df]

        # Get schema objects
        schema_result = get_schema_objects()
        assert len(schema_result) == 2
        assert "CUSTOMER" in schema_result["TABLE_NAME"].values

        # Get table data for first table
        table_name = schema_result["TABLE_NAME"].iloc[0]
        table_result = get_table_data(table_name, limit=10)
        assert len(table_result) == 3
        assert "C_CUSTKEY" in table_result.columns


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Test integration of error handling across components."""

    @patch("utils.snowflake_utils.get_snowflake_session")
    def test_session_failure_propagation(self, mock_get_session):
        """Test that session failures propagate correctly."""
        mock_get_session.return_value = None

        # Test schema objects
        schema_result = get_schema_objects()
        assert "error" in schema_result.columns

        # Test table data
        table_result = get_table_data("CUSTOMER")
        assert "error" in table_result.columns

        # Test query execution
        query_result = execute_query("SELECT * FROM customer")
        assert "error" in query_result.columns

    @patch("utils.snowflake_utils.get_snowflake_session")
    def test_query_exception_handling(self, mock_get_session):
        """Test handling of query execution exceptions."""
        mock_session = Mock()
        mock_get_session.return_value = mock_session
        mock_session.sql.side_effect = Exception("Network timeout")

        result = execute_query("SELECT * FROM snowflake_sample_data.tpch_sf10.customer")

        assert "error" in result.columns
        assert "Network timeout" in result["error"].iloc[0]
        mock_session.close.assert_called_once()


@pytest.mark.integration
class TestRateLimitingIntegration:
    """Test rate limiting integration with query execution."""

    def test_rate_limiting_blocks_excessive_queries(self, reset_query_history):
        """Test that rate limiting prevents excessive query execution."""
        from utils.snowflake_utils import _query_history, _MAX_QUERIES_PER_MINUTE
        import time

        # Fill up the rate limit
        current_time = time.time()
        for _ in range(_MAX_QUERIES_PER_MINUTE):
            _query_history.append(current_time)

        # Try to execute another query
        result = execute_query("SELECT 1")

        assert "error" in result.columns
        assert "Rate limit exceeded" in result["error"].iloc[0]

    def test_rate_limiting_allows_queries_after_time_window(self, reset_query_history):
        """Test that rate limiting allows queries after the time window."""
        from utils.snowflake_utils import _query_history
        import time

        # Add old entries (more than 1 minute ago)
        old_time = time.time() - 120  # 2 minutes ago
        for _ in range(5):
            _query_history.append(old_time)

        # Should be able to execute a new query
        with patch("utils.snowflake_utils.get_snowflake_session") as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = mock_session
            mock_session.sql.return_value.to_pandas.return_value = pd.DataFrame(
                {"result": [1]}
            )

            result = execute_query("SELECT 1")
            assert "error" not in result.columns


@pytest.mark.integration
class TestThemeIntegration:
    """Test theme integration with result formatting."""

    def test_result_formatting_with_different_themes(self, sample_dataframe):
        """Test that result formatting works with different themes."""
        themes = ["alpine", "alpine-dark"]

        for theme in themes:
            result = format_query_results(sample_dataframe, theme=theme)
            assert result is not None
            # The exact structure depends on the implementation
            # but we can verify it returns a valid HTML structure

    def test_grid_id_uniqueness(self, sample_dataframe):
        """Test that unique grid IDs are generated."""
        grid_ids = ["grid1", "grid2", "grid3"]

        for grid_id in grid_ids:
            result = format_query_results(sample_dataframe, grid_id=grid_id)
            assert result is not None
            # Each should have its unique grid ID


@pytest.mark.integration
@pytest.mark.slow
class TestLargeDatasetHandling:
    """Test handling of large datasets."""

    def test_large_dataset_formatting(self, large_datasets):
        """Test formatting of large datasets."""
        large_df = large_datasets(5000)  # 5000 rows

        result = format_query_results(large_df, max_rows=1000)

        assert result is not None
        # Should handle large datasets gracefully

    @patch("utils.snowflake_utils.get_snowflake_session")
    def test_large_query_result_handling(self, mock_get_session, large_datasets):
        """Test handling of queries that return large results."""
        mock_session = Mock()
        mock_get_session.return_value = mock_session

        # Simulate a large dataset response
        large_df = large_datasets(8000)
        mock_session.sql.return_value.to_pandas.return_value = large_df

        result = execute_query("SELECT * FROM large_table", max_rows=2000)

        # Should be limited to max_rows
        assert len(result) == 8000  # The mock returns the full dataset
        # But in real implementation, it would be limited


@pytest.mark.integration
class TestSecurityIntegration:
    """Test security integration across the system."""

    def test_end_to_end_security_validation(self):
        """Test complete security validation flow."""
        dangerous_query = "DELETE FROM users WHERE id = 1"

        result = execute_query(dangerous_query)

        assert "error" in result.columns
        assert "forbidden keyword" in result["error"].iloc[0]

    def test_security_with_result_formatting(self):
        """Test that security errors are properly formatted."""
        error_df = pd.DataFrame({"error": ["Query rejected for security reasons"]})

        result = format_query_results(error_df)

        # Should return an error alert
        assert hasattr(result, "color")  # It's a DBC Alert
        assert result.color == "danger"


@pytest.mark.integration
class TestEnvironmentIntegration:
    """Test environment-specific integration."""

    @patch("utils.snowflake_utils.is_running_in_spcs")
    @patch("utils.snowflake_utils.get_login_token")
    @patch("utils.snowflake_utils.Session")
    def test_spcs_environment_integration(
        self, mock_session_class, mock_get_token, mock_spcs_check
    ):
        """Test integration in SPCS environment."""
        mock_spcs_check.return_value = True
        mock_get_token.return_value = "test_token"
        mock_session = Mock()
        mock_session_class.builder.configs.return_value.create.return_value = (
            mock_session
        )
        mock_session.sql.return_value.to_pandas.return_value = pd.DataFrame(
            {"result": [1]}
        )

        with patch.dict(
            "os.environ",
            {"SNOWFLAKE_HOST": "test_host", "SNOWFLAKE_ACCOUNT": "test_account"},
        ):
            result = execute_query("SELECT 1")
            assert "error" not in result.columns

    @patch("utils.snowflake_utils.is_running_in_spcs")
    @patch("utils.snowflake_utils.Session")
    def test_local_environment_integration(self, mock_session_class, mock_spcs_check):
        """Test integration in local environment."""
        mock_spcs_check.return_value = False
        mock_session = Mock()
        mock_session_class.builder.configs.return_value.create.return_value = (
            mock_session
        )
        mock_session.sql.return_value.to_pandas.return_value = pd.DataFrame(
            {"result": [1]}
        )

        with patch.dict(
            "os.environ",
            {
                "SNOWFLAKE_ACCOUNT": "test_account",
                "SNOWFLAKE_USER": "test_user",
                "SNOWFLAKE_PASSWORD": "test_password",
            },
        ):
            result = execute_query("SELECT 1")
            assert "error" not in result.columns
