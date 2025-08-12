"""
Analytics page - Advanced analytics and custom queries.
"""

import dash
from dash import html, dcc, Output, Input, State, callback, no_update
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import logging

from components.layout import create_page_container
from utils.snowflake_utils import execute_query, format_query_results


# Register this page
dash.register_page(
    __name__,
    path="/analytics",
    name="Analytics",
    title="Analytics - Snowflake Analytics",
)

logger = logging.getLogger(__name__)


def layout():
    """Analytics page layout."""
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
                                            html.I(className="fas fa-chart-area me-2"),
                                            "Advanced Analytics",
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            dbc.Label(
                                                "Select Analysis Type:",
                                                className="mb-2",
                                            ),
                                            dcc.Dropdown(
                                                id="analytics-type-dropdown",
                                                options=[
                                                    {
                                                        "label": "Sales Analysis",
                                                        "value": "sales",
                                                    },
                                                    {
                                                        "label": "Customer Segmentation",
                                                        "value": "customers",
                                                    },
                                                    {
                                                        "label": "Product Performance",
                                                        "value": "products",
                                                    },
                                                    {
                                                        "label": "Regional Analysis",
                                                        "value": "regions",
                                                    },
                                                    {
                                                        "label": "Time Series Analysis",
                                                        "value": "timeseries",
                                                    },
                                                ],
                                                value="sales",
                                                clearable=False,
                                                className="mb-3",
                                            ),
                                            dbc.Button(
                                                "Run Analysis",
                                                id="run-analysis-btn",
                                                color="primary",
                                                className="mb-3",
                                            ),
                                        ]
                                    ),
                                ],
                                className="shadow-sm mb-4",
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
                                            html.I(className="fas fa-code me-2"),
                                            "Custom SQL Query",
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            dbc.Label(
                                                "Enter SQL Query:", className="mb-2"
                                            ),
                                            dcc.Textarea(
                                                id="sql-query-input",
                                                placeholder="SELECT * FROM snowflake_sample_data.tpch_sf10.customer LIMIT 10;",
                                                style={"width": "100%", "height": 100},
                                                className="mb-3",
                                            ),
                                            dbc.Alert(
                                                [
                                                    html.I(
                                                        className="fas fa-shield-alt me-2"
                                                    ),
                                                    html.Strong(
                                                        "Security & Performance Limits:"
                                                    ),
                                                    html.Ul(
                                                        [
                                                            html.Li(
                                                                "Only SELECT statements allowed (no data modification)"
                                                            ),
                                                            html.Li(
                                                                "Results limited to 10,000 rows maximum"
                                                            ),
                                                            html.Li(
                                                                "Rate limited to 10 queries per minute"
                                                            ),
                                                            html.Li(
                                                                "Access restricted to sample data schemas only"
                                                            ),
                                                            html.Li(
                                                                "Complex operations and file access blocked"
                                                            ),
                                                            html.Li(
                                                                "SQL injection protection enabled"
                                                            ),
                                                        ],
                                                        className="mb-0 mt-2",
                                                    ),
                                                ],
                                                color="info",
                                                className="mb-3",
                                                style={"fontSize": "0.875rem"},
                                            ),
                                            dbc.Button(
                                                "Execute Query",
                                                id="execute-query-btn",
                                                color="success",
                                                className="me-2",
                                            ),
                                            dbc.Button(
                                                "Clear",
                                                id="clear-query-btn",
                                                color="secondary",
                                                outline=True,
                                            ),
                                        ]
                                    ),
                                ],
                                className="shadow-sm mb-4",
                            )
                        ],
                        md=8,
                    ),
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
                                            "Query Results",
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            dcc.Loading(
                                                id="query-loading",
                                                children=html.Div(
                                                    id="query-results-content"
                                                ),
                                                type="default",
                                                style={"minHeight": "200px"},
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
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.I(className="fas fa-list-alt me-2"),
                                            "Common Queries",
                                            html.Small(
                                                " - Click to use",
                                                className="text-muted ms-2",
                                            ),
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.P(
                                                "Select from these common queries:",
                                                className="mb-3",
                                            ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.H6(
                                                                "📊 Data Exploration",
                                                                className="mb-2",
                                                            ),
                                                            dbc.ListGroup(
                                                                [
                                                                    dbc.ListGroupItem(
                                                                        [
                                                                            html.Strong(
                                                                                "Top 10 Customers by Revenue"
                                                                            ),
                                                                            html.Br(),
                                                                            html.Small(
                                                                                "Analyze highest value customers",
                                                                                className="text-muted",
                                                                            ),
                                                                        ],
                                                                        id="query-top-customers",
                                                                        action=True,
                                                                        className="query-item",
                                                                    ),
                                                                    dbc.ListGroupItem(
                                                                        [
                                                                            html.Strong(
                                                                                "Sales by Region"
                                                                            ),
                                                                            html.Br(),
                                                                            html.Small(
                                                                                "Regional sales performance",
                                                                                className="text-muted",
                                                                            ),
                                                                        ],
                                                                        id="query-sales-region",
                                                                        action=True,
                                                                        className="query-item",
                                                                    ),
                                                                    dbc.ListGroupItem(
                                                                        [
                                                                            html.Strong(
                                                                                "Product Performance"
                                                                            ),
                                                                            html.Br(),
                                                                            html.Small(
                                                                                "Top selling products analysis",
                                                                                className="text-muted",
                                                                            ),
                                                                        ],
                                                                        id="query-product-performance",
                                                                        action=True,
                                                                        className="query-item",
                                                                    ),
                                                                ],
                                                                flush=True,
                                                            ),
                                                        ],
                                                        md=4,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            html.H6(
                                                                "📈 Business Analytics",
                                                                className="mb-2",
                                                            ),
                                                            dbc.ListGroup(
                                                                [
                                                                    dbc.ListGroupItem(
                                                                        [
                                                                            html.Strong(
                                                                                "Monthly Sales Trends"
                                                                            ),
                                                                            html.Br(),
                                                                            html.Small(
                                                                                "Time-based sales analysis",
                                                                                className="text-muted",
                                                                            ),
                                                                        ],
                                                                        id="query-monthly-trends",
                                                                        action=True,
                                                                        className="query-item",
                                                                    ),
                                                                    dbc.ListGroupItem(
                                                                        [
                                                                            html.Strong(
                                                                                "Customer Lifetime Value"
                                                                            ),
                                                                            html.Br(),
                                                                            html.Small(
                                                                                "Customer value analysis",
                                                                                className="text-muted",
                                                                            ),
                                                                        ],
                                                                        id="query-customer-ltv",
                                                                        action=True,
                                                                        className="query-item",
                                                                    ),
                                                                    dbc.ListGroupItem(
                                                                        [
                                                                            html.Strong(
                                                                                "Order Frequency Analysis"
                                                                            ),
                                                                            html.Br(),
                                                                            html.Small(
                                                                                "Customer ordering patterns",
                                                                                className="text-muted",
                                                                            ),
                                                                        ],
                                                                        id="query-order-frequency",
                                                                        action=True,
                                                                        className="query-item",
                                                                    ),
                                                                ],
                                                                flush=True,
                                                            ),
                                                        ],
                                                        md=4,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            html.H6(
                                                                "🔍 Sample Data",
                                                                className="mb-2",
                                                            ),
                                                            dbc.ListGroup(
                                                                [
                                                                    dbc.ListGroupItem(
                                                                        [
                                                                            html.Strong(
                                                                                "Browse Customer Table"
                                                                            ),
                                                                            html.Br(),
                                                                            html.Small(
                                                                                "View customer data structure",
                                                                                className="text-muted",
                                                                            ),
                                                                        ],
                                                                        id="query-browse-customers",
                                                                        action=True,
                                                                        className="query-item",
                                                                    ),
                                                                    dbc.ListGroupItem(
                                                                        [
                                                                            html.Strong(
                                                                                "Browse Orders Table"
                                                                            ),
                                                                            html.Br(),
                                                                            html.Small(
                                                                                "View orders data structure",
                                                                                className="text-muted",
                                                                            ),
                                                                        ],
                                                                        id="query-browse-orders",
                                                                        action=True,
                                                                        className="query-item",
                                                                    ),
                                                                    dbc.ListGroupItem(
                                                                        [
                                                                            html.Strong(
                                                                                "Table Information"
                                                                            ),
                                                                            html.Br(),
                                                                            html.Small(
                                                                                "Get metadata about tables",
                                                                                className="text-muted",
                                                                            ),
                                                                        ],
                                                                        id="query-table-info",
                                                                        action=True,
                                                                        className="query-item",
                                                                    ),
                                                                ],
                                                                flush=True,
                                                            ),
                                                        ],
                                                        md=4,
                                                    ),
                                                ]
                                            ),
                                        ]
                                    ),
                                ],
                                className="shadow-sm mb-4",
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
                                            html.I(className="fas fa-chart-line me-2"),
                                            html.Span(
                                                "Analysis Results",
                                                id="analysis-results-header",
                                            ),
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            dbc.Spinner(
                                                html.Div(id="analysis-results-content"),
                                                color="primary",
                                                type="border",
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
            # Toast notification for query processing status
            dbc.Toast(
                id="query-status-toast",
                header="Query Status",
                is_open=False,
                dismissable=True,
                duration=3000,
                icon="info",
                style={
                    "position": "fixed",
                    "top": 66,
                    "right": 10,
                    "width": 350,
                    "z-index": 1999,
                },
            ),
        ],
        "Analytics",
        "analytics",
    )


@callback(
    [
        Output("analysis-results-content", "children"),
        Output("analysis-results-header", "children"),
    ],
    [Input("run-analysis-btn", "n_clicks"), Input("theme-store", "data")],
    State("analytics-type-dropdown", "value"),
    prevent_initial_call=True,
)
def run_predefined_analysis(n_clicks, theme_data, analysis_type):
    """Run predefined analytics based on selection."""
    if not n_clicks:
        return [], "Analysis Results"

    try:
        # Determine theme
        current_theme = (
            theme_data.get("current_theme", "snowflake") if theme_data else "snowflake"
        )

        if current_theme == "dark":
            template = "plotly_dark"
        elif current_theme == "snowflake":
            template = "plotly_white"
        else:
            template = "plotly_white"

        if analysis_type == "sales":
            # Sample sales analysis
            df = pd.DataFrame(
                {
                    "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                    "Sales": [45000, 52000, 48000, 61000, 55000, 67000],
                    "Target": [50000, 50000, 50000, 55000, 55000, 60000],
                }
            )

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df["Month"],
                    y=df["Sales"],
                    name="Actual Sales",
                    line=dict(color="#29B5E8"),
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df["Month"],
                    y=df["Target"],
                    name="Target",
                    line=dict(color="#FF6B6B", dash="dash"),
                )
            )
            fig.update_layout(
                title="Sales vs Target Analysis", template=template, height=400
            )

            return dcc.Graph(figure=fig), "Sales Analysis Results"

        elif analysis_type == "customers":
            # Customer segmentation
            df = pd.DataFrame(
                {
                    "Segment": ["High Value", "Medium Value", "Low Value", "New"],
                    "Count": [150, 320, 480, 200],
                    "Revenue": [450000, 320000, 180000, 50000],
                }
            )

            fig = px.pie(
                df,
                values="Count",
                names="Segment",
                title="Customer Segmentation by Count",
            )
            fig.update_layout(template=template, height=400)

            return dcc.Graph(figure=fig), "Customer Segmentation Results"

        elif analysis_type == "products":
            # Product performance
            df = pd.DataFrame(
                {
                    "Product": [
                        "Product A",
                        "Product B",
                        "Product C",
                        "Product D",
                        "Product E",
                    ],
                    "Revenue": [120000, 85000, 95000, 115000, 75000],
                    "Units": [850, 720, 960, 640, 580],
                }
            )

            fig = px.scatter(
                df,
                x="Units",
                y="Revenue",
                text="Product",
                title="Product Performance: Revenue vs Units Sold",
            )
            fig.update_traces(textposition="top center")
            fig.update_layout(template=template, height=400)

            return dcc.Graph(figure=fig), "Product Performance Results"

        elif analysis_type == "regions":
            # Regional analysis
            df = pd.DataFrame(
                {
                    "Region": ["North", "South", "East", "West", "Central"],
                    "Revenue": [120000, 85000, 95000, 115000, 90000],
                    "Growth": [15.2, 8.1, 12.3, 18.7, 10.5],
                }
            )

            fig = px.bar(
                df,
                x="Region",
                y="Revenue",
                color="Growth",
                title="Regional Revenue and Growth Analysis",
                color_continuous_scale="Blues",
            )
            fig.update_layout(template=template, height=400)

            return dcc.Graph(figure=fig), "Regional Analysis Results"

        else:  # timeseries
            # Time series analysis
            dates = pd.date_range("2023-01-01", periods=12, freq="M")
            df = pd.DataFrame(
                {
                    "Date": dates,
                    "Value": [
                        100,
                        110,
                        105,
                        120,
                        115,
                        130,
                        125,
                        140,
                        135,
                        150,
                        145,
                        160,
                    ],
                    "Trend": [
                        100,
                        105,
                        110,
                        115,
                        120,
                        125,
                        130,
                        135,
                        140,
                        145,
                        150,
                        155,
                    ],
                }
            )

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df["Date"],
                    y=df["Value"],
                    name="Actual",
                    line=dict(color="#29B5E8"),
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df["Date"],
                    y=df["Trend"],
                    name="Trend",
                    line=dict(color="#FF6B6B"),
                )
            )
            fig.update_layout(
                title="Time Series Analysis with Trend", template=template, height=400
            )

            return dcc.Graph(figure=fig), "Time Series Analysis Results"

    except Exception as e:
        logger.error(f"Error in predefined analysis: {e}")
        return dbc.Alert(
            f"Error running analysis: {str(e)}", color="danger"
        ), "Analysis Results"


@callback(
    [
        Output("query-results-content", "children"),
        Output("query-status-toast", "is_open"),
        Output("query-status-toast", "children"),
        Output("query-status-toast", "icon"),
    ],
    [Input("execute-query-btn", "n_clicks")],
    State("sql-query-input", "value"),
    prevent_initial_call=True,
)
def execute_custom_query(n_clicks, query):
    """Execute custom SQL query with status notifications."""
    # Check if this is actually a button click, not just page load
    ctx = dash.callback_context
    if not ctx.triggered or not n_clicks or n_clicks == 0:
        logger.info(
            f"Execute query callback: Page load or no clicks (n_clicks={n_clicks})"
        )
        # Return initial state - no loading, no toast, default message
        return (
            html.P(
                "Enter a SQL query and click 'Execute Query' to see results.",
                className="text-muted",
            ),
            False,  # No toast
            "",  # No toast message
            "info",  # Default icon
        )

    # Verify the trigger was the execute button
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id != "execute-query-btn":
        logger.info(f"Execute query callback: Wrong trigger {trigger_id}")
        return (
            html.P(
                "Enter a SQL query and click 'Execute Query' to see results.",
                className="text-muted",
            ),
            False,
            "",
            "info",
        )

    logger.info(
        f"Execute query callback: Valid button click n_clicks={n_clicks}, query='{query}'"
    )

    if not query or not query.strip():
        return (
            dbc.Alert("Please enter a SQL query before executing.", color="warning"),
            True,
            [
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Please enter a SQL query before executing.",
            ],
            "warning",
        )

    try:
        # Show processing notification
        logger.info("Starting query execution...")

        # Execute the query and format results using reusable utility functions
        result_df = execute_query(query)

        # Check if query was successful
        if "error" in result_df.columns:
            error_msg = result_df["error"].iloc[0]
            logger.error(f"Query execution failed: {error_msg}")
            return (
                dbc.Alert(f"Query failed: {error_msg}", color="danger"),
                True,
                [
                    html.I(className="fas fa-times-circle me-2"),
                    f"Query failed: {error_msg[:100]}{'...' if len(error_msg) > 100 else ''}",
                ],
                "danger",
            )

        # Format results and show success notification
        formatted_results = format_query_results(
            result_df, max_rows=1000, grid_id="analytics-query-results-grid"
        )

        row_count = len(result_df)
        logger.info(f"Query executed successfully, returned {row_count} rows")

        return (
            formatted_results,
            True,
            [
                html.I(className="fas fa-check-circle me-2"),
                f"Query completed successfully! Retrieved {row_count:,} row{'' if row_count == 1 else 's'}.",
            ],
            "success",
        )

    except Exception as e:
        logger.error(f"Unexpected error during query execution: {str(e)}")
        return (
            dbc.Alert(f"Unexpected error: {str(e)}", color="danger"),
            True,
            [
                html.I(className="fas fa-exclamation-circle me-2"),
                f"Unexpected error occurred: {str(e)[:100]}{'...' if len(str(e)) > 100 else ''}",
            ],
            "danger",
        )


@callback(
    Output("sql-query-input", "value"),
    Input("clear-query-btn", "n_clicks"),
    prevent_initial_call=True,
)
def clear_query(n_clicks):
    """Clear the SQL query input."""
    if n_clicks:
        return ""
    return no_update


@callback(
    Output("sql-query-input", "value", allow_duplicate=True),
    [
        Input("query-top-customers", "n_clicks"),
        Input("query-sales-region", "n_clicks"),
        Input("query-product-performance", "n_clicks"),
        Input("query-monthly-trends", "n_clicks"),
        Input("query-customer-ltv", "n_clicks"),
        Input("query-order-frequency", "n_clicks"),
        Input("query-browse-customers", "n_clicks"),
        Input("query-browse-orders", "n_clicks"),
        Input("query-table-info", "n_clicks"),
    ],
    prevent_initial_call=True,
)
def insert_common_query(*args):
    """Insert selected common query into the SQL input field."""
    ctx = dash.callback_context

    if not ctx.triggered:
        return no_update

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Define the common queries
    queries = {
        "query-top-customers": """-- Top 10 Customers by Revenue
SELECT 
    c.C_NAME as customer_name,
    c.C_MKTSEGMENT as market_segment,
    ROUND(SUM(o.O_TOTALPRICE), 2) as total_revenue,
    COUNT(o.O_ORDERKEY) as order_count
FROM snowflake_sample_data.tpch_sf10.customer c
JOIN snowflake_sample_data.tpch_sf10.orders o ON c.C_CUSTKEY = o.O_CUSTKEY
GROUP BY c.C_CUSTKEY, c.C_NAME, c.C_MKTSEGMENT
ORDER BY total_revenue DESC
LIMIT 10;""",
        "query-sales-region": """-- Sales Performance by Region
SELECT 
    r.R_NAME as region,
    n.N_NAME as nation,
    COUNT(DISTINCT o.O_ORDERKEY) as total_orders,
    ROUND(SUM(o.O_TOTALPRICE), 2) as total_revenue,
    ROUND(AVG(o.O_TOTALPRICE), 2) as avg_order_value
FROM snowflake_sample_data.tpch_sf10.region r
JOIN snowflake_sample_data.tpch_sf10.nation n ON r.R_REGIONKEY = n.N_REGIONKEY
JOIN snowflake_sample_data.tpch_sf10.customer c ON n.N_NATIONKEY = c.C_NATIONKEY
JOIN snowflake_sample_data.tpch_sf10.orders o ON c.C_CUSTKEY = o.O_CUSTKEY
GROUP BY r.R_REGIONKEY, r.R_NAME, n.N_NATIONKEY, n.N_NAME
ORDER BY total_revenue DESC;""",
        "query-product-performance": """-- Product Performance Analysis
SELECT 
    p.P_NAME as product_name,
    p.P_TYPE as product_type,
    p.P_BRAND as brand,
    COUNT(DISTINCT l.L_ORDERKEY) as orders_containing_product,
    ROUND(SUM(l.L_EXTENDEDPRICE), 2) as total_revenue,
    ROUND(AVG(l.L_EXTENDEDPRICE), 2) as avg_line_value,
    SUM(l.L_QUANTITY) as total_quantity_sold
FROM snowflake_sample_data.tpch_sf10.part p
JOIN snowflake_sample_data.tpch_sf10.lineitem l ON p.P_PARTKEY = l.L_PARTKEY
GROUP BY p.P_PARTKEY, p.P_NAME, p.P_TYPE, p.P_BRAND
ORDER BY total_revenue DESC
LIMIT 20;""",
        "query-monthly-trends": """-- Monthly Sales Trends
SELECT 
    YEAR(o.O_ORDERDATE) as order_year,
    MONTH(o.O_ORDERDATE) as order_month,
    COUNT(DISTINCT o.O_ORDERKEY) as total_orders,
    ROUND(SUM(o.O_TOTALPRICE), 2) as monthly_revenue,
    ROUND(AVG(o.O_TOTALPRICE), 2) as avg_order_value,
    COUNT(DISTINCT o.O_CUSTKEY) as unique_customers
FROM snowflake_sample_data.tpch_sf10.orders o
WHERE o.O_ORDERDATE >= '1995-01-01' 
    AND o.O_ORDERDATE < '1997-01-01'
GROUP BY YEAR(o.O_ORDERDATE), MONTH(o.O_ORDERDATE)
ORDER BY order_year, order_month;""",
        "query-customer-ltv": """-- Customer Lifetime Value Analysis
SELECT 
    c.C_MKTSEGMENT as market_segment,
    COUNT(DISTINCT c.C_CUSTKEY) as customer_count,
    ROUND(AVG(customer_totals.lifetime_value), 2) as avg_lifetime_value,
    ROUND(MIN(customer_totals.lifetime_value), 2) as min_lifetime_value,
    ROUND(MAX(customer_totals.lifetime_value), 2) as max_lifetime_value,
    ROUND(AVG(customer_totals.order_count), 1) as avg_orders_per_customer
FROM (
    SELECT 
        c.C_CUSTKEY,
        c.C_MKTSEGMENT,
        SUM(o.O_TOTALPRICE) as lifetime_value,
        COUNT(o.O_ORDERKEY) as order_count
    FROM snowflake_sample_data.tpch_sf10.customer c
    JOIN snowflake_sample_data.tpch_sf10.orders o ON c.C_CUSTKEY = o.O_CUSTKEY
    GROUP BY c.C_CUSTKEY, c.C_MKTSEGMENT
) customer_totals
JOIN snowflake_sample_data.tpch_sf10.customer c ON customer_totals.C_CUSTKEY = c.C_CUSTKEY
GROUP BY c.C_MKTSEGMENT
ORDER BY avg_lifetime_value DESC;""",
        "query-order-frequency": """-- Customer Order Frequency Analysis
SELECT 
    order_frequency_bucket,
    COUNT(*) as customer_count,
    ROUND(AVG(total_spent), 2) as avg_total_spent,
    ROUND(AVG(avg_order_value), 2) as avg_order_value
FROM (
    SELECT 
        c.C_CUSTKEY,
        COUNT(o.O_ORDERKEY) as order_count,
        SUM(o.O_TOTALPRICE) as total_spent,
        AVG(o.O_TOTALPRICE) as avg_order_value,
        CASE 
            WHEN COUNT(o.O_ORDERKEY) = 1 THEN '1 Order'
            WHEN COUNT(o.O_ORDERKEY) BETWEEN 2 AND 5 THEN '2-5 Orders'
            WHEN COUNT(o.O_ORDERKEY) BETWEEN 6 AND 10 THEN '6-10 Orders'
            ELSE '10+ Orders'
        END as order_frequency_bucket
    FROM snowflake_sample_data.tpch_sf10.customer c
    JOIN snowflake_sample_data.tpch_sf10.orders o ON c.C_CUSTKEY = o.O_CUSTKEY
    GROUP BY c.C_CUSTKEY
) customer_analysis
GROUP BY order_frequency_bucket
ORDER BY 
    CASE order_frequency_bucket
        WHEN '1 Order' THEN 1
        WHEN '2-5 Orders' THEN 2
        WHEN '6-10 Orders' THEN 3
        ELSE 4
    END;""",
        "query-browse-customers": """-- Browse Customer Table Structure and Sample Data
SELECT 
    C_CUSTKEY as customer_key,
    C_NAME as customer_name,
    C_ADDRESS as address,
    C_NATIONKEY as nation_key,
    C_PHONE as phone,
    C_ACCTBAL as account_balance,
    C_MKTSEGMENT as market_segment,
    C_COMMENT as comment
FROM snowflake_sample_data.tpch_sf10.customer 
ORDER BY C_CUSTKEY
LIMIT 50;""",
        "query-browse-orders": """-- Browse Orders Table Structure and Sample Data
SELECT 
    O_ORDERKEY as order_key,
    O_CUSTKEY as customer_key,
    O_ORDERSTATUS as order_status,
    O_TOTALPRICE as total_price,
    O_ORDERDATE as order_date,
    O_ORDERPRIORITY as order_priority,
    O_CLERK as clerk,
    O_SHIPPRIORITY as ship_priority
FROM snowflake_sample_data.tpch_sf10.orders 
ORDER BY O_ORDERDATE DESC
LIMIT 50;""",
        "query-table-info": """-- Show Information About Available Tables
SELECT 
    table_schema,
    table_name,
    table_type,
    row_count,
    bytes,
    created
FROM snowflake_sample_data.information_schema.tables 
WHERE table_schema = 'TPCH_SF10'
    AND table_type = 'BASE TABLE'
ORDER BY table_name;""",
    }

    if button_id in queries:
        return queries[button_id]

    return no_update


# Note: AG Grid theme callback would be added here if needed for dynamic theme switching
# This would require the AG Grid component to exist first, so it's handled in the utility function
