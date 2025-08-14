"""
Dashboard page - Main analytics and visualization page.
"""

import dash
from dash import html, dcc, Output, Input, State, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from typing import Tuple, Dict, Any
import logging

from components.layout import create_page_container
from utils.snowflake_utils import execute_query

# Register this page
dash.register_page(
    __name__, path="/", name="Dashboard", title="Dashboard - Snowflake Analytics"
)

logger = logging.getLogger(__name__)


def layout():
    """Dashboard page layout."""
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
                                            html.I(className="fas fa-database me-2"),
                                            "Data Source Selection",
                                        ],
                                        id="data-selection-header",
                                    ),
                                    dbc.CardBody(
                                        [
                                            dbc.Label(
                                                "Select Sample Data:",
                                                className="mb-2",
                                                html_for="sample-dropdown",
                                            ),
                                            dcc.Dropdown(
                                                id="sample-dropdown",
                                                options=[
                                                    {
                                                        "label": "Revenue by Region",
                                                        "value": "revenue",
                                                    },
                                                    {
                                                        "label": "Customer Growth",
                                                        "value": "customers",
                                                    },
                                                    {
                                                        "label": "Sales Trends",
                                                        "value": "sales",
                                                    },
                                                    {
                                                        "label": "Product Performance",
                                                        "value": "products",
                                                    },
                                                ],
                                                value="revenue",
                                                clearable=False,
                                                className="mb-3",
                                            ),
                                            dbc.Label(
                                                "Year (optional):",
                                                className="mb-2",
                                                html_for="year-dropdown",
                                            ),
                                            dcc.Dropdown(
                                                id="year-dropdown",
                                                options=[],
                                                value=None,
                                                clearable=True,
                                                placeholder="Select Year",
                                            ),
                                        ]
                                    ),
                                ],
                                id="data-selection-card",
                                className="mb-4 shadow-sm",
                            )
                        ],
                        md=4,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.I(className="fas fa-chart-line me-2"),
                                            "Analytics & Insights",
                                        ],
                                        id="visualization-header",
                                    ),
                                    dbc.CardBody(
                                        [
                                            dbc.Spinner(
                                                dcc.Graph(
                                                    id="sample-graph",
                                                    config={
                                                        "displayModeBar": True,
                                                        "displaylogo": False,
                                                        "modeBarButtonsToRemove": [
                                                            "lasso2d",
                                                            "select2d",
                                                        ],
                                                    },
                                                ),
                                                color="primary",
                                                type="border",
                                                fullscreen=False,
                                                spinner_class_name="spinner-grow",
                                                delay_show=100,
                                            )
                                        ]
                                    ),
                                ],
                                id="visualization-card",
                                className="shadow-sm",
                            )
                        ],
                        md=8,
                    ),
                ]
            ),
            # Quick metrics row
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                "Quick Metrics", className="card-title"
                                            ),
                                            html.Div(id="quick-metrics"),
                                        ]
                                    )
                                ],
                                className="shadow-sm",
                            )
                        ],
                        md=12,
                    )
                ],
                className="mt-4",
            ),
        ],
        "Dashboard",
        "dashboard",
    )


def format_humanized_number(value: float, is_currency: bool = False) -> str:
    """Return a compact, human-friendly string for large numbers.

    Examples:
    - 1_234 -> "1.2K"
    - 5_000_000 -> "5M"
    - 2_500_000_000 -> "2.5B"
    Currency values are prefixed with "$".
    """
    try:
        number = float(value)
    except Exception:
        return "$0" if is_currency else "0"

    absolute_number = abs(number)
    if absolute_number >= 1_000_000_000:
        compact_value = number / 1_000_000_000
        suffix = "B"
    elif absolute_number >= 1_000_000:
        compact_value = number / 1_000_000
        suffix = "M"
    elif absolute_number >= 1_000:
        compact_value = number / 1_000
        suffix = "K"
    else:
        core = f"{number:,.0f}"
        return f"${core}" if is_currency else core

    # One decimal place max, trim trailing .0
    core = f"{compact_value:.1f}".rstrip("0").rstrip(".") + suffix
    return f"${core}" if is_currency else core


@callback(
    Output("year-dropdown", "options"),
    Input("sample-dropdown", "value"),
    prevent_initial_call=False,
)
def load_year_options(_selection: str):
    """Populate the Year dropdown from Snowflake sample orders data."""
    try:
        sql = (
            "SELECT DISTINCT DATE_PART('year', O_ORDERDATE) AS YEAR "
            "FROM snowflake_sample_data.tpch_sf10.orders "
            "WHERE O_ORDERDATE IS NOT NULL "
            "ORDER BY YEAR"
        )
        df = execute_query(sql)
        if "error" in df.columns or df.empty:
            return []
        years = [
            int(y)
            for y in df[df.columns[0]].dropna().astype(int).sort_values().tolist()
        ]
        return [{"label": str(y), "value": y} for y in years]
    except Exception:
        return []


@callback(
    [
        Output("sample-graph", "figure"),
        Output("error-toast-dashboard", "is_open"),
        Output("error-toast-dashboard", "children"),
        Output("quick-metrics", "children"),
    ],
    [
        Input("sample-dropdown", "value"),
        Input("theme-store", "data"),
        Input("year-dropdown", "value"),
    ],
    [
        State("sample-graph", "figure"),
        State("quick-metrics", "children"),
    ],
    prevent_initial_call=False,
)
def update_dashboard(
    selected_value: str,
    theme_data: Dict[str, str],
    year_value: Any = None,
    fig_state: Any = None,
    metrics_state: Any = None,
) -> Tuple[Any, bool, str, Any]:
    """Update the dashboard based on selection and current theme."""
    try:
        # Helper to build a details accordion showing SQL and transformations
        def build_details(sql_text: str, transformations: list[str]) -> dbc.Accordion:
            return dbc.Accordion(
                [
                    dbc.AccordionItem(
                        [
                            html.Div(
                                [
                                    html.H6("SQL Executed", className="mb-2"),
                                    html.Pre(
                                        sql_text, style={"whiteSpace": "pre-wrap"}
                                    ),
                                ],
                                className="mb-3",
                            ),
                            html.Div(
                                [
                                    html.H6("Transformations", className="mb-2"),
                                    html.Ul([html.Li(t) for t in transformations]),
                                ]
                            ),
                        ],
                        title="Query & Transform Details",
                    )
                ],
                start_collapsed=True,
                class_name="mt-3",
            )

        # Determine theme-based colors first
        current_theme = (
            theme_data.get("current_theme", "snowflake") if theme_data else "snowflake"
        )

        if current_theme == "dark":
            template = "plotly_dark"
            text_color = "white"
            marker_color = "rgb(100, 149, 237)"
            marker_line_color = "rgb(135, 206, 250)"
        elif current_theme == "snowflake":
            template = "plotly_white"
            text_color = "#1E293B"
            marker_color = "#29B5E8"
            marker_line_color = "#1E3A8A"
        else:  # light
            template = "plotly_white"
            text_color = "black"
            marker_color = "rgb(59, 89, 152)"
            marker_line_color = "rgb(8, 48, 107)"

        # If only theme changed, restyle existing figure without re-querying
        triggered_id = None
        try:
            ctx = dash.callback_context
            if getattr(ctx, "triggered", None):
                triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
        except Exception:
            triggered_id = None

        if (
            triggered_id == "theme-store"
            and fig_state is not None
            and metrics_state is not None
        ):
            try:
                fig = go.Figure(fig_state) if fig_state else go.Figure()
                fig.update_layout(
                    title_x=0.5,
                    margin=dict(t=50, l=50, r=30, b=50),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    hovermode="closest",
                    showlegend=False,
                    font=dict(
                        family="system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
                        color=text_color,
                    ),
                    template=template,
                )
                fig.update_traces(
                    marker_color=marker_color,
                    marker_line_color=marker_line_color,
                    marker_line_width=1.5,
                    opacity=0.8,
                )
                return (
                    fig,
                    False,
                    "",
                    metrics_state if metrics_state is not None else html.Div(),
                )
            except Exception:
                # Fallback: return prior state unmodified
                return (
                    fig_state,
                    False,
                    "",
                    metrics_state if metrics_state is not None else html.Div(),
                )

        # Use Snowflake sample data
        if selected_value == "revenue":
            sql = (
                "SELECT r.R_NAME AS REGION, ROUND(SUM(orv.ORDER_REVENUE), 2) AS REVENUE "
                "FROM snowflake_sample_data.tpch_sf10.region r "
                "JOIN snowflake_sample_data.tpch_sf10.nation n ON r.R_REGIONKEY = n.N_REGIONKEY "
                "JOIN snowflake_sample_data.tpch_sf10.customer c ON n.N_NATIONKEY = c.C_NATIONKEY "
                "JOIN snowflake_sample_data.tpch_sf10.orders o ON c.C_CUSTKEY = o.O_CUSTKEY "
                "JOIN (SELECT l.L_ORDERKEY AS ORDERKEY, SUM(l.L_EXTENDEDPRICE * (1 - l.L_DISCOUNT)) AS ORDER_REVENUE "
                "      FROM snowflake_sample_data.tpch_sf10.lineitem l GROUP BY l.L_ORDERKEY) orv "
                "ON o.O_ORDERKEY = orv.ORDERKEY "
            )
            if year_value:
                sql += f" WHERE DATE_PART('year', o.O_ORDERDATE) = {int(year_value)}"
            sql += " GROUP BY 1 ORDER BY REVENUE DESC LIMIT 5"
            df = execute_query(sql)
            if "error" in df.columns or df.empty:
                msg = (
                    df["error"].iloc[0]
                    if "error" in df.columns and not df.empty
                    else "No data returned"
                )
                empty_fig = px.bar(title="Error loading data")
                return empty_fig, True, msg, html.Div("Error loading metrics")
            title = "Revenue by Region"
            x, y = df.columns[0], df.columns[1]
            total_metric = format_humanized_number(df[y].sum(), True)
            avg_metric = format_humanized_number(df[y].mean(), True)
            details_acc = build_details(
                sql,
                [
                    "Subquery order_revenue: SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)) per order",
                    "JOIN region→nation→customer→orders→order_revenue",
                    "Aggregation: SUM(order_revenue) by region",
                    "GROUP BY region",
                    "ORDER BY revenue DESC",
                    "LIMIT 5",
                ],
            )
        elif selected_value == "customers":
            sql = (
                "SELECT DATE_TRUNC('quarter', O_ORDERDATE) AS QUARTER, COUNT(DISTINCT O_CUSTKEY) AS CUSTOMERS "
                "FROM snowflake_sample_data.tpch_sf10.orders"
            )
            if year_value:
                sql += f" WHERE DATE_PART('year', O_ORDERDATE) = {int(year_value)}"
            sql += " GROUP BY 1 ORDER BY 1 LIMIT 8"
            df = execute_query(sql)
            if "error" in df.columns or df.empty:
                msg = (
                    df["error"].iloc[0]
                    if "error" in df.columns and not df.empty
                    else "No data returned"
                )
                empty_fig = px.bar(title="Error loading data")
                return empty_fig, True, msg, html.Div("Error loading metrics")
            title = "Customer Growth by Quarter"
            x, y = df.columns[0], df.columns[1]
            total_metric = format_humanized_number(df[y].iloc[-1], False)
            avg_metric = format_humanized_number(df[y].mean(), False)
            details_acc = build_details(
                sql,
                [
                    "DATE_TRUNC by quarter on O_ORDERDATE",
                    "Aggregation: COUNT(DISTINCT O_CUSTKEY)",
                    "GROUP BY quarter",
                    "ORDER BY quarter",
                    "LIMIT 8",
                ],
            )
        elif selected_value == "sales":
            sql = (
                "SELECT DATE_TRUNC('month', O_ORDERDATE) AS MONTH, SUM(O_TOTALPRICE) AS SALES "
                "FROM snowflake_sample_data.tpch_sf10.orders"
            )
            if year_value:
                sql += f" WHERE DATE_PART('year', O_ORDERDATE) = {int(year_value)}"
            sql += " GROUP BY 1 ORDER BY 1 LIMIT 12"
            df = execute_query(sql)
            if "error" in df.columns or df.empty:
                msg = (
                    df["error"].iloc[0]
                    if "error" in df.columns and not df.empty
                    else "No data returned"
                )
                empty_fig = px.bar(title="Error loading data")
                return empty_fig, True, msg, html.Div("Error loading metrics")
            title = "Monthly Sales Trends"
            x, y = df.columns[0], df.columns[1]
            total_metric = format_humanized_number(df[y].sum(), True)
            avg_metric = format_humanized_number(df[y].mean(), True)
            details_acc = build_details(
                sql,
                [
                    "DATE_TRUNC by month on O_ORDERDATE",
                    "Aggregation: SUM(O_TOTALPRICE) as SALES",
                    "GROUP BY month",
                    "ORDER BY month",
                    "LIMIT 12",
                ],
            )
        else:  # products
            sql = (
                "SELECT p.P_NAME AS PRODUCT, SUM(l.L_QUANTITY) AS UNITS "
                "FROM snowflake_sample_data.tpch_sf10.part p "
                "JOIN snowflake_sample_data.tpch_sf10.lineitem l ON p.P_PARTKEY = l.L_PARTKEY "
                "JOIN snowflake_sample_data.tpch_sf10.orders o ON l.L_ORDERKEY = o.O_ORDERKEY"
            )
            if year_value:
                sql += f" WHERE DATE_PART('year', o.O_ORDERDATE) = {int(year_value)}"
            sql += " GROUP BY 1 ORDER BY UNITS DESC LIMIT 10"
            df = execute_query(sql)
            if "error" in df.columns or df.empty:
                msg = (
                    df["error"].iloc[0]
                    if "error" in df.columns and not df.empty
                    else "No data returned"
                )
                empty_fig = px.bar(title="Error loading data")
                return empty_fig, True, msg, html.Div("Error loading metrics")
            title = "Product Performance"
            x, y = df.columns[0], df.columns[1]
            total_metric = format_humanized_number(df[y].sum(), False)
            avg_metric = format_humanized_number(df[y].mean(), False)
            details_acc = build_details(
                sql,
                [
                    "JOIN part (p) with lineitem (l) on P_PARTKEY",
                    "Aggregation: SUM(L_QUANTITY) as UNITS",
                    "GROUP BY product name",
                    "ORDER BY UNITS DESC",
                    "LIMIT 10",
                ],
            )

        # Create the chart
        fig = px.bar(
            df,
            x=x,
            y=y,
            title=title,
            template=template,
            labels={x: x.title(), y: y.title()},
            height=400,
        )

        # Enhanced figure layout
        fig.update_layout(
            title_x=0.5,
            margin=dict(t=50, l=50, r=30, b=50),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            hovermode="closest",
            showlegend=False,
            font=dict(
                family="system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
                color=text_color,
            ),
        )

        fig.update_traces(
            marker_color=marker_color,
            marker_line_color=marker_line_color,
            marker_line_width=1.5,
            opacity=0.8,
        )

        # Create quick metrics
        metrics = html.Div(
            [
                html.Div(
                    [
                        html.Span(
                            f"Year: {year_value}" if year_value else "Year: All",
                            className="text-muted",
                        )
                    ],
                    className="mb-2",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H5("Total", className="text-muted"),
                                html.H3(total_metric, className="text-primary"),
                            ],
                            md=6,
                        ),
                        dbc.Col(
                            [
                                html.H5("Average", className="text-muted"),
                                html.H3(avg_metric, className="text-secondary"),
                            ],
                            md=6,
                        ),
                    ]
                ),
                # Append query & transform details below metrics
                details_acc,
            ]
        )

        return fig, False, "", metrics

    except Exception as e:
        logger.error(f"Error updating dashboard: {e}")
        empty_fig = px.bar(title="Error loading data")
        return empty_fig, True, str(e), html.Div("Error loading metrics")
