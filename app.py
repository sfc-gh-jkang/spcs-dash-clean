from typing import Tuple, Dict, Any
from dash import Dash, html, dcc, Output, Input, State
import dash
import plotly.express as px
import pandas as pd

# Suppress pkg_resources warnings before importing snowflake
import warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*")
warnings.filterwarnings("ignore", category=UserWarning, module="snowflake.*")

from snowflake.snowpark.session import Session  # noqa: E402
import dash_bootstrap_components as dbc # noqa: E402
import dash_ag_grid as dag # noqa: E402
import os # noqa: E402
import logging # noqa: E402
import time # noqa: E402
from datetime import datetime, timezone # noqa: E402
import sys # noqa: E402
import pytz # noqa: E402

# Add a global variable indicating the port number
PORT = 8000

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(timezone)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

# Add timezone info to logging
class TimezoneFormatter(logging.Formatter):
    def format(self, record):
        record.timezone = time.strftime('%Z %z', time.localtime(record.created))
        return super().format(record)

# Apply timezone formatter to all handlers
for handler in logging.getLogger().handlers:
    handler.setFormatter(TimezoneFormatter('%(asctime)s %(timezone)s - %(name)s - %(levelname)s - %(message)s'))
logger = logging.getLogger(__name__)

def is_running_in_spcs():
    """
    Checks if the current environment is Snowpark Container Services (SPCS)
    by looking for the Snowflake session token file.
    """
    snowflake_token_path = "/snowflake/session/token"
    return os.path.exists(snowflake_token_path)

def get_login_token():
    """Get the login token from the Snowflake session token file."""
    with open('/snowflake/session/token', 'r') as f:
        return f.read()


# Initialize Snowflake connection
def get_snowflake_session() -> Session:
    """Create a Snowflake session using environment variables."""
    try:
        if is_running_in_spcs():
            logger.info("Detected SPCS environment - using token authentication")
            connection_parameters = {
                "host": os.getenv('SNOWFLAKE_HOST'),
                "account": os.getenv('SNOWFLAKE_ACCOUNT'),
                "token": get_login_token(),
                "authenticator": 'oauth',
                "database": os.getenv('SNOWFLAKE_DATABASE'),
                "schema": os.getenv('SNOWFLAKE_SCHEMA', 'PUBLIC'),
                "warehouse": os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH')
            }
            session = Session.builder.configs(connection_parameters).create()
            logger.info("Successfully connected to Snowflake via SPCS token authentication")
        else:            
            logger.info("Detected local environment - using credential authentication")
            connection_parameters = {
                "account": os.getenv("SNOWFLAKE_ACCOUNT"),
                "user": os.getenv("SNOWFLAKE_USER"),
                "password": os.getenv("SNOWFLAKE_PASSWORD"),
                "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
                "database": os.getenv("SNOWFLAKE_DATABASE"),
                "schema": os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")
            }
            session = Session.builder.configs(connection_parameters).create()
            logger.info("Successfully connected to Snowflake locally")
        return session
    except Exception as e:
        logger.error(f"Error connecting to Snowflake: {e}")
        return None

def get_schema_objects() -> pd.DataFrame:
    """Query Snowflake to get all tables and views in SNOWFLAKE_SAMPLE_DATA.TPCH_SF10 schema."""
    session = get_snowflake_session()
    if session is None:
        logger.error("Failed to connect to Snowflake")
        return pd.DataFrame({'error': ['Failed to connect to Snowflake']})
    
    try:
        # Query to get all tables and views from the specified schema
        query = """
        SELECT 
            table_name,
            table_type,
            row_count,
            bytes,
            created,
            table_schema,
            table_catalog
        FROM snowflake_sample_data.information_schema.tables 
        WHERE table_schema = 'TPCH_SF10' 
        AND table_catalog = 'SNOWFLAKE_SAMPLE_DATA'
        ORDER BY table_name
        """
        
        # Execute query and convert to pandas DataFrame
        result_df = session.sql(query).to_pandas()
        logger.info(f"Successfully retrieved {len(result_df)} tables/views from Snowflake schema")
        session.close()
        return result_df
        
    except Exception as e:
        logger.error(f"Error querying Snowflake: {e}")
        session.close() if session else None
        return pd.DataFrame({'error': [f'Query failed: {str(e)}']})
    
def get_table_list() -> list:
    """Get a simple list of table names from SNOWFLAKE_SAMPLE_DATA.TPCH_SF10 schema."""
    df = get_schema_objects()
    if 'error' in df.columns:
        return []
    return df['TABLE_NAME'].tolist() if not df.empty else []

# Initialize the Dash app with Bootstrap theme and dark/light mode support
THEME = dbc.themes.BOOTSTRAP
app = Dash(
    __name__,
    external_stylesheets=[THEME, dbc.icons.FONT_AWESOME],
    title="Snowflake Analytics Dashboard",
    suppress_callback_exceptions=True,  # Added for more robust callback handling
    assets_folder='static'  # Serve CSS from static folder
)
server = app.server  # Needed for deployment

# Add dedicated health check endpoint for container orchestration
# TODO: Make sure this actually works
@server.route('/health')
def health_check():
    """Health check endpoint for Docker and SPCS monitoring."""
    # Get current time in UTC
    now_utc = datetime.now(timezone.utc)
    
    # Use pytz for accurate NYC timezone (automatically handles EST/EDT)
    nyc_tz = pytz.timezone('America/New_York')
    now_nyc = now_utc.astimezone(nyc_tz)
    
    # Get timezone name and offset
    tz_name = now_nyc.strftime('%Z')  # EST or EDT
    tz_offset = now_nyc.strftime('%z')  # -0500 or -0400
    
    # Get library versions
    import dash
    import plotly
    import pandas as pd
    import snowflake.snowpark
    import dash_bootstrap_components as dbc
    import dash_ag_grid as dag
    
    versions = {
        'python': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'dash': dash.__version__,
        'plotly': plotly.__version__,
        'pandas': pd.__version__,
        'snowpark': snowflake.snowpark.__version__,
        'dash_bootstrap_components': dbc.__version__,
        'dash_ag_grid': dag.__version__,
        'pytz': pytz.__version__
    }
    
    return {
        'status': 'healthy', 
        'service': 'dash-app', 
        'port': PORT,
        'timestamp_utc': now_utc.isoformat(),
        'timestamp_NYC': now_nyc.isoformat(),
        'timezone': f'NYC {tz_name} ({tz_offset})',
        'versions': versions
    }, 200

# Define the layout with better organization and styling
app.layout = dbc.Container([
    # Store component for theme state
    dcc.Store(id='theme-store', data={'current_theme': 'snowflake'}),
    
    dbc.Row([
        dbc.Col([
            dbc.Navbar(
                dbc.Container([
                    html.Div([
                        html.I(className="fas fa-snowflake me-2", style={"color": "white"}),
                        html.H1('Snowflake Analytics Platform', className='d-inline mb-0', style={"color": "white", "fontWeight": "600"})
                    ], className='d-flex align-items-center'),
                    # Theme toggle button with three options
                    dbc.ButtonGroup([
                        dbc.Button(
                            html.I(className="fas fa-snowflake"),
                            id="snowflake-theme-btn",
                            color="primary",  # Highlighted by default
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
                    ], size="sm"),
                ], fluid=True),
                id="main-navbar",
                color="light",
                className="mb-4"
            ),
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-database me-2"),
                    "Data Source Selection"
                ], id="data-selection-header"),
                dbc.CardBody([
                    dbc.Label('Select Sample Data:', className='mb-2', html_for='sample-dropdown'),
                    dcc.Dropdown(
                        id='sample-dropdown',
                        options=[
                            {'label': 'Revenue by Region', 'value': 'revenue'},
                            {'label': 'Customer Growth', 'value': 'customers'}
                        ],
                        value='revenue',
                        clearable=False,
                        className='mb-3'
                    ),
                    # Toast for error messages with improved positioning
                    dbc.Toast(
                        id="error-toast",
                        header="Error",
                        is_open=False,
                        dismissable=True,
                        duration=4000,
                        icon="danger",
                        class_name="position-fixed top-0 end-0 m-3",
                        style={"z-index": 1999}
                    )
                ])
            ], id="data-selection-card", className='mb-4 shadow-sm')
        ], md=4),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-chart-line me-2"),
                    "Analytics & Insights"
                ], id="visualization-header"),
                dbc.CardBody([
                    # Loading spinner with improved configuration
                    dbc.Spinner(
                        dcc.Graph(
                            id='sample-graph',
                            config={
                                'displayModeBar': True,
                                'displaylogo': False,
                                'modeBarButtonsToRemove': ['lasso2d', 'select2d']
                            }
                        ),
                        color="primary",
                        type="border",
                        fullscreen=False,
                        spinner_class_name="spinner-grow",
                        delay_show=100  # Small delay to prevent flickering
                    )
                ])
            ], id="visualization-card", className='shadow-sm')
        ], md=8)
    ]),
    
    # Add AG Grid for Snowflake table list
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-snowflake me-2"),
                    "Snowflake Data Catalog (TPCH_SF10)"
                ], id="tables-header"),
                dbc.CardBody([
                    dbc.Spinner(
                        dag.AgGrid(
                            id="tables-grid",
                            rowData=[],
                            columnDefs=[
                                {"headerName": "Table Name", "field": "table_name", "sortable": True, "filter": True},
                                {"headerName": "Table Type", "field": "table_type", "sortable": True, "filter": True},
                                {"headerName": "Row Count", "field": "row_count", "sortable": True, "filter": True, "type": "numericColumn"},
                                {"headerName": "Size (Bytes)", "field": "bytes", "sortable": True, "filter": True, "type": "numericColumn"},
                                {"headerName": "Created", "field": "created", "sortable": True, "filter": True}
                            ],
                            className="ag-theme-alpine",
                            style={"height": "400px"},
                            dashGridOptions={
                                "pagination": True,
                                "paginationPageSize": 10,
                                "defaultColDef": {
                                    "resizable": True,
                                    "sortable": True,
                                    "filter": True
                                }
                            }
                        ),
                        color="primary",
                        type="border"
                    )
                ])
            ], id="tables-card", className='shadow-sm')
        ], md=12)
    ], className="mt-4")
], fluid=True, className="p-4")

@app.callback(
    [Output('theme-store', 'data'),
     Output('snowflake-theme-btn', 'color'),
     Output('light-theme-btn', 'color'),
     Output('dark-theme-btn', 'color')],
    [Input('snowflake-theme-btn', 'n_clicks'),
     Input('light-theme-btn', 'n_clicks'),
     Input('dark-theme-btn', 'n_clicks')],
    State('theme-store', 'data'),
    prevent_initial_call=False  # Allow initial call to set correct button states
)
def update_theme(snowflake_clicks, light_clicks, dark_clicks, theme_data):
    """Handle theme selection from three-button group."""
    if not theme_data:
        theme_data = {'current_theme': 'snowflake'}
    
    ctx = dash.callback_context
    if not ctx.triggered:
        # Initial state - use default theme
        theme = theme_data.get('current_theme', 'snowflake')
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'snowflake-theme-btn':
            theme = 'snowflake'
        elif button_id == 'light-theme-btn':
            theme = 'light'
        elif button_id == 'dark-theme-btn':
            theme = 'dark'
        else:
            theme = theme_data.get('current_theme', 'snowflake')
    
    # Set button colors based on active theme
    # Use info for inactive buttons to make them stand out more
    snowflake_color = "primary" if theme == 'snowflake' else "info"
    light_color = "warning" if theme == 'light' else "info"  # Yellow for sun icon
    dark_color = "dark" if theme == 'dark' else "info"
    
    return ({'current_theme': theme}, 
            snowflake_color, light_color, dark_color)

@app.callback(
    Output('tables-grid', 'rowData'),
    Input('tables-grid', 'id'),
    prevent_initial_call=False
)
def load_snowflake_tables(_):
    """Load Snowflake table data into the AG Grid."""
    try:
        logger.info("Loading Snowflake table data for AG Grid")
        df = get_schema_objects()
        if 'error' in df.columns:
            # Return error message as single row
            logger.warning("Error in Snowflake data retrieval for AG Grid")
            return [{"table_name": "Error", "table_type": "N/A", "row_count": 0, "bytes": 0, "created": df['error'].iloc[0]}]
        
        # Convert DataFrame to list of dictionaries for AG Grid
        # Convert column names to lowercase to match field names in columnDefs
        df.columns = df.columns.str.lower()
        logger.info(f"Successfully loaded {len(df)} rows for AG Grid")
        return df.to_dict('records')
        
    except Exception as e:
        logger.error(f"Failed to load AG Grid data: {str(e)}")
        return [{"table_name": "Error", "table_type": "N/A", "row_count": 0, "bytes": 0, "created": f"Failed to load data: {str(e)}"}]

@app.callback(
    [Output('sample-graph', 'figure'),
     Output('error-toast', 'is_open'),
     Output('error-toast', 'children')],
    [Input('sample-dropdown', 'value'),
     Input('theme-store', 'data')],
    prevent_initial_call=False
)
def update_graph(selected_value: str, theme_data: Dict[str, str]) -> Tuple[Any, bool, str]:
    """Update the graph based on selection and current theme."""
    try:
        # Sample data - in production, you would query Snowflake here
        if selected_value == 'revenue':
            df = pd.DataFrame({
                'Region': ['North', 'South', 'East', 'West'],
                'Revenue': [120000, 85000, 95000, 115000]
            })
            title = 'Revenue by Region'
            x, y = 'Region', 'Revenue'
        else:
            df = pd.DataFrame({
                'Quarter': ['Q1', 'Q2', 'Q3', 'Q4'],
                'Customers': [1200, 1450, 1800, 2100]
            })
            title = 'Customer Growth by Quarter'
            x, y = 'Quarter', 'Customers'
        
        # Determine theme-based colors
        current_theme = theme_data.get('current_theme', 'snowflake') if theme_data else 'snowflake'
        
        if current_theme == 'dark':
            template = 'plotly_dark'
            text_color = 'white'
        elif current_theme == 'snowflake':
            template = 'plotly_white'
            text_color = '#1E293B'
        else:  # light
            template = 'plotly_white'
            text_color = 'black'
        
        # Using improved template system in plotly 6.1.2
        fig = px.bar(
            df, 
            x=x, 
            y=y, 
            title=title,
            template=template,
            labels={x: x.title(), y: y.title()},  # Better axis labels
            height=400  # Fixed height for better layout
        )
        
        # Enhanced figure layout with better defaults
        fig.update_layout(
            title_x=0.5,
            margin=dict(t=50, l=50, r=30, b=50),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            hovermode='closest',
            showlegend=False,  # Hide legend for single trace
            # Improved font settings
            font=dict(
                family="system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
                color=text_color
            )
        )
        
        # Theme-specific bar styling
        if current_theme == 'snowflake':
            marker_color = '#29B5E8'  # Snowflake blue
            marker_line_color = '#1E3A8A'  # Snowflake dark blue
        elif current_theme == 'dark':
            marker_color = 'rgb(100, 149, 237)'
            marker_line_color = 'rgb(135, 206, 250)'
        else:  # light
            marker_color = 'rgb(59, 89, 152)'
            marker_line_color = 'rgb(8, 48, 107)'
        
        fig.update_traces(
            marker_color=marker_color,
            marker_line_color=marker_line_color,
            marker_line_width=1.5,
            opacity=0.8
        )
        
        return fig, False, ''  # No error
        
    except Exception as e:
        return px.bar(title='Error loading data'), True, str(e)

@app.callback(
    Output('tables-grid', 'className'),
    Input('theme-store', 'data'),
    prevent_initial_call=False
)
def update_grid_theme(theme_data: Dict[str, str]) -> str:
    """Update AG Grid theme based on current theme."""
    if not theme_data:
        return "ag-theme-alpine"
    
    current_theme = theme_data.get('current_theme', 'snowflake')
    
    if current_theme == 'dark':
        return "ag-theme-alpine-dark"
    else:  # 'snowflake' or 'light' both use alpine
        return "ag-theme-alpine"

# External CSS reference
# All styling is now moved to static/styles.css for better maintainability

# Add external CSS and fonts to the app
app.index_string = '''<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="/assets/styles.css">
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>'''

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
    Output('theme-store', 'data', allow_duplicate=True),
    Input('theme-store', 'data'),
    prevent_initial_call=True
)

if __name__ == '__main__':
    logger.info(f"Starting Snowflake Dash Application on port {PORT}")
    app.run(debug=True, host='0.0.0.0', port=PORT)