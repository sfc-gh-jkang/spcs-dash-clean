"""
Multi-page Snowflake Dash Analytics Application.

A modern multi-page Dash application designed for deployment to Snowflake Container Services (SPCS)
with full local development support. Features interactive data visualization, Snowflake integration,
and a responsive UI with dark/light mode support across multiple pages.
"""

# Suppress warnings before importing any packages
import warnings
import logging

warnings.filterwarnings("ignore", category=UserWarning, module="snowflake.*")
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*")
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Suppress Snowflake INFO logs for cleaner startup
logging.getLogger("snowflake.snowpark").setLevel(logging.WARNING)

from dash import Dash, Output, Input, callback, page_container  # noqa: E402
import dash  # noqa: E402
import dash_bootstrap_components as dbc  # noqa: E402
import time  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
import sys  # noqa: E402
import pytz  # noqa: E402  # type: ignore[import-not-found]

# Mypy: provide typing stubs if available (ignored at runtime)
try:  # pragma: no cover
    import types_pytz as _types_pytz  # type: ignore # noqa: F401
except Exception:  # pragma: no cover
    _types_pytz = None  # type: ignore

# Import shared components
from components.layout import create_theme_store  # noqa: E402

# Add a global variable indicating the port number
PORT = 8000

# Configure logging with timezone support
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(timezone)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(), logging.FileHandler("app.log")],
)


# Add timezone info to logging
class TimezoneFormatter(logging.Formatter):
    def format(self, record):
        record.timezone = time.strftime("%Z %z", time.localtime(record.created))
        return super().format(record)


# Apply timezone formatter to all handlers
for handler in logging.getLogger().handlers:
    handler.setFormatter(
        TimezoneFormatter(
            "%(asctime)s %(timezone)s - %(name)s - %(levelname)s - %(message)s"
        )
    )

logger = logging.getLogger(__name__)

# Initialize the Dash app with Bootstrap theme and multi-page support
THEME = dbc.themes.BOOTSTRAP
app = Dash(
    __name__,
    external_stylesheets=[THEME, dbc.icons.FONT_AWESOME],
    title="Snowflake Analytics Platform",
    suppress_callback_exceptions=True,
    assets_folder="static",
    use_pages=True,  # Enable multi-page support
    pages_folder="pages",  # Specify pages folder
)
server = app.server  # Needed for deployment

# Pages are automatically discovered by Dash using use_pages=True and pages_folder="pages"


# Add basic security headers
@server.after_request
def add_security_headers(response):  # type: ignore[no-redef]
    """Set minimal security headers for all responses."""
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    # CSP tuned for Dash + fonts; relax connect-src for API calls
    # Allow external CDNs (Bootstrap theme, Font Awesome, etc.)
    csp = (
        "default-src 'self' https:; "
        "img-src 'self' data: blob: https:; "
        "style-src 'self' 'unsafe-inline' https:; "
        "font-src 'self' data: https:; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; "
        "connect-src 'self' *; "
        "frame-ancestors 'self'"
    )
    response.headers.setdefault("Content-Security-Policy", csp)
    return response


# Add dedicated health check endpoint for container orchestration
@server.route("/health")
def health_check():
    """Health check endpoint for Docker and SPCS monitoring."""
    # Get current time in UTC
    now_utc = datetime.now(timezone.utc)

    # Use pytz for accurate NYC timezone (automatically handles EST/EDT)
    nyc_tz = pytz.timezone("America/New_York")
    now_nyc = now_utc.astimezone(nyc_tz)

    # Get timezone name and offset
    tz_name = now_nyc.strftime("%Z")  # EST or EDT
    tz_offset = now_nyc.strftime("%z")  # -0500 or -0400

    # Get library versions
    import dash
    import plotly
    import pandas as pd
    import snowflake.snowpark
    import dash_bootstrap_components as dbc
    import dash_ag_grid as dag

    versions = {
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "dash": dash.__version__,
        "plotly": plotly.__version__,
        "pandas": pd.__version__,
        "snowpark": snowflake.snowpark.__version__,
        "dash_bootstrap_components": dbc.__version__,
        "dash_ag_grid": dag.__version__,
        "pytz": pytz.__version__,
    }

    return {
        "status": "healthy",
        "service": "dash-app-multipage",
        "port": PORT,
        "timestamp_utc": now_utc.isoformat(),
        "timestamp_NYC": now_nyc.isoformat(),
        "timezone": f"NYC {tz_name} ({tz_offset})",
        "versions": versions,
        "pages": [page["path"] for page in dash.page_registry.values()],
    }, 200


# Define the main app layout with page container
app.layout = dbc.Container(
    [
        create_theme_store(),
        page_container,  # This will render the current page
    ],
    fluid=True,
    className="p-0",
)


# Global theme callback that works across all pages
@callback(
    [
        Output("theme-store", "data"),
        Output("snowflake-theme-btn", "color"),
        Output("light-theme-btn", "color"),
        Output("dark-theme-btn", "color"),
    ],
    [
        Input("snowflake-theme-btn", "n_clicks"),
        Input("light-theme-btn", "n_clicks"),
        Input("dark-theme-btn", "n_clicks"),
    ],
    prevent_initial_call=False,
)
def update_theme(snowflake_clicks, light_clicks, dark_clicks):
    """Handle theme selection from three-button group across all pages."""
    ctx = dash.callback_context

    if not ctx.triggered:
        # Initial state - use default theme
        theme = "snowflake"
    else:
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if button_id == "snowflake-theme-btn":
            theme = "snowflake"
        elif button_id == "light-theme-btn":
            theme = "light"
        elif button_id == "dark-theme-btn":
            theme = "dark"
        else:
            theme = "snowflake"

    # Set button colors based on active theme
    snowflake_color = "primary" if theme == "snowflake" else "info"
    light_color = "warning" if theme == "light" else "info"
    dark_color = "dark" if theme == "dark" else "info"

    return ({"current_theme": theme}, snowflake_color, light_color, dark_color)


# Add external CSS and fonts to the app
app.index_string = """<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="/static/styles.css">
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""

# Clientside callback to update body class for three themes
app.clientside_callback(
    """
    function(theme_data) {
        // Remove all theme classes
        document.body.classList.remove('light-theme', 'dark-theme');

        if (theme_data) {
            const theme = theme_data.current_theme;
            if (theme === 'light') {
                document.body.classList.add('light-theme');
            } else if (theme === 'dark') {
                document.body.classList.add('dark-theme');
            }
            // For 'snowflake' theme, no additional class needed (default)
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("theme-store", "data", allow_duplicate=True),
    Input("theme-store", "data"),
    prevent_initial_call=True,
)

if __name__ == "__main__":
    logger.info(f"Starting Multi-Page Snowflake Dash Application on port {PORT}")
    logger.info(f"Registered pages: {list(dash.page_registry.keys())}")
    app.run(debug=True, host="0.0.0.0", port=PORT)
