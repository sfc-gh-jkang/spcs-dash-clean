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

    @patch("pages.dashboard.px.bar")
    def test_update_dashboard_revenue(self, mock_bar):
        """Test dashboard update with revenue selection."""
        # Mock plotly figure
        mock_fig = Mock()
        mock_bar.return_value = mock_fig

        theme_data = {"current_theme": "bootstrap"}

        # Test the callback function directly
        figure, toast_open, toast_children, metrics = dashboard.update_dashboard(
            "revenue", theme_data
        )

        # Verify the response
        assert figure is not None
        assert not toast_open  # No error
        assert metrics is not None
        mock_bar.assert_called_once()

    @patch("pages.dashboard.px.bar")
    def test_update_dashboard_customers(self, mock_bar):
        """Test dashboard update with customers selection."""
        # Mock plotly figure
        mock_fig = Mock()
        mock_bar.return_value = mock_fig

        theme_data = {"current_theme": "bootstrap"}

        figure, toast_open, toast_children, metrics = dashboard.update_dashboard(
            "customers", theme_data
        )

        assert figure is not None
        assert not toast_open
        assert metrics is not None

    @patch("pages.dashboard.px.bar")
    def test_update_dashboard_sales(self, mock_bar):
        """Test dashboard update with sales selection."""
        mock_fig = Mock()
        mock_bar.return_value = mock_fig

        theme_data = {"current_theme": "bootstrap"}

        figure, toast_open, toast_children, metrics = dashboard.update_dashboard(
            "sales", theme_data
        )

        assert figure is not None
        assert not toast_open
        assert metrics is not None

    @patch("pages.dashboard.px.bar")
    def test_update_dashboard_products(self, mock_bar):
        """Test dashboard update with products selection."""
        mock_fig = Mock()
        mock_bar.return_value = mock_fig

        theme_data = {"current_theme": "bootstrap"}

        figure, toast_open, toast_children, metrics = dashboard.update_dashboard(
            "products", theme_data
        )

        assert figure is not None
        assert not toast_open
        assert metrics is not None

    def test_update_dashboard_exception_handling(self):
        """Test dashboard callback exception handling."""
        theme_data = {"current_theme": "bootstrap"}

        # Test with invalid selected_value to trigger exception path
        with patch(
            "pages.dashboard.pd.DataFrame", side_effect=Exception("Test error")
        ):
            with patch("pages.dashboard.px.bar") as mock_bar:
                # Mock the error case figure for the exception handler
                mock_error_fig = Mock()
                mock_bar.return_value = mock_error_fig

                figure, toast_open, toast_children, metrics = (
                    dashboard.update_dashboard("revenue", theme_data)
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
            mock_df, max_rows=1000, grid_id="analytics-query-results-grid"
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

    @patch("pages.analytics.pd.DataFrame", side_effect=Exception("Analysis error"))
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
        content, header = analytics.run_predefined_analysis(1, theme_data, "sales")

        assert content is not None
        assert "Sales Analysis Results" == str(header)

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

    def test_update_dashboard_dark_theme_templates(self):
        """Test dashboard update with dark theme template and colors."""
        theme_data = {"current_theme": "dark"}

        with patch("pages.dashboard.px.bar") as mock_bar:
            mock_fig = Mock()
            mock_bar.return_value = mock_fig

            figure, toast_open, toast_children, metrics = dashboard.update_dashboard(
                "revenue", theme_data
            )

            assert figure is not None
            assert not toast_open

    def test_update_dashboard_snowflake_theme_templates(self):
        """Test dashboard update with snowflake theme template and colors."""
        theme_data = {"current_theme": "snowflake"}

        with patch("pages.dashboard.px.bar") as mock_bar:
            mock_fig = Mock()
            mock_bar.return_value = mock_fig

            figure, toast_open, toast_children, metrics = dashboard.update_dashboard(
                "revenue", theme_data
            )

            assert figure is not None
            assert not toast_open

    def test_update_dashboard_light_theme_templates(self):
        """Test dashboard update with light theme template and colors."""
        theme_data = {"current_theme": "light"}

        with patch("pages.dashboard.px.bar") as mock_bar:
            mock_fig = Mock()
            mock_bar.return_value = mock_fig

            figure, toast_open, toast_children, metrics = dashboard.update_dashboard(
                "revenue", theme_data
            )

            assert figure is not None
            assert not toast_open

    def test_update_dashboard_snowflake_marker_colors(self):
        """Test dashboard marker color selection for snowflake theme."""
        theme_data = {"current_theme": "snowflake"}

        with patch("pages.dashboard.px.bar") as mock_bar:
            mock_fig = Mock()
            mock_bar.return_value = mock_fig

            figure, toast_open, toast_children, metrics = dashboard.update_dashboard(
                "customers", theme_data
            )

            assert figure is not None
            assert not toast_open

    def test_update_dashboard_dark_marker_colors(self):
        """Test dashboard marker color selection for dark theme."""
        theme_data = {"current_theme": "dark"}

        with patch("pages.dashboard.px.bar") as mock_bar:
            mock_fig = Mock()
            mock_bar.return_value = mock_fig

            figure, toast_open, toast_children, metrics = dashboard.update_dashboard(
                "customers", theme_data
            )

            assert figure is not None
            assert not toast_open

    def test_update_dashboard_light_marker_colors(self):
        """Test dashboard marker color selection for light theme."""
        theme_data = {"current_theme": "light"}

        with patch("pages.dashboard.px.bar") as mock_bar:
            mock_fig = Mock()
            mock_bar.return_value = mock_fig

            figure, toast_open, toast_children, metrics = dashboard.update_dashboard(
                "customers", theme_data
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
