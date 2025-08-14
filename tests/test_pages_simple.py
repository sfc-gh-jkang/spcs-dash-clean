"""
Simplified tests for pages modules focusing on layout functions.

This test suite validates basic page functionality that we know exists:
- Layout function availability
- Basic structure validation
"""

from unittest.mock import patch
import dash_bootstrap_components as dbc


class TestPagesLayoutFunctions:
    """Test that page layout functions exist and return valid structures."""

    def test_analytics_layout_exists(self):
        """Test that analytics layout function exists and returns a container."""
        # Mock dash.register_page to prevent registration errors
        with patch("dash.register_page"):
            from pages import analytics

        # Test layout function exists
        assert hasattr(analytics, "layout")
        assert callable(analytics.layout)

        # Test layout returns container
        layout_result = analytics.layout()
        assert isinstance(layout_result, dbc.Container)
        assert layout_result.fluid is True

    def test_dashboard_layout_exists(self):
        """Test that dashboard layout function exists and returns a container."""
        # Mock dash.register_page to prevent registration errors
        with patch("dash.register_page"):
            from pages import dashboard

        # Test layout function exists
        assert hasattr(dashboard, "layout")
        assert callable(dashboard.layout)

        # Test layout returns container
        layout_result = dashboard.layout()
        assert isinstance(layout_result, dbc.Container)
        assert layout_result.fluid is True

    def test_data_browser_layout_exists(self):
        """Test that data browser layout function exists and returns a container."""
        # Mock dash.register_page to prevent registration errors
        with patch("dash.register_page"):
            from pages import data_browser

        # Test layout function exists
        assert hasattr(data_browser, "layout")
        assert callable(data_browser.layout)

        # Test layout returns container
        layout_result = data_browser.layout()
        assert isinstance(layout_result, dbc.Container)
        assert layout_result.fluid is True

    def test_analytics_layout_structure(self):
        """Test analytics layout structure."""
        with patch("dash.register_page"):
            from pages import analytics

        layout_result = analytics.layout()

        # Check main container structure
        assert len(layout_result.children) == 3  # navbar, content, toast

        # Get the page content
        page_content = layout_result.children[1]
        assert hasattr(page_content, "className")
        assert "page-content" in page_content.className

    def test_dashboard_layout_structure(self):
        """Test dashboard layout structure."""
        with patch("dash.register_page"):
            from pages import dashboard

        layout_result = dashboard.layout()

        # Check main container structure
        assert len(layout_result.children) == 3  # navbar, content, toast

        # Get the page content
        page_content = layout_result.children[1]
        assert hasattr(page_content, "className")
        assert "page-content" in page_content.className

    def test_data_browser_layout_structure(self):
        """Test data browser layout structure."""
        with patch("dash.register_page"):
            from pages import data_browser

        layout_result = data_browser.layout()

        # Check main container structure
        assert len(layout_result.children) == 3  # navbar, content, toast

        # Get the page content
        page_content = layout_result.children[1]
        assert hasattr(page_content, "className")
        assert "page-content" in page_content.className

    def test_all_pages_use_create_page_container(self):
        """Test that all pages use the create_page_container function."""
        with patch("dash.register_page"):
            from pages import analytics, dashboard, data_browser

        # All layouts should return containers with the same structure
        analytics_layout = analytics.layout()
        dashboard_layout = dashboard.layout()
        data_browser_layout = data_browser.layout()

        # All should be containers
        assert isinstance(analytics_layout, dbc.Container)
        assert isinstance(dashboard_layout, dbc.Container)
        assert isinstance(data_browser_layout, dbc.Container)

        # All should have the same number of top-level children
        assert len(analytics_layout.children) == 3
        assert len(dashboard_layout.children) == 3
        assert len(data_browser_layout.children) == 3

    def test_page_containers_no_duplicate_theme_stores(self):
        """Test that individual pages don't create duplicate theme stores."""
        with patch("dash.register_page"):
            from pages import analytics, dashboard, data_browser

        layouts = [analytics.layout(), dashboard.layout(), data_browser.layout()]

        for layout in layouts:
            # Pages should not have theme stores (to avoid duplicates)
            # First child should be navbar, not theme store
            navbar = layout.children[0]
            assert hasattr(navbar, "id")
            assert navbar.id == "main-navbar"

    def test_page_containers_have_navbars(self):
        """Test that all pages include navigation bars."""
        with patch("dash.register_page"):
            from pages import analytics, dashboard, data_browser

        layouts = [analytics.layout(), dashboard.layout(), data_browser.layout()]

        for layout in layouts:
            # First child should be navbar
            navbar = layout.children[0]
            assert hasattr(navbar, "id")
            assert navbar.id == "main-navbar"

    def test_page_containers_have_error_toasts(self):
        """Test that all pages include error toasts."""
        with patch("dash.register_page"):
            from pages import analytics, dashboard, data_browser

        layouts = [analytics.layout(), dashboard.layout(), data_browser.layout()]

        for layout in layouts:
            # Third child should be error toast
            error_toast = layout.children[2]
            assert hasattr(error_toast, "id")
            assert "error-toast" in error_toast.id


class TestPageModuleImports:
    """Test that page modules can be imported successfully."""

    def test_analytics_module_import(self):
        """Test that analytics module can be imported."""
        with patch("dash.register_page"):
            from pages import analytics

        # Module should have required attributes
        assert hasattr(analytics, "layout")
        assert hasattr(analytics, "dash")

    def test_dashboard_module_import(self):
        """Test that dashboard module can be imported."""
        with patch("dash.register_page"):
            from pages import dashboard

        # Module should have required attributes
        assert hasattr(dashboard, "layout")
        assert hasattr(dashboard, "dash")

    def test_data_browser_module_import(self):
        """Test that data browser module can be imported."""
        with patch("dash.register_page"):
            from pages import data_browser

        # Module should have required attributes
        assert hasattr(data_browser, "layout")
        assert hasattr(data_browser, "dash")

    def test_all_modules_import_utilities(self):
        """Test that all page modules import required utilities."""
        with patch("dash.register_page"):
            from pages import analytics, dashboard, data_browser

        # All modules should import from components.layout
        # This is tested by verifying they can create layouts successfully
        for module in [analytics, dashboard, data_browser]:
            layout = module.layout()
            assert layout is not None


class TestPageLayoutConsistency:
    """Test consistency across page layouts."""

    def test_consistent_page_structure(self):
        """Test that all pages have consistent structure."""
        with patch("dash.register_page"):
            from pages import analytics, dashboard, data_browser

        layouts = {
            "analytics": analytics.layout(),
            "dashboard": dashboard.layout(),
            "data_browser": data_browser.layout(),
        }

        for page_name, layout in layouts.items():
            # All pages should use same container structure
            assert isinstance(
                layout, dbc.Container
            ), f"{page_name} should use dbc.Container"
            assert layout.fluid is True, f"{page_name} should have fluid=True"
            assert (
                len(layout.children) == 3
            ), f"{page_name} should have 3 top-level children"

            # Check class name
            assert "p-4" in layout.className, f"{page_name} should have p-4 class"

    def test_consistent_component_ids(self):
        """Test that common components have consistent IDs."""
        with patch("dash.register_page"):
            from pages import analytics, dashboard, data_browser

        layouts = [analytics.layout(), dashboard.layout(), data_browser.layout()]

        for layout in layouts:
            # Navbar should have consistent ID (now first child)
            navbar = layout.children[0]
            assert navbar.id == "main-navbar"

            # Error toast should have error-toast in ID (now third child)
            error_toast = layout.children[2]
            assert "error-toast" in error_toast.id

    def test_page_content_structure(self):
        """Test that page content is properly structured."""
        with patch("dash.register_page"):
            from pages import analytics, dashboard, data_browser

        layouts = [analytics.layout(), dashboard.layout(), data_browser.layout()]

        for layout in layouts:
            # Page content should be second child
            page_content = layout.children[1]
            assert hasattr(page_content, "className")
            assert "page-content" in page_content.className

            # Page content should have children
            assert hasattr(page_content, "children")
            assert page_content.children is not None
