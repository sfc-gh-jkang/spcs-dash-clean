"""
Test page callback functions directly to improve coverage.
"""

import pytest  # noqa: F401
import pandas as pd
from unittest.mock import patch, Mock
from dash import html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go  # noqa: F401

# Mock dash.register_page to avoid registration errors during import
with patch("dash.register_page"):
    from pages import analytics, dashboard, data_browser


class TestDashboardCallbacks:
    """Test dashboard page callback functions."""

    @patch("pages.dashboard.execute_query")
    @patch("pages.dashboard.px.bar")
    def test_update_dashboard_revenue(self, mock_bar, mock_exec):
        """Test dashboard update with revenue selection."""
        # Mock plotly figure
        mock_fig = Mock()
        mock_bar.return_value = mock_fig

        theme_data = {"current_theme": "bootstrap"}

        # Stub data to avoid Snowflake in unit test
        import pandas as pd

        mock_exec.return_value = pd.DataFrame({"REGION": ["N", "S"], "REVENUE": [1, 2]})

        # Test the callback function directly
        figure, toast_open, toast_children, metrics = dashboard.update_dashboard(
            "revenue", theme_data, None, None, None
        )

        # Verify the response
        assert figure is not None
        assert not toast_open  # No error
        assert metrics is not None
        mock_bar.assert_called_once()

    @patch("pages.dashboard.execute_query")
    @patch("pages.dashboard.px.bar")
    def test_update_dashboard_customers(self, mock_bar, mock_exec):
        """Test dashboard update with customers selection."""
        # Mock plotly figure
        mock_fig = Mock()
        mock_bar.return_value = mock_fig

        theme_data = {"current_theme": "bootstrap"}

        import pandas as pd

        mock_exec.return_value = pd.DataFrame(
            {"QUARTER": ["Q1", "Q2"], "CUSTOMERS": [10, 20]}
        )

        figure, toast_open, toast_children, metrics = dashboard.update_dashboard(
            "customers", theme_data, None, None, None
        )

        assert figure is not None
        assert not toast_open
        assert metrics is not None

    @patch("pages.dashboard.execute_query")
    @patch("pages.dashboard.px.bar")
    def test_update_dashboard_sales(self, mock_bar, mock_exec):
        """Test dashboard update with sales selection."""
        mock_fig = Mock()
        mock_bar.return_value = mock_fig

        theme_data = {"current_theme": "bootstrap"}

        import pandas as pd

        mock_exec.return_value = pd.DataFrame(
            {"MONTH": ["Jan", "Feb"], "SALES": [1, 2]}
        )

        figure, toast_open, toast_children, metrics = dashboard.update_dashboard(
            "sales", theme_data, None, None, None
        )

        assert figure is not None
        assert not toast_open
        assert metrics is not None

    @patch("pages.dashboard.execute_query")
    @patch("pages.dashboard.px.bar")
    def test_update_dashboard_products(self, mock_bar, mock_exec):
        """Test dashboard update with products selection."""
        mock_fig = Mock()
        mock_bar.return_value = mock_fig

        theme_data = {"current_theme": "bootstrap"}

        import pandas as pd

        mock_exec.return_value = pd.DataFrame({"PRODUCT": ["A", "B"], "UNITS": [1, 2]})

        figure, toast_open, toast_children, metrics = dashboard.update_dashboard(
            "products", theme_data, None, None, None
        )

        assert figure is not None
        assert not toast_open
        assert metrics is not None

    @patch("pages.dashboard.execute_query", side_effect=Exception("Test error"))
    def test_update_dashboard_exception_handling(self, mock_exec):
        """Test dashboard callback exception handling."""
        theme_data = {"current_theme": "bootstrap"}

        with patch("pages.dashboard.px.bar") as mock_bar:
            # Mock the error case figure for the exception handler
            mock_error_fig = Mock()
            mock_bar.return_value = mock_error_fig

            figure, toast_open, toast_children, metrics = dashboard.update_dashboard(
                "revenue", theme_data, None, None, None
            )

            # Should handle exception gracefully by returning appropriate error responses
            assert toast_open  # Error toast should be open
            assert "Test error" in str(toast_children)
            assert figure == mock_error_fig  # Should return the error figure


class TestAnalyticsCallbacks:
    """Test analytics page callback functions."""

    @patch("pages.analytics.execute_query")
    @patch("pages.analytics.format_query_results")
    def test_execute_custom_query_success(self, mock_format, mock_execute):
        """Test successful custom query execution."""
        # Mock successful query execution
        mock_df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
        mock_execute.return_value = mock_df
        mock_format.return_value = html.Div("Query results")

        with patch("pages.analytics.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = [{"prop_id": "execute-query-btn.n_clicks"}]
            content, toast_open, toast_children, toast_icon = (
                analytics.execute_custom_query(1, "SELECT * FROM test_table")
            )

        assert content is not None
        assert toast_open is True
        assert toast_icon == "success"
        assert "successfully" in str(toast_children).lower()
        # Loading is now handled by standard dcc.Loading component
        mock_execute.assert_called_once_with("SELECT * FROM test_table")
        mock_format.assert_called_once_with(
            mock_df,
            max_rows=1000,
            grid_id="analytics-query-results-grid",
            apply_theme_on_container=True,
        )

    def test_execute_custom_query_no_clicks(self):
        """Test query execution with no button clicks."""
        with patch("pages.analytics.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = []  # No trigger context (page load)

            content, toast_open, toast_children, toast_icon = (
                analytics.execute_custom_query(None, "SELECT * FROM test")
            )

            assert "Enter a SQL query" in str(content)
            assert toast_open is False

    def test_execute_custom_query_zero_clicks(self):
        """Test query execution with zero clicks."""
        with patch("pages.analytics.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = [
                {"prop_id": "execute-query-btn.n_clicks"}
            ]  # Button triggered but 0 clicks

            content, toast_open, toast_children, toast_icon = (
                analytics.execute_custom_query(0, "SELECT * FROM test")
            )

            assert "Enter a SQL query" in str(content)
            assert toast_open is False

    def test_execute_custom_query_empty_query(self):
        """Test query execution with empty query."""
        with patch("pages.analytics.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = [
                {"prop_id": "execute-query-btn.n_clicks"}
            ]  # Valid button click

            content, toast_open, toast_children, toast_icon = (
                analytics.execute_custom_query(1, "")
            )

            assert "Please enter a SQL query" in str(content)
            assert toast_open is True
            assert toast_icon == "warning"
            assert isinstance(content, dbc.Alert)

    def test_execute_custom_query_whitespace_only(self):
        """Test query execution with whitespace-only query."""
        with patch("pages.analytics.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = [
                {"prop_id": "execute-query-btn.n_clicks"}
            ]  # Valid button click

            content, toast_open, toast_children, toast_icon = (
                analytics.execute_custom_query(1, "   \n\t   ")
            )

            assert "Please enter a SQL query" in str(content)
            assert toast_open is True
            assert toast_icon == "warning"
            assert isinstance(content, dbc.Alert)

    def test_clear_query_btn(self):
        """Test clear query button callback."""
        result = analytics.clear_query(1)

        assert result == ""

    def test_clear_query_btn_no_clicks(self):
        """Test clear query with no clicks."""
        from dash import no_update

        result = analytics.clear_query(None)

        # When n_clicks is None, Dash returns no_update
        assert result == no_update

    @patch("pages.analytics.execute_query")
    def test_execute_custom_query_with_error_dataframe(self, mock_execute):
        """Test query execution that returns error in dataframe."""
        # Mock error response from execute_query
        error_df = pd.DataFrame({"error": ["Query failed: Invalid syntax"]})
        mock_execute.return_value = error_df

        with patch("pages.analytics.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = [{"prop_id": "execute-query-btn.n_clicks"}]
            content, toast_open, toast_children, toast_icon = (
                analytics.execute_custom_query(1, "INVALID SQL")
            )

        assert toast_open is True
        assert toast_icon == "danger"
        assert "Query failed" in str(content)
        assert "Query failed" in str(toast_children)

    @patch("pages.analytics.execute_query")
    def test_execute_custom_query_with_exception(self, mock_execute):
        """Test query execution that raises an exception."""
        # Mock exception during execution
        mock_execute.side_effect = Exception("Database connection failed")

        with patch("pages.analytics.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = [{"prop_id": "execute-query-btn.n_clicks"}]
            content, toast_open, toast_children, toast_icon = (
                analytics.execute_custom_query(1, "SELECT * FROM test")
            )

        assert toast_open is True
        assert toast_icon == "danger"
        assert "Unexpected error" in str(content)
        assert "Unexpected error" in str(toast_children)

    def test_execute_custom_query_callback_returns_four_outputs(self):
        """Test that callback returns exactly 4 outputs (no loading style)."""
        with (
            patch("pages.analytics.execute_query") as mock_execute,
            patch("pages.analytics.format_query_results") as mock_format,
            patch("pages.analytics.dash.callback_context") as mock_ctx,
        ):
            mock_ctx.triggered = [{"prop_id": "execute-query-btn.n_clicks"}]

            # Mock successful query execution
            mock_df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
            mock_execute.return_value = mock_df
            mock_format.return_value = html.Div("Query results")

            result = analytics.execute_custom_query(1, "SELECT * FROM test")

            # Verify exactly 4 outputs (no loading style)
            assert len(result) == 4
            content, toast_open, toast_children, toast_icon = result
            assert content is not None
            assert toast_open is True
            assert toast_icon == "success"

    def test_execute_custom_query_wrong_trigger(self):
        """Test query execution with wrong trigger ID."""
        with patch("pages.analytics.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = [
                {"prop_id": "some-other-btn.n_clicks"}
            ]  # Wrong trigger

            content, toast_open, toast_children, toast_icon = (
                analytics.execute_custom_query(1, "SELECT * FROM test")
            )

            assert "Enter a SQL query" in str(content)
            assert toast_open is False
            assert toast_icon == "info"

    def test_run_predefined_analysis_sales(self):
        """Test predefined sales analysis."""
        theme_data = {"current_theme": "bootstrap"}

        content, header = analytics.run_predefined_analysis(1, theme_data, "sales")

        assert content is not None
        assert "Sales Analysis Results" == str(header)

    def test_run_predefined_analysis_customers(self):
        """Test predefined customers analysis."""
        theme_data = {"current_theme": "bootstrap"}

        content, header = analytics.run_predefined_analysis(1, theme_data, "customers")

        assert content is not None
        assert "Customer Segmentation Results" == str(header)

    def test_run_predefined_analysis_timeseries(self):
        """Test predefined timeseries analysis."""
        theme_data = {"current_theme": "bootstrap"}

        content, header = analytics.run_predefined_analysis(1, theme_data, "timeseries")

        assert content is not None
        assert "Time Series Analysis Results" == str(header)

    def test_run_predefined_analysis_no_clicks(self):
        """Test predefined analysis with no clicks."""
        theme_data = {"current_theme": "bootstrap"}

        content, header = analytics.run_predefined_analysis(None, theme_data, "sales")

        assert content == []
        assert "Analysis Results" == str(header)

    @patch("pages.analytics.execute_query", side_effect=Exception("Analysis error"))
    def test_run_predefined_analysis_exception(self, mock_df):
        """Test predefined analysis exception handling."""
        theme_data = {"current_theme": "bootstrap"}

        content, header = analytics.run_predefined_analysis(1, theme_data, "sales")

        assert "Error" in str(content)
        assert "Analysis Results" in str(header)


class TestAnalyticsCommonQueries:
    """Test analytics page common query functionality."""

    def test_insert_common_query_top_customers(self):
        """Test inserting top customers query."""
        from pages.analytics import insert_common_query

        # Mock callback context
        with patch("pages.analytics.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = [{"prop_id": "query-top-customers.n_clicks"}]

            result = insert_common_query(
                1, None, None, None, None, None, None, None, None
            )

            assert result is not None
            assert "Top 10 Customers by Revenue" in result
            assert "SELECT" in result.upper()
            assert "customer" in result.lower()

    def test_insert_common_query_sales_region(self):
        """Test inserting sales by region query."""
        from pages.analytics import insert_common_query

        with patch("pages.analytics.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = [{"prop_id": "query-sales-region.n_clicks"}]

            result = insert_common_query(
                None, 1, None, None, None, None, None, None, None
            )

            assert result is not None
            assert "Sales Performance by Region" in result
            assert "region" in result.lower()
            assert "revenue" in result.lower()

    def test_insert_common_query_product_performance(self):
        """Test inserting product performance query."""
        from pages.analytics import insert_common_query

        with patch("pages.analytics.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = [{"prop_id": "query-product-performance.n_clicks"}]

            result = insert_common_query(
                None, None, 1, None, None, None, None, None, None
            )

            assert result is not None
            assert "Product Performance Analysis" in result
            assert "product" in result.lower()
            assert "part" in result.lower()

    def test_insert_common_query_monthly_trends(self):
        """Test inserting monthly trends query."""
        from pages.analytics import insert_common_query

        with patch("pages.analytics.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = [{"prop_id": "query-monthly-trends.n_clicks"}]

            result = insert_common_query(
                None, None, None, 1, None, None, None, None, None
            )

            assert result is not None
            assert "Monthly Sales Trends" in result
            assert "YEAR" in result.upper()
            assert "MONTH" in result.upper()

    def test_insert_common_query_customer_ltv(self):
        """Test inserting customer lifetime value query."""
        from pages.analytics import insert_common_query

        with patch("pages.analytics.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = [{"prop_id": "query-customer-ltv.n_clicks"}]

            result = insert_common_query(
                None, None, None, None, 1, None, None, None, None
            )

            assert result is not None
            assert "Customer Lifetime Value Analysis" in result
            assert "lifetime_value" in result.lower()
            assert "mktsegment" in result.lower()

    def test_insert_common_query_order_frequency(self):
        """Test inserting order frequency query."""
        from pages.analytics import insert_common_query

        with patch("pages.analytics.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = [{"prop_id": "query-order-frequency.n_clicks"}]

            result = insert_common_query(
                None, None, None, None, None, 1, None, None, None
            )

            assert result is not None
            assert "Customer Order Frequency Analysis" in result
            assert "order_frequency_bucket" in result.lower()
            assert "CASE" in result.upper()

    def test_insert_common_query_browse_customers(self):
        """Test inserting browse customers query."""
        from pages.analytics import insert_common_query

        with patch("pages.analytics.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = [{"prop_id": "query-browse-customers.n_clicks"}]

            result = insert_common_query(
                None, None, None, None, None, None, 1, None, None
            )

            assert result is not None
            assert "Browse Customer Table Structure" in result
            assert "C_CUSTKEY" in result.upper()
            assert "C_NAME" in result.upper()

    def test_insert_common_query_browse_orders(self):
        """Test inserting browse orders query."""
        from pages.analytics import insert_common_query

        with patch("pages.analytics.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = [{"prop_id": "query-browse-orders.n_clicks"}]

            result = insert_common_query(
                None, None, None, None, None, None, None, 1, None
            )

            assert result is not None
            assert "Browse Orders Table Structure" in result
            assert "O_ORDERKEY" in result.upper()
            assert "O_TOTALPRICE" in result.upper()

    def test_insert_common_query_table_info(self):
        """Test inserting table information query."""
        from pages.analytics import insert_common_query

        with patch("pages.analytics.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = [{"prop_id": "query-table-info.n_clicks"}]

            result = insert_common_query(
                None, None, None, None, None, None, None, None, 1
            )

            assert result is not None
            assert "Show Information About Available Tables" in result
            assert "information_schema.tables" in result.lower()
            assert "table_schema" in result.lower()

    def test_insert_common_query_no_trigger(self):
        """Test common query insertion with no trigger."""
        from pages.analytics import insert_common_query, no_update

        with patch("pages.analytics.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = []

            result = insert_common_query(
                None, None, None, None, None, None, None, None, None
            )

            assert result == no_update

    def test_insert_common_query_unknown_button(self):
        """Test common query insertion with unknown button ID."""
        from pages.analytics import insert_common_query, no_update

        with patch("pages.analytics.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = [{"prop_id": "unknown-button.n_clicks"}]

            result = insert_common_query(
                1, None, None, None, None, None, None, None, None
            )

            assert result == no_update


class TestDataBrowserCallbacks:
    """Test data browser page callback functions."""

    @patch("pages.data_browser.get_schema_objects")
    def test_load_snowflake_tables_success(self, mock_get_schema):
        """Test successful loading of Snowflake tables."""
        import pandas as pd

        # Mock successful schema objects retrieval
        mock_df = pd.DataFrame(
            {
                "TABLE_NAME": ["customers", "orders", "products"],
                "TABLE_TYPE": ["BASE TABLE", "BASE TABLE", "BASE TABLE"],
                "ROW_COUNT": [1000, 5000, 200],
                "BYTES": [1024000, 5120000, 204800],
                "CREATED": ["2023-01-01", "2023-01-02", "2023-01-03"],
            }
        )
        mock_get_schema.return_value = mock_df

        result = data_browser.load_snowflake_tables("dummy_id")

        assert len(result) == 3
        assert result[0]["table_name"] == "customers"
        assert result[1]["table_name"] == "orders"
        assert result[2]["table_name"] == "products"
        # Check that columns are converted to lowercase
        assert "table_name" in result[0]
        assert "table_type" in result[0]

    @patch("pages.data_browser.get_schema_objects")
    def test_load_snowflake_tables_error_in_dataframe(self, mock_get_schema):
        """Test handling of error column in schema objects."""
        import pandas as pd

        # Mock error response
        mock_df = pd.DataFrame({"error": ["Database connection failed"]})
        mock_get_schema.return_value = mock_df

        result = data_browser.load_snowflake_tables("dummy_id")

        assert len(result) == 1
        assert result[0]["table_name"] == "Error"
        assert result[0]["table_type"] == "N/A"
        assert result[0]["created"] == "Database connection failed"

    @patch(
        "pages.data_browser.get_schema_objects",
        side_effect=Exception("Connection failed"),
    )
    def test_load_snowflake_tables_exception(self, mock_get_schema):
        """Test exception handling in load_snowflake_tables."""
        result = data_browser.load_snowflake_tables("dummy_id")

        assert len(result) == 1
        assert result[0]["table_name"] == "Error"
        assert result[0]["table_type"] == "N/A"
        assert "Failed to load data: Connection failed" in result[0]["created"]

    def test_update_grid_theme_default(self):
        """Test grid theme update with default theme."""
        result = data_browser.update_grid_theme(None)
        assert result == "ag-theme-alpine"

        result = data_browser.update_grid_theme({})
        assert result == "ag-theme-alpine"

    def test_update_grid_theme_dark(self):
        """Test grid theme update with dark theme."""
        theme_data = {"current_theme": "dark"}
        result = data_browser.update_grid_theme(theme_data)
        assert result == "ag-theme-alpine-dark"

    def test_update_grid_theme_light(self):
        """Test grid theme update with light/snowflake theme."""
        theme_data = {"current_theme": "snowflake"}
        result = data_browser.update_grid_theme(theme_data)
        assert result == "ag-theme-alpine"

        theme_data = {"current_theme": "bootstrap"}
        result = data_browser.update_grid_theme(theme_data)
        assert result == "ag-theme-alpine"

    def test_update_table_preview_no_selection(self):
        """Test table preview with no selection."""
        result = data_browser.update_table_preview(None)

        (
            preview_content,
            header,
            alert_style,
            info_content,
            toast_open,
            toast_content,
            loading_style,
        ) = result

        assert preview_content == []
        assert header == "Table Data Preview"
        assert alert_style == {}
        assert toast_open is False
        assert loading_style == {"display": "none"}

    def test_update_table_preview_empty_selection(self):
        """Test table preview with empty selection."""
        result = data_browser.update_table_preview([])

        (
            preview_content,
            header,
            alert_style,
            info_content,
            toast_open,
            toast_content,
            loading_style,
        ) = result

        assert preview_content == []
        assert header == "Table Data Preview"
        assert alert_style == {}
        assert toast_open is False
        assert loading_style == {"display": "none"}

    def test_update_table_preview_invalid_table(self):
        """Test table preview with invalid table selection."""
        selected_rows = [{"invalid_field": "value"}]

        # Provide theme_data to match new signature (dark theme path also OK)
        result = data_browser.update_table_preview(selected_rows)

        (
            preview_content,
            header,
            alert_style,
            info_content,
            toast_open,
            toast_content,
            loading_style,
        ) = result

        assert preview_content == []
        assert header == "Table Data Preview"
        assert toast_open is False
        assert loading_style == {"display": "none"}

    @patch("pages.data_browser.execute_query")
    @patch("pages.data_browser.format_query_results")
    def test_update_table_preview_success(self, mock_format, mock_execute):
        """Test successful table preview."""
        import pandas as pd

        # Mock successful query execution
        mock_df = pd.DataFrame(
            {"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"], "age": [25, 30, 35]}
        )
        mock_execute.return_value = mock_df
        mock_format.return_value = html.Div("Formatted table data")

        selected_rows = [
            {"table_name": "customers", "row_count": 1000, "bytes": 1024000}
        ]

        result = data_browser.update_table_preview(selected_rows)

        (
            preview_content,
            header,
            alert_style,
            info_content,
            toast_open,
            toast_content,
            loading_style,
        ) = result

        assert preview_content is not None
        assert header == "Table Data Preview - CUSTOMERS"
        assert alert_style == {"display": "none"}
        assert toast_open is True
        assert loading_style == {"display": "none"}

        # Verify query was executed correctly
        mock_execute.assert_called_once()
        call_args = mock_execute.call_args[0]
        assert (
            "SELECT * FROM snowflake_sample_data.tpch_sf10.customers LIMIT 100"
            == call_args[0]
        )

        # Verify format_query_results was called
        mock_format.assert_called_once()

    @patch("pages.data_browser.execute_query")
    def test_update_table_preview_query_error(self, mock_execute):
        """Test table preview with query error."""
        import pandas as pd

        # Mock error response
        mock_df = pd.DataFrame({"error": ["Table not found"]})
        mock_execute.return_value = mock_df

        selected_rows = [{"table_name": "nonexistent_table"}]

        result = data_browser.update_table_preview(selected_rows)

        (
            preview_content,
            header,
            alert_style,
            info_content,
            toast_open,
            toast_content,
            loading_style,
        ) = result

        assert "Error loading table data" in str(preview_content)
        assert header == "Table Data Preview - nonexistent_table"
        assert alert_style == {"display": "none"}
        assert toast_open is True
        assert "Failed to load table" in str(toast_content)

    @patch("pages.data_browser.execute_query")
    @patch("pages.data_browser.format_query_results")
    def test_update_table_preview_empty_table(self, mock_format, mock_execute):
        """Test table preview with empty table."""
        import pandas as pd

        # Mock empty dataframe
        mock_df = pd.DataFrame()
        mock_execute.return_value = mock_df

        selected_rows = [{"table_name": "empty_table"}]

        result = data_browser.update_table_preview(selected_rows)

        (
            preview_content,
            header,
            alert_style,
            info_content,
            toast_open,
            toast_content,
            loading_style,
        ) = result

        assert "appears to be empty" in str(preview_content)
        assert header == "Table Data Preview - empty_table"
        assert toast_open is True
        assert "appears to be empty" in str(toast_content)

    @patch(
        "pages.data_browser.execute_query",
        side_effect=Exception("Query execution failed"),
    )
    def test_update_table_preview_exception(self, mock_execute):
        """Test table preview exception handling."""
        selected_rows = [{"table_name": "customers"}]

        result = data_browser.update_table_preview(selected_rows)

        (
            preview_content,
            header,
            alert_style,
            info_content,
            toast_open,
            toast_content,
            loading_style,
        ) = result

        assert "Error loading table preview" in str(preview_content)
        assert header == "Table Data Preview - customers"
        assert toast_open is True
        assert "Error loading customers" in str(toast_content)


class TestAnalyticsAdvancedCallbacks:
    """Test advanced analytics callback scenarios to improve coverage."""

    def test_run_predefined_analysis_products(self):
        """Test predefined analysis for products type."""
        theme_data = {"current_theme": "bootstrap"}
        content, header = analytics.run_predefined_analysis(1, theme_data, "products")

        assert content is not None
        assert "Product Performance Results" == str(header)

    def test_run_predefined_analysis_regions(self):
        """Test predefined analysis for regions type."""
        theme_data = {"current_theme": "bootstrap"}
        content, header = analytics.run_predefined_analysis(1, theme_data, "regions")

        assert content is not None
        assert "Regional Analysis Results" == str(header)

    def test_run_predefined_analysis_dark_theme(self):
        """Test predefined analysis with dark theme template selection."""
        theme_data = {"current_theme": "dark"}
        # initial run
        content, header = analytics.run_predefined_analysis(1, theme_data, "sales")

        assert content is not None
        assert "Sales Analysis Results" == str(header)

        # simulate theme-only restyle without rerun
        from dash import no_update

        with patch("pages.analytics.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = [{"prop_id": "theme-store.data"}]
            content2, header2 = analytics.run_predefined_analysis(
                1, {"current_theme": "snowflake"}, "sales", content
            )
        # no_update for header, content updated or no_update; just ensure no exception and type is acceptable
        assert header2 == no_update or isinstance(header2, str)

    def test_run_predefined_analysis_snowflake_theme(self):
        """Test predefined analysis with snowflake theme template selection."""
        theme_data = {"current_theme": "snowflake"}
        content, header = analytics.run_predefined_analysis(1, theme_data, "sales")

        assert content is not None
        assert "Sales Analysis Results" == str(header)

    def test_run_predefined_analysis_light_theme(self):
        """Test predefined analysis with light theme template selection."""
        theme_data = {"current_theme": "light"}
        content, header = analytics.run_predefined_analysis(1, theme_data, "sales")

        assert content is not None
        assert "Sales Analysis Results" == str(header)


class TestDashboardAdvancedCallbacks:
    """Test advanced dashboard callback scenarios to improve coverage."""

    @patch("pages.dashboard.execute_query")
    def test_update_dashboard_dark_theme_templates(self, mock_exec):
        """Test dashboard update with dark theme template and colors."""
        theme_data = {"current_theme": "dark"}

        with patch("pages.dashboard.px.bar") as mock_bar:
            mock_fig = Mock()
            mock_bar.return_value = mock_fig
            import pandas as pd

            mock_exec.return_value = pd.DataFrame({"REGION": ["N"], "REVENUE": [1]})

            figure, toast_open, toast_children, metrics = dashboard.update_dashboard(
                "revenue", theme_data, None, None, None
            )

            assert figure is not None
            assert not toast_open

    @patch("pages.dashboard.execute_query")
    def test_update_dashboard_snowflake_theme_templates(self, mock_exec):
        """Test dashboard update with snowflake theme template and colors."""
        theme_data = {"current_theme": "snowflake"}

        with patch("pages.dashboard.px.bar") as mock_bar:
            mock_fig = Mock()
            mock_bar.return_value = mock_fig
            import pandas as pd

            mock_exec.return_value = pd.DataFrame({"REGION": ["N"], "REVENUE": [1]})

            figure, toast_open, toast_children, metrics = dashboard.update_dashboard(
                "revenue", theme_data, None, None, None
            )

            assert figure is not None
            assert not toast_open

    @patch("pages.dashboard.execute_query")
    def test_update_dashboard_light_theme_templates(self, mock_exec):
        """Test dashboard update with light theme template and colors."""
        theme_data = {"current_theme": "light"}

        with patch("pages.dashboard.px.bar") as mock_bar:
            mock_fig = Mock()
            mock_bar.return_value = mock_fig
            import pandas as pd

            mock_exec.return_value = pd.DataFrame({"REGION": ["N"], "REVENUE": [1]})

            figure, toast_open, toast_children, metrics = dashboard.update_dashboard(
                "revenue", theme_data, None, None, None
            )

            assert figure is not None
            assert not toast_open

    @patch("pages.dashboard.execute_query")
    def test_update_dashboard_snowflake_marker_colors(self, mock_exec):
        """Test dashboard marker color selection for snowflake theme."""
        theme_data = {"current_theme": "snowflake"}

        with patch("pages.dashboard.px.bar") as mock_bar:
            mock_fig = Mock()
            mock_bar.return_value = mock_fig
            import pandas as pd

            mock_exec.return_value = pd.DataFrame(
                {"QUARTER": ["Q1", "Q2"], "CUSTOMERS": [1, 2]}
            )

            figure, toast_open, toast_children, metrics = dashboard.update_dashboard(
                "customers", theme_data, None, None, None
            )

            assert figure is not None
            assert not toast_open

    @patch("pages.dashboard.execute_query")
    def test_update_dashboard_dark_marker_colors(self, mock_exec):
        """Test dashboard marker color selection for dark theme."""
        theme_data = {"current_theme": "dark"}

        with patch("pages.dashboard.px.bar") as mock_bar:
            mock_fig = Mock()
            mock_bar.return_value = mock_fig
            import pandas as pd

            mock_exec.return_value = pd.DataFrame(
                {"QUARTER": ["Q1", "Q2"], "CUSTOMERS": [1, 2]}
            )

            figure, toast_open, toast_children, metrics = dashboard.update_dashboard(
                "customers", theme_data, None, None, None
            )

            assert figure is not None
            assert not toast_open

    @patch("pages.dashboard.execute_query")
    def test_update_dashboard_light_marker_colors(self, mock_exec):
        """Test dashboard marker color selection for light theme."""
        theme_data = {"current_theme": "light"}

        with patch("pages.dashboard.px.bar") as mock_bar:
            mock_fig = Mock()
            mock_bar.return_value = mock_fig
            import pandas as pd

            mock_exec.return_value = pd.DataFrame(
                {"QUARTER": ["Q1", "Q2"], "CUSTOMERS": [1, 2]}
            )

            figure, toast_open, toast_children, metrics = dashboard.update_dashboard(
                "customers", theme_data, None, None, None
            )

            assert figure is not None
            assert not toast_open


class TestDataBrowserAdvancedCallbacks:
    """Test advanced data browser callback scenarios to improve coverage."""

    def test_grid_theme_additional_scenarios(self):
        """Test grid theme update with additional scenarios for better coverage."""
        # Test with None theme data
        result = data_browser.update_grid_theme(None)
        assert result == "ag-theme-alpine"

    def test_data_browser_overlay_and_class_callbacks(self):
        # overlay theme callbacks
        dark = data_browser.sync_preview_loading_overlay({"current_theme": "dark"})
        light = data_browser.sync_preview_loading_overlay({"current_theme": "light"})
        assert dark["backgroundColor"].startswith("rgba(")
        assert light["backgroundColor"] in ("white",)
        # info overlay
        dark2 = data_browser.sync_info_loading_overlay({"current_theme": "dark"})
        light2 = data_browser.sync_info_loading_overlay({"current_theme": "light"})
        assert dark2["opacity"] == 0.7 and light2["visibility"] == "visible"
        # preview grid class switcher
        assert (
            data_browser.sync_preview_grid_theme({"current_theme": "dark"})
            == "ag-theme-alpine-dark"
        )
        assert (
            data_browser.sync_preview_grid_theme({"current_theme": "light"})
            == "ag-theme-alpine"
        )


class TestAnalyticsMoreCoverage:
    """Add tests to drive analytics.py towards full coverage."""

    @patch("pages.analytics.execute_query")
    def test_sales_error_dataframe(self, mock_exec):
        import pandas as pd

        mock_exec.return_value = pd.DataFrame({"error": ["boom"]})
        content, header = analytics.run_predefined_analysis(
            1, {"current_theme": "dark"}, "sales"
        )
        assert "Error" in str(content)
        assert "Sales Analysis Results" in str(header)

    @patch("pages.analytics.execute_query")
    def test_customers_error_dataframe(self, mock_exec):
        import pandas as pd

        mock_exec.return_value = pd.DataFrame({"error": ["nope"]})
        content, header = analytics.run_predefined_analysis(
            1, {"current_theme": "snowflake"}, "customers"
        )
        assert "Error" in str(content)

    @patch("pages.analytics.execute_query")
    def test_products_error_dataframe(self, mock_exec):
        import pandas as pd

        mock_exec.return_value = pd.DataFrame({"error": ["nope"]})
        content, header = analytics.run_predefined_analysis(
            1, {"current_theme": "light"}, "products"
        )
        assert "Error" in str(content)

    @patch("pages.analytics.execute_query")
    def test_regions_error_dataframe(self, mock_exec):
        import pandas as pd

        mock_exec.return_value = pd.DataFrame({"error": ["nope"]})
        content, header = analytics.run_predefined_analysis(
            1, {"current_theme": "dark"}, "regions"
        )
        assert "Error" in str(content)

    @patch("pages.analytics.execute_query")
    def test_timeseries_error_dataframe(self, mock_exec):
        import pandas as pd

        mock_exec.return_value = pd.DataFrame({"error": ["nope"]})
        content, header = analytics.run_predefined_analysis(
            1, {"current_theme": "dark"}, "timeseries"
        )
        assert "Error" in str(content)

    @patch("pages.analytics.execute_query")
    def test_sales_success_path(self, mock_exec):
        import pandas as pd

        df = pd.DataFrame(
            {"MONTH": ["2020-01", "2020-02"], "SALES": [100, 200], "TARGET": [150, 150]}
        )
        mock_exec.return_value = df
        content, header = analytics.run_predefined_analysis(
            1, {"current_theme": "snowflake"}, "sales"
        )
        assert "Sales Analysis Results" == str(header)

    @patch("pages.analytics.execute_query")
    def test_customers_success_path(self, mock_exec):
        import pandas as pd

        df = pd.DataFrame({"SEGMENT": ["A", "B"], "CNT": [10, 5]})
        mock_exec.return_value = df
        content, header = analytics.run_predefined_analysis(
            1, {"current_theme": "dark"}, "customers"
        )
        assert "Customer Segmentation Results" == str(header)

    @patch("pages.analytics.execute_query")
    def test_products_success_path(self, mock_exec):
        import pandas as pd

        df = pd.DataFrame(
            {"PRODUCT": ["P1", "P2"], "REVENUE": [1000, 2000], "UNITS": [10, 20]}
        )
        mock_exec.return_value = df
        content, header = analytics.run_predefined_analysis(
            1, {"current_theme": "snowflake"}, "products"
        )
        assert "Product Performance Results" == str(header)

    @patch("pages.analytics.execute_query")
    def test_regions_success_path(self, mock_exec):
        import pandas as pd

        df = pd.DataFrame({"REGION": ["N", "S"], "REVENUE": [1000, 500]})
        mock_exec.return_value = df
        content, header = analytics.run_predefined_analysis(
            1, {"current_theme": "light"}, "regions"
        )
        assert "Regional Analysis Results" == str(header)

    @patch("pages.analytics.execute_query")
    def test_timeseries_success_path(self, mock_exec):
        import pandas as pd

        df = pd.DataFrame({"MONTH": ["2020-01", "2020-02"], "REVENUE": [100, 200]})
        mock_exec.return_value = df
        content, header = analytics.run_predefined_analysis(
            1, {"current_theme": "dark"}, "timeseries"
        )
        assert "Time Series Analysis Results" == str(header)

    def test_theme_sync_helpers(self):
        # query results wrapper theme
        assert (
            analytics.sync_query_results_theme({"current_theme": "dark"})
            == "ag-theme-alpine-dark"
        )
        assert (
            analytics.sync_query_results_theme({"current_theme": "light"})
            == "ag-theme-alpine"
        )
        # analysis wrapper class
        assert (
            analytics.sync_analysis_results_theme({"current_theme": "dark"})
            == "dark-analytics"
        )
        assert analytics.sync_analysis_results_theme({"current_theme": "light"}) == ""
        # overlay styles
        dark_overlay = analytics.update_query_loading_overlay_theme(
            {"current_theme": "dark"}
        )
        light_overlay = analytics.update_query_loading_overlay_theme(
            {"current_theme": "light"}
        )
        assert dark_overlay["backgroundColor"].startswith("rgba(")
        assert light_overlay["backgroundColor"] in ("white",)

    def test_theme_restyle_no_existing_content(self):
        from dash import no_update

        with patch("pages.analytics.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = [{"prop_id": "theme-store.data"}]
            content, header = analytics.run_predefined_analysis(
                1, {"current_theme": "dark"}, "sales", None
            )
        assert content == no_update
        assert header == no_update

    def test_theme_restyle_children_not_list(self):
        from dash import no_update

        comp = html.Div(html.Div("no-graph-here"))
        with patch("pages.analytics.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = [{"prop_id": "theme-store.data"}]
            content, header = analytics.run_predefined_analysis(
                1, {"current_theme": "dark"}, "sales", comp
            )
        # Unable to restyle, leaves unchanged
        assert content == no_update
        assert header == no_update

    def test_theme_restyle_children_list_first_not_graph(self):
        from dash import no_update

        comp = [html.Div("not-a-graph"), html.Div("details")]  # first lacks .figure
        with patch("pages.analytics.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = [{"prop_id": "theme-store.data"}]
            content, header = analytics.run_predefined_analysis(
                1, {"current_theme": "dark"}, "sales", comp
            )
        assert content == no_update
        assert header == no_update

    def test_theme_restyle_success_updates_graph(self):
        # Build content with a real graph to restyle
        from dash import dcc

        initial_fig = {"data": [], "layout": {}}
        comp = html.Div([dcc.Graph(figure=initial_fig), html.Div("details")])
        with patch("pages.analytics.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = [{"prop_id": "theme-store.data"}]
            content, header = analytics.run_predefined_analysis(
                1, {"current_theme": "dark"}, "sales", comp
            )
        # Should return updated content (not no_update)
        from dash import no_update

        assert content != no_update
        assert header == no_update

    def test_theme_restyle_exception_path(self):
        # First child has invalid figure to trigger exception
        class Bad:
            def __init__(self):
                self.figure = object()

        bad = Bad()
        comp = [bad, html.Div("details")]
        from dash import no_update

        with patch("pages.analytics.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = [{"prop_id": "theme-store.data"}]
            content, header = analytics.run_predefined_analysis(
                1, {"current_theme": "dark"}, "sales", comp
            )
        assert content == no_update
        assert header == no_update

    def test_theme_restyle_outer_exception(self):
        # Pass a theme_data without .get to trigger outer except
        from dash import no_update
        from dash import dcc

        comp = html.Div([dcc.Graph(figure={}), html.Div("details")])

        class NoGet:
            pass

        with patch("pages.analytics.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = [{"prop_id": "theme-store.data"}]
            content, header = analytics.run_predefined_analysis(
                1, NoGet(), "sales", comp
            )
        assert content == no_update
        assert header == no_update

        # Test with empty theme data
        result = data_browser.update_grid_theme({})
        assert result == "ag-theme-alpine"

        # Test with missing current_theme key
        result = data_browser.update_grid_theme({"other_key": "value"})
        assert result == "ag-theme-alpine"

        # Test with dark theme
        result = data_browser.update_grid_theme({"current_theme": "dark"})
        assert result == "ag-theme-alpine-dark"

        # Test with light theme (should return alpine, not alpine-dark)
        result = data_browser.update_grid_theme({"current_theme": "light"})
        assert result == "ag-theme-alpine"

        # Test with snowflake theme (should return alpine, not alpine-dark)
        result = data_browser.update_grid_theme({"current_theme": "snowflake"})
        assert result == "ag-theme-alpine"


class TestDashboardYearAndSQL:
    """Additional tests for dashboard year options, theme restyle, and SQL assembly."""

    @patch("pages.dashboard.execute_query")
    def test_load_year_options_success_sorted_ints(self, mock_exec):
        import pandas as pd

        mock_exec.return_value = pd.DataFrame({"YEAR": [2021, 2019, 2020]})

        options = dashboard.load_year_options("revenue")
        assert options == [
            {"label": "2019", "value": 2019},
            {"label": "2020", "value": 2020},
            {"label": "2021", "value": 2021},
        ]

    @patch("pages.dashboard.execute_query")
    def test_load_year_options_error_or_empty(self, mock_exec):
        import pandas as pd

        # Error path
        mock_exec.return_value = pd.DataFrame({"error": ["failed"]})
        assert dashboard.load_year_options("revenue") == []

        # Empty path
        mock_exec.return_value = pd.DataFrame()
        assert dashboard.load_year_options("revenue") == []

    @patch("pages.dashboard.execute_query", side_effect=Exception("year fail"))
    def test_load_year_options_exception_branch(self, _mock_exec):
        assert dashboard.load_year_options("revenue") == []

    @patch("pages.dashboard.execute_query")
    def test_theme_only_restyle_does_not_requery(self, mock_exec):
        # Ensure execute_query is not called when only theme changed
        from pages.dashboard import update_dashboard

        # Simulate prior state figure and metrics
        fig_state = {}
        metrics_state = html.Div("old metrics")

        theme_data = {"current_theme": "dark"}

        with patch("pages.dashboard.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = [{"prop_id": "theme-store.data"}]
            figure, toast_open, toast_children, metrics = update_dashboard(
                "revenue", theme_data, None, fig_state, metrics_state
            )

        mock_exec.assert_not_called()
        assert figure is not None
        assert not toast_open
        assert metrics is not None

    @patch("pages.dashboard.execute_query")
    def test_revenue_sql_contains_per_order_subquery_and_year_filter(self, mock_exec):
        import pandas as pd

        mock_exec.return_value = pd.DataFrame({"REGION": ["X"], "REVENUE": [1]})

        figure, toast_open, toast_children, metrics = dashboard.update_dashboard(
            "revenue", {"current_theme": "snowflake"}, 2020, None, None
        )

        # Verify SQL used
        sql = mock_exec.call_args[0][0]
        assert "JOIN (SELECT l.L_ORDERKEY" in sql
        assert "DATE_PART('year', o.O_ORDERDATE)" in sql
        assert "WITH order_revenue" not in sql
        assert "GROUP BY 1 ORDER BY REVENUE DESC" in sql
        assert figure is not None and not toast_open and metrics is not None

    @patch("pages.dashboard.execute_query")
    def test_products_sql_contains_year_filter_when_provided(self, mock_exec):
        import pandas as pd

        mock_exec.return_value = pd.DataFrame({"PRODUCT": ["A"], "UNITS": [10]})

        _ = dashboard.update_dashboard(
            "products", {"current_theme": "snowflake"}, 2018, None, None
        )

        sql = mock_exec.call_args[0][0]
        assert "JOIN snowflake_sample_data.tpch_sf10.orders o" in sql
        assert "DATE_PART('year', o.O_ORDERDATE)" in sql

    def test_format_humanized_number_exception_branch(self):
        from pages.dashboard import format_humanized_number

        class X: ...

        assert format_humanized_number(X(), True) == "$0"

    @patch("pages.dashboard.execute_query", side_effect=Exception("boom"))
    @patch("pages.dashboard.px.bar")
    def test_dashboard_exception_handler(self, mock_bar, _mock_exec):
        mock_fig = Mock()
        mock_bar.return_value = mock_fig
        fig, toast_open, toast_children, metrics = dashboard.update_dashboard(
            "revenue", {"current_theme": "snowflake"}, None, None, None
        )
        assert toast_open is True
        assert "boom" in str(toast_children)
        assert fig == mock_fig

    @patch("pages.dashboard.execute_query")
    def test_revenue_empty_dataframe_path(self, mock_exec):
        import pandas as pd

        mock_exec.return_value = pd.DataFrame()
        fig, toast_open, toast_children, metrics = dashboard.update_dashboard(
            "revenue", {"current_theme": "snowflake"}, None, None, None
        )
        assert toast_open is True

    @patch("pages.dashboard.execute_query")
    def test_customers_error_dataframe_path(self, mock_exec):
        import pandas as pd

        mock_exec.return_value = pd.DataFrame({"error": ["x"]})
        fig, toast_open, toast_children, metrics = dashboard.update_dashboard(
            "customers", {"current_theme": "snowflake"}, None, None, None
        )
        assert toast_open is True

    @patch("pages.dashboard.execute_query")
    def test_sales_empty_dataframe_path(self, mock_exec):
        import pandas as pd

        mock_exec.return_value = pd.DataFrame()
        fig, toast_open, toast_children, metrics = dashboard.update_dashboard(
            "sales", {"current_theme": "snowflake"}, None, None, None
        )
        assert toast_open is True

    @patch("pages.dashboard.execute_query")
    def test_products_error_dataframe_path(self, mock_exec):
        import pandas as pd

        mock_exec.return_value = pd.DataFrame({"error": ["err"]})
        fig, toast_open, toast_children, metrics = dashboard.update_dashboard(
            "products", {"current_theme": "snowflake"}, None, None, None
        )
        assert toast_open is True

    @patch("pages.dashboard.execute_query")
    def test_customers_year_filter_success(self, mock_exec):
        import pandas as pd

        mock_exec.return_value = pd.DataFrame({"QUARTER": ["Q1"], "CUSTOMERS": [1]})
        fig, toast_open, toast_children, metrics = dashboard.update_dashboard(
            "customers", {"current_theme": "dark"}, 2020, None, None
        )
        assert not toast_open

    @patch("pages.dashboard.execute_query")
    def test_sales_year_filter_success(self, mock_exec):
        import pandas as pd

        mock_exec.return_value = pd.DataFrame({"MONTH": ["2020-01"], "SALES": [1]})
        fig, toast_open, toast_children, metrics = dashboard.update_dashboard(
            "sales", {"current_theme": "dark"}, 2020, None, None
        )
        assert not toast_open

    @patch("pages.dashboard.execute_query", side_effect=Exception("oops"))
    @patch("pages.dashboard.px.bar")
    def test_dashboard_exception_generic(self, mock_bar, _mock_exec):
        mock_bar.return_value = Mock()
        fig, toast_open, toast_children, metrics = dashboard.update_dashboard(
            "sales", {"current_theme": "snowflake"}, None, None, None
        )
        assert toast_open is True

    def test_format_humanized_number(self):
        from pages.dashboard import format_humanized_number

        assert format_humanized_number(999) == "999"
        assert format_humanized_number(1_200) == "1.2K"
        assert format_humanized_number(2_000_000) == "2M"
        assert format_humanized_number(2_500_000_000) == "2.5B"
        assert format_humanized_number(1530, True) == "$1.5K"
        assert (
            format_humanized_number(-2_400_000, True) == "-$2.4M"
            or format_humanized_number(-2_400_000, True) == "$-2.4M"
        )

    @patch("pages.dashboard.execute_query")
    def test_theme_only_restyle_fallback(self, mock_exec):
        from pages.dashboard import update_dashboard

        # Intentionally pass an invalid figure state to trigger fallback path
        fig_state = {"unexpected": "shape"}
        metrics_state = html.Div("existing")
        with patch("pages.dashboard.dash.callback_context") as mock_ctx:
            mock_ctx.triggered = [{"prop_id": "theme-store.data"}]
            fig, toast_open, toast_children, metrics = update_dashboard(
                "revenue", {"current_theme": "dark"}, None, fig_state, metrics_state
            )
        assert toast_open is False
        assert metrics is not None

    @patch("pages.dashboard.execute_query")
    @patch("pages.dashboard.px.bar")
    def test_metrics_include_year_label(self, mock_bar, mock_exec):
        import pandas as pd

        mock_bar.return_value = Mock()
        mock_exec.return_value = pd.DataFrame(
            {"REGION": ["N"], "REVENUE": [1_500_000_000]}
        )

        _, toast_open, _, metrics = dashboard.update_dashboard(
            "revenue", {"current_theme": "light"}, 2021, None, None
        )

        assert not toast_open
        assert "Year: 2021" in str(metrics)
