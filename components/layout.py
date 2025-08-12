"""
Shared layout components for the multi-page Dash application.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def create_navbar():
    """Create the main navigation bar with theme controls and page links."""
    return dbc.Navbar(
        dbc.Container(
            [
                # Brand/Logo section
                html.Div(
                    [
                        html.I(
                            className="fas fa-snowflake me-2", style={"color": "white"}
                        ),
                        html.H1(
                            "Snowflake Analytics Platform",
                            className="d-inline mb-0",
                            style={"color": "white", "fontWeight": "600"},
                        ),
                    ],
                    className="d-flex align-items-center",
                ),
                # Navigation links
                dbc.Nav(
                    [
                        dbc.NavItem(dbc.NavLink("Dashboard", href="/", active="exact")),
                        dbc.NavItem(
                            dbc.NavLink(
                                "Data Browser", href="/data-browser", active="exact"
                            )
                        ),
                        dbc.NavItem(
                            dbc.NavLink("Analytics", href="/analytics", active="exact")
                        ),
                    ],
                    navbar=True,
                    className="me-auto",
                ),
                # Theme toggle button group
                dbc.ButtonGroup(
                    [
                        dbc.Button(
                            html.I(className="fas fa-snowflake"),
                            id="snowflake-theme-btn",
                            color="primary",
                            outline=True,
                            size="sm",
                            title="Snowflake theme",
                            className="theme-btn",
                        ),
                        dbc.Button(
                            html.I(className="fas fa-sun"),
                            id="light-theme-btn",
                            color="info",
                            outline=True,
                            size="sm",
                            title="Light theme",
                            className="theme-btn",
                        ),
                        dbc.Button(
                            html.I(className="fas fa-moon"),
                            id="dark-theme-btn",
                            color="info",
                            outline=True,
                            size="sm",
                            title="Dark theme",
                            className="theme-btn",
                        ),
                    ],
                    size="sm",
                ),
            ],
            fluid=True,
        ),
        id="main-navbar",
        color="light",
        className="mb-4",
    )


def create_theme_store():
    """Create the theme storage component."""
    return dcc.Store(id="theme-store", data={"current_theme": "snowflake"})


def create_error_toast(page_suffix=""):
    """Create a reusable error toast component with optional page suffix."""
    toast_id = f"error-toast{'-' + page_suffix if page_suffix else ''}"
    return dbc.Toast(
        id=toast_id,
        header="Error",
        is_open=False,
        dismissable=True,
        duration=4000,
        icon="danger",
        class_name="position-fixed top-0 end-0 m-3",
        style={"z-index": 1999},
    )


def create_page_container(children, page_title="Snowflake Analytics", page_suffix=""):
    """Create a standard page container with consistent styling."""
    return dbc.Container(
        [
            create_navbar(),
            html.Div(children, className="page-content"),
            create_error_toast(page_suffix),
        ],
        fluid=True,
        className="p-4",
    )
