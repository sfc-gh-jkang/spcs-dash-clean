"""
Data Browser page - Browse and explore Snowflake tables.
"""

import dash
from dash import html, dcc, Output, Input, callback
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import logging

from components.layout import create_page_container
from utils.snowflake_utils import (
    get_schema_objects,
    format_query_results,
    execute_query,
)

# Register this page
dash.register_page(
    __name__,
    path="/data-browser",
    name="Data Browser",
    title="Data Browser - Snowflake Analytics",
)

logger = logging.getLogger(__name__)


def layout():
    """Data browser page layout."""
    return create_page_container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.I(className="fas fa-snowflake me-2"),
                                            "Snowflake Data Catalog (TPCH_SF10)",
                                        ],
                                        id="tables-header",
                                    ),
                                    dbc.CardBody(
                                        [
                                            dbc.Spinner(
                                                dag.AgGrid(
                                                    id="tables-grid",
                                                    rowData=[],
                                                    columnDefs=[
                                                        {
                                                            "headerName": "Table Name",
                                                            "field": "table_name",
                                                            "sortable": True,
                                                            "filter": True,
                                                        },
                                                        {
                                                            "headerName": "Table Type",
                                                            "field": "table_type",
                                                            "sortable": True,
                                                            "filter": True,
                                                        },
                                                        {
                                                            "headerName": "Row Count",
                                                            "field": "row_count",
                                                            "sortable": True,
                                                            "filter": True,
                                                            "type": "numericColumn",
                                                        },
                                                        {
                                                            "headerName": "Size (Bytes)",
                                                            "field": "bytes",
                                                            "sortable": True,
                                                            "filter": True,
                                                            "type": "numericColumn",
                                                        },
                                                        {
                                                            "headerName": "Created",
                                                            "field": "created",
                                                            "sortable": True,
                                                            "filter": True,
                                                        },
                                                    ],
                                                    className="ag-theme-alpine",
                                                    style={"height": "400px"},
                                                    dashGridOptions={
                                                        "pagination": True,
                                                        "paginationPageSize": 10,
                                                        "defaultColDef": {
                                                            "resizable": True,
                                                            "sortable": True,
                                                            "filter": True,
                                                        },
                                                        "rowSelection": "single",
                                                        "suppressRowClickSelection": False,
                                                    },
                                                ),
                                                color="primary",
                                                type="border",
                                            )
                                        ]
                                    ),
                                ],
                                id="tables-card",
                                className="shadow-sm",
                            )
                        ],
                        md=12,
                    )
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.I(className="fas fa-table me-2"),
                                            html.Span(
                                                "Table Data Preview",
                                                id="table-preview-header",
                                            ),
                                            # Loading indicator in header
                                            html.Div(
                                                [
                                                    dbc.Spinner(
                                                        size="sm",
                                                        color="primary",
                                                        id="header-loading-spinner",
                                                    ),
                                                    html.Small(
                                                        " Loading...",
                                                        id="header-loading-text",
                                                        className="text-muted ms-2",
                                                    ),
                                                ],
                                                id="header-loading-container",
                                                style={"display": "none"},
                                                className="float-end",
                                            ),
                                        ],
                                        className="d-flex justify-content-between align-items-center",
                                    ),
                                    dbc.CardBody(
                                        [
                                            dbc.Alert(
                                                "Select a table from the catalog above to preview its data.",
                                                color="info",
                                                id="no-table-alert",
                                            ),
                                            # Loading spinner for table preview
                                            dcc.Loading(
                                                id="table-preview-loading",
                                                type="default",
                                                color="#29B5E8",
                                                children=[
                                                    html.Div(id="table-preview-content")
                                                ],
                                                # Will be overridden based on theme by a callback
                                                overlay_style={
                                                    "visibility": "visible",
                                                    "opacity": 0.7,
                                                    "backgroundColor": "white",
                                                },
                                            ),
                                        ]
                                    ),
                                ],
                                id="preview-card",
                                className="shadow-sm",
                            )
                        ],
                        md=12,
                    )
                ],
                className="mt-4",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.I(className="fas fa-info-circle me-2"),
                                            "Table Information",
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            # Loading spinner for table information
                                            dcc.Loading(
                                                id="table-info-loading",
                                                type="circle",
                                                color="#29B5E8",
                                                children=[
                                                    html.Div(
                                                        id="table-info-content",
                                                        children=[
                                                            html.P(
                                                                "Select a table to view detailed information.",
                                                                className="text-muted",
                                                            )
                                                        ],
                                                    )
                                                ],
                                                # Will be overridden based on theme by a callback
                                                overlay_style={
                                                    "visibility": "visible",
                                                    "opacity": 0.7,
                                                    "backgroundColor": "white",
                                                },
                                            )
                                        ]
                                    ),
                                ],
                                className="shadow-sm",
                            )
                        ],
                        md=12,
                    )
                ],
                className="mt-4",
            ),
            # Toast notification for table selection feedback
            dbc.Toast(
                id="table-selection-toast",
                header="Table Selected",
                is_open=False,
                dismissable=True,
                duration=3000,
                icon="success",
                style={
                    "position": "fixed",
                    "top": 66,
                    "right": 10,
                    "width": 350,
                    "z-index": 1999,
                },
            ),
        ],
        "Data Browser",
        "databrowser",
    )


@callback(
    Output("tables-grid", "rowData"),
    Input("tables-grid", "id"),
    prevent_initial_call=False,
)
def load_snowflake_tables(_):
    """Load Snowflake table data into the AG Grid."""
    try:
        logger.info("Loading Snowflake table data for AG Grid")
        df = get_schema_objects()
        if "error" in df.columns:
            logger.warning("Error in Snowflake data retrieval for AG Grid")
            return [
                {
                    "table_name": "Error",
                    "table_type": "N/A",
                    "row_count": 0,
                    "bytes": 0,
                    "created": df["error"].iloc[0],
                }
            ]

        # Convert DataFrame to list of dictionaries for AG Grid
        df.columns = df.columns.str.lower()
        logger.info(f"Successfully loaded {len(df)} rows for AG Grid")
        return df.to_dict("records")

    except Exception as e:
        logger.error(f"Failed to load AG Grid data: {str(e)}")
        return [
            {
                "table_name": "Error",
                "table_type": "N/A",
                "row_count": 0,
                "bytes": 0,
                "created": f"Failed to load data: {str(e)}",
            }
        ]


@callback(
    Output("tables-grid", "className"),
    Input("theme-store", "data"),
    prevent_initial_call=False,
)
def update_grid_theme(theme_data):
    """Update AG Grid theme based on current theme."""
    if not theme_data:
        return "ag-theme-alpine"

    current_theme = theme_data.get("current_theme", "snowflake")

    if current_theme == "dark":
        return "ag-theme-alpine-dark"
    else:
        return "ag-theme-alpine"


@callback(
    Output("table-preview-loading", "overlay_style"),
    Input("theme-store", "data"),
    prevent_initial_call=False,
)
def sync_preview_loading_overlay(theme_data):
    """Match preview loading overlay to current theme (dark vs light)."""
    is_dark = bool(theme_data and theme_data.get("current_theme") == "dark")
    return {
        "visibility": "visible",
        "opacity": 0.7,
        "backgroundColor": "rgba(15, 23, 42, 0.85)" if is_dark else "white",
    }


@callback(
    Output("table-preview-wrapper", "className"),
    Input("theme-store", "data"),
    prevent_initial_call=False,
)
def sync_preview_grid_theme(theme_data):
    """Switch preview grid theme class without reloading its data."""
    is_dark = bool(theme_data and theme_data.get("current_theme") == "dark")
    return "ag-theme-alpine-dark" if is_dark else "ag-theme-alpine"


@callback(
    Output("table-info-loading", "overlay_style"),
    Input("theme-store", "data"),
    prevent_initial_call=False,
)
def sync_info_loading_overlay(theme_data):
    """Match info loading overlay to current theme (dark vs light)."""
    is_dark = bool(theme_data and theme_data.get("current_theme") == "dark")
    return {
        "visibility": "visible",
        "opacity": 0.7,
        "backgroundColor": "rgba(15, 23, 42, 0.85)" if is_dark else "white",
    }


@callback(
    [
        Output("table-preview-content", "children"),
        Output("table-preview-header", "children"),
        Output("no-table-alert", "style"),
        Output("table-info-content", "children"),
        Output("table-selection-toast", "is_open"),
        Output("table-selection-toast", "children"),
        Output("header-loading-container", "style"),
    ],
    Input("tables-grid", "selectedRows"),
    prevent_initial_call=True,
)
def update_table_preview(selected_rows):
    """Update table preview when a table is selected."""
    if not selected_rows or len(selected_rows) == 0:
        return (
            [],
            "Table Data Preview",
            {},
            [
                html.P(
                    "Select a table from the catalog above to preview its data.",
                    className="text-muted",
                )
            ],
            False,
            "",
            {"display": "none"},
        )

    # Get the first selected row
    selected_table = selected_rows[0]
    table_name = selected_table.get("table_name")

    if not table_name:
        return (
            [],
            "Table Data Preview",
            {},
            [html.P("Invalid table selection.", className="text-muted")],
            False,
            "",
            {"display": "none"},
        )

    try:
        logger.info(f"Loading preview for table: {table_name}")

        # Create a safe SELECT query for the table preview
        preview_query = (
            f"SELECT * FROM snowflake_sample_data.tpch_sf10.{table_name} LIMIT 100"
        )

        # Use the secure execute_query function
        df = execute_query(preview_query, max_rows=100)

        if "error" in df.columns:
            error_content = dbc.Alert(
                f"Error loading table data: {df['error'].iloc[0]}", color="danger"
            )
            toast_content = f"❌ Failed to load table {table_name}"
            return (
                error_content,
                f"Table Data Preview - {table_name}",
                {"display": "none"},
                [html.P("Error loading table information.", className="text-danger")],
                True,
                toast_content,
                {"display": "none"},
            )

        # Use the reusable format_query_results function with AG Grid
        if len(df) > 0:
            # Render grid without embedding theme class; container will receive theme
            preview_content = format_query_results(
                df,
                max_rows=100,
                grid_id=f"table-preview-grid-{table_name}",
                theme="alpine",
                apply_theme_on_container=True,
            )

            # Wrap with a stable wrapper whose class changes with theme only
            preview_content = html.Div(
                preview_content, id="table-preview-wrapper", className="ag-theme-alpine"
            )

            # Create enhanced table information
            table_info = [
                html.Div(
                    [
                        html.H5(f"📊 Table: {table_name}", className="mb-3"),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            [
                                                dbc.CardBody(
                                                    [
                                                        html.H6(
                                                            "📈 Statistics",
                                                            className="card-title",
                                                        ),
                                                        html.P(
                                                            [
                                                                html.Strong(
                                                                    "Preview rows: "
                                                                ),
                                                                f"{len(df):,}",
                                                                html.Br(),
                                                                html.Strong(
                                                                    "Total columns: "
                                                                ),
                                                                f"{len(df.columns):,}",
                                                                html.Br(),
                                                                html.Strong(
                                                                    "Total rows: "
                                                                ),
                                                                f"{selected_table.get('row_count', 'Unknown'):,}"
                                                                if selected_table.get(
                                                                    "row_count"
                                                                )
                                                                else "Unknown",
                                                                html.Br(),
                                                                html.Strong("Size: "),
                                                                f"{selected_table.get('bytes', 'Unknown')} bytes"
                                                                if selected_table.get(
                                                                    "bytes"
                                                                )
                                                                else "Unknown",
                                                            ]
                                                        ),
                                                    ]
                                                )
                                            ],
                                            className="h-100",
                                        )
                                    ],
                                    md=6,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            [
                                                dbc.CardBody(
                                                    [
                                                        html.H6(
                                                            "🏷️ Column Types",
                                                            className="card-title",
                                                        ),
                                                        html.Div(
                                                            [
                                                                dbc.Badge(
                                                                    f"{col}: {str(df[col].dtype)}",
                                                                    color="secondary",
                                                                    className="me-1 mb-1",
                                                                )
                                                                for col in df.columns[
                                                                    :8
                                                                ]  # Show first 8 columns
                                                            ]
                                                            + (
                                                                [
                                                                    dbc.Badge(
                                                                        f"... and {len(df.columns) - 8} more",
                                                                        color="light",
                                                                        className="me-1 mb-1",
                                                                    )
                                                                ]
                                                                if len(df.columns) > 8
                                                                else []
                                                            )
                                                        ),
                                                    ]
                                                )
                                            ],
                                            className="h-100",
                                        )
                                    ],
                                    md=6,
                                ),
                            ],
                            className="mb-3",
                        ),
                        # Query suggestion
                        dbc.Alert(
                            [
                                html.I(className="fas fa-lightbulb me-2"),
                                html.Strong("💡 Tip: "),
                                "Try this query in Analytics: ",
                                html.Code(
                                    f"SELECT * FROM snowflake_sample_data.tpch_sf10.{table_name} LIMIT 50",
                                    className="ms-1",
                                ),
                            ],
                            color="info",
                            className="mb-0",
                        ),
                    ]
                )
            ]

            # Create toast notification content
            toast_content = html.Div(
                [
                    html.I(className="fas fa-check-circle me-2"),
                    f"Successfully loaded {table_name.upper()} ({len(df):,} rows)",
                ]
            )

            return (
                preview_content,
                f"Table Data Preview - {table_name.upper()}",
                {"display": "none"},
                table_info,
                True,
                toast_content,
                {"display": "none"},
            )
        else:
            empty_content = dbc.Alert(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    f"Table {table_name} appears to be empty or no data is accessible.",
                ],
                color="warning",
            )
            toast_content = f"⚠️ Table {table_name} appears to be empty"
            return (
                empty_content,
                f"Table Data Preview - {table_name}",
                {"display": "none"},
                [
                    html.P(
                        f"No data available in table {table_name}.",
                        className="text-warning",
                    )
                ],
                True,
                toast_content,
                {"display": "none"},
            )

    except Exception as e:
        logger.error(f"Error loading table preview for {table_name}: {e}")
        error_content = dbc.Alert(
            [
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Error loading table preview: {str(e)}",
            ],
            color="danger",
        )
        toast_content = f"❌ Error loading {table_name}: {str(e)[:50]}..."
        return (
            error_content,
            f"Table Data Preview - {table_name}",
            {"display": "none"},
            [html.P("Error loading table information.", className="text-danger")],
            True,
            toast_content,
            {"display": "none"},
        )
