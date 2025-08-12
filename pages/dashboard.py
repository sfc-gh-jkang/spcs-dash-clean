"""
Dashboard page - Main analytics and visualization page.
"""

import dash
from dash import html, dcc, Output, Input, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from typing import Tuple, Dict, Any
import logging

from components.layout import create_page_container

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


@callback(
    [
        Output("sample-graph", "figure"),
        Output("error-toast-dashboard", "is_open"),
        Output("error-toast-dashboard", "children"),
        Output("quick-metrics", "children"),
    ],
    [Input("sample-dropdown", "value"), Input("theme-store", "data")],
    prevent_initial_call=False,
)
def update_dashboard(
    selected_value: str, theme_data: Dict[str, str]
) -> Tuple[Any, bool, str, Any]:
    """Update the dashboard based on selection and current theme."""
    try:
        # Sample data - in production, you would query Snowflake here
        if selected_value == "revenue":
            df = pd.DataFrame(
                {
                    "Region": ["North", "South", "East", "West"],
                    "Revenue": [120000, 85000, 95000, 115000],
                }
            )
            title = "Revenue by Region"
            x, y = "Region", "Revenue"
            total_metric = f"${df['Revenue'].sum():,}"
            avg_metric = f"${df['Revenue'].mean():,.0f}"
        elif selected_value == "customers":
            df = pd.DataFrame(
                {
                    "Quarter": ["Q1", "Q2", "Q3", "Q4"],
                    "Customers": [1200, 1450, 1800, 2100],
                }
            )
            title = "Customer Growth by Quarter"
            x, y = "Quarter", "Customers"
            total_metric = f"{df['Customers'].iloc[-1]:,}"
            avg_metric = f"{df['Customers'].mean():,.0f}"
        elif selected_value == "sales":
            df = pd.DataFrame(
                {
                    "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                    "Sales": [45000, 52000, 48000, 61000, 55000, 67000],
                }
            )
            title = "Monthly Sales Trends"
            x, y = "Month", "Sales"
            total_metric = f"${df['Sales'].sum():,}"
            avg_metric = f"${df['Sales'].mean():,.0f}"
        else:  # products
            df = pd.DataFrame(
                {
                    "Product": ["Product A", "Product B", "Product C", "Product D"],
                    "Units": [850, 720, 960, 640],
                }
            )
            title = "Product Performance"
            x, y = "Product", "Units"
            total_metric = f"{df['Units'].sum():,}"
            avg_metric = f"{df['Units'].mean():,.0f}"

        # Determine theme-based colors
        current_theme = (
            theme_data.get("current_theme", "snowflake") if theme_data else "snowflake"
        )

        if current_theme == "dark":
            template = "plotly_dark"
            text_color = "white"
        elif current_theme == "snowflake":
            template = "plotly_white"
            text_color = "#1E293B"
        else:  # light
            template = "plotly_white"
            text_color = "black"

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

        # Theme-specific bar styling
        if current_theme == "snowflake":
            marker_color = "#29B5E8"
            marker_line_color = "#1E3A8A"
        elif current_theme == "dark":
            marker_color = "rgb(100, 149, 237)"
            marker_line_color = "rgb(135, 206, 250)"
        else:  # light
            marker_color = "rgb(59, 89, 152)"
            marker_line_color = "rgb(8, 48, 107)"

        fig.update_traces(
            marker_color=marker_color,
            marker_line_color=marker_line_color,
            marker_line_width=1.5,
            opacity=0.8,
        )

        # Create quick metrics
        metrics = html.Div(
            [
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
                )
            ]
        )

        return fig, False, "", metrics

    except Exception as e:
        logger.error(f"Error updating dashboard: {e}")
        empty_fig = px.bar(title="Error loading data")
        return empty_fig, True, str(e), html.Div("Error loading metrics")
