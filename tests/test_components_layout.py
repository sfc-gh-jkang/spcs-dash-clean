"""
Tests for components/layout.py module.

This test suite validates the layout component functions including:
- Navigation bar creation
- Theme store creation
- Error toast creation
- Page container creation
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

from components.layout import (
    create_navbar,
    create_theme_store,
    create_error_toast,
    create_page_container,
)


class TestNavbarCreation:
    """Test navbar creation functionality."""

    def test_create_navbar_structure(self):
        """Test that create_navbar returns expected structure."""
        navbar = create_navbar()

        # Check it's a Navbar component
        assert isinstance(navbar, dbc.Navbar)
        assert navbar.id == "main-navbar"
        assert navbar.color == "light"

        # Check the structure contains a Container
        container = navbar.children
        assert isinstance(container, dbc.Container)
        assert container.fluid is True

        # Check container has the expected children (brand, nav, theme buttons)
        container_children = container.children
        assert len(container_children) == 3  # Brand, Nav, ButtonGroup

    def test_navbar_brand_section(self):
        """Test the brand section of the navbar."""
        navbar = create_navbar()
        container = navbar.children
        brand_section = container.children[0]

        assert isinstance(brand_section, html.Div)
        assert "d-flex align-items-center" in brand_section.className

        # Check brand contains icon and title
        brand_children = brand_section.children
        assert len(brand_children) == 2

        # Check icon
        icon = brand_children[0]
        assert isinstance(icon, html.I)
        assert "fas fa-snowflake" in icon.className

        # Check title
        title = brand_children[1]
        assert isinstance(title, html.H1)
        assert title.children == "Snowflake Analytics Platform"

    def test_navbar_navigation_links(self):
        """Test the navigation links section."""
        navbar = create_navbar()
        container = navbar.children
        nav_section = container.children[1]

        assert isinstance(nav_section, dbc.Nav)
        assert nav_section.navbar is True

        # Check nav items
        nav_items = nav_section.children
        assert len(nav_items) == 3

        # Check each nav item
        expected_links = [
            ("Dashboard", "/"),
            ("Data Browser", "/data-browser"),
            ("Analytics", "/analytics"),
        ]

        for i, (expected_text, expected_href) in enumerate(expected_links):
            nav_item = nav_items[i]
            assert isinstance(nav_item, dbc.NavItem)

            nav_link = nav_item.children
            assert isinstance(nav_link, dbc.NavLink)
            assert nav_link.children == expected_text
            assert nav_link.href == expected_href
            assert nav_link.active == "exact"

    def test_navbar_theme_buttons(self):
        """Test the theme button group."""
        navbar = create_navbar()
        container = navbar.children
        button_group = container.children[2]

        assert isinstance(button_group, dbc.ButtonGroup)
        assert button_group.size == "sm"

        # Check theme buttons
        buttons = button_group.children
        assert len(buttons) == 3

        expected_buttons = [
            ("snowflake-theme-btn", "fas fa-snowflake", "primary", "Snowflake theme"),
            ("light-theme-btn", "fas fa-sun", "info", "Light theme"),
            ("dark-theme-btn", "fas fa-moon", "info", "Dark theme"),
        ]

        for i, (
            expected_id,
            expected_icon,
            expected_color,
            expected_title,
        ) in enumerate(expected_buttons):
            button = buttons[i]
            assert isinstance(button, dbc.Button)
            assert button.id == expected_id
            assert button.color == expected_color
            assert button.outline is True
            assert button.size == "sm"
            assert button.title == expected_title
            assert "theme-btn" in button.className

            # Check button icon
            icon = button.children
            assert isinstance(icon, html.I)
            assert expected_icon in icon.className


class TestThemeStore:
    """Test theme store creation functionality."""

    def test_create_theme_store_structure(self):
        """Test that create_theme_store returns expected structure."""
        store = create_theme_store()

        assert isinstance(store, dcc.Store)
        assert store.id == "theme-store"
        assert store.data == {"current_theme": "snowflake"}

    def test_theme_store_default_data(self):
        """Test the default theme data."""
        store = create_theme_store()

        assert "current_theme" in store.data
        assert store.data["current_theme"] == "snowflake"


class TestErrorToast:
    """Test error toast creation functionality."""

    def test_create_error_toast_default(self):
        """Test error toast creation with default parameters."""
        toast = create_error_toast()

        assert isinstance(toast, dbc.Toast)
        assert toast.id == "error-toast"
        assert toast.header == "Error"
        assert toast.is_open is False
        assert toast.dismissable is True
        assert toast.duration == 4000
        assert toast.icon == "danger"
        assert "position-fixed top-0 end-0 m-3" in toast.class_name
        assert toast.style == {"z-index": 1999}

    def test_create_error_toast_with_suffix(self):
        """Test error toast creation with page suffix."""
        toast = create_error_toast(page_suffix="analytics")

        assert isinstance(toast, dbc.Toast)
        assert toast.id == "error-toast-analytics"
        assert toast.header == "Error"

    def test_create_error_toast_empty_suffix(self):
        """Test error toast creation with empty suffix."""
        toast = create_error_toast(page_suffix="")

        assert isinstance(toast, dbc.Toast)
        assert toast.id == "error-toast"

    def test_create_error_toast_multiple_suffixes(self):
        """Test error toast creation with various suffixes."""
        suffixes = ["dashboard", "data-browser", "analytics", "test-page"]

        for suffix in suffixes:
            toast = create_error_toast(page_suffix=suffix)
            expected_id = f"error-toast-{suffix}"
            assert toast.id == expected_id


class TestPageContainer:
    """Test page container creation functionality."""

    def test_create_page_container_structure(self):
        """Test page container creation with default parameters."""
        test_children = [html.Div("Test content")]
        container = create_page_container(test_children)

        assert isinstance(container, dbc.Container)
        assert container.fluid is True
        assert "p-4" in container.className

        # Check container children structure
        container_children = container.children
        assert len(container_children) == 3

        # Check each component
        navbar = container_children[0]
        page_content = container_children[1]
        error_toast = container_children[2]

        assert isinstance(navbar, dbc.Navbar)
        assert navbar.id == "main-navbar"

        assert isinstance(page_content, html.Div)
        assert "page-content" in page_content.className
        assert page_content.children == test_children

        assert isinstance(error_toast, dbc.Toast)
        assert error_toast.id == "error-toast"

    def test_create_page_container_with_suffix(self):
        """Test page container creation with page suffix."""
        test_children = [html.Div("Test content")]
        container = create_page_container(
            test_children, page_title="Custom Title", page_suffix="analytics"
        )

        assert isinstance(container, dbc.Container)

        # Check error toast has correct suffix
        error_toast = container.children[2]
        assert isinstance(error_toast, dbc.Toast)
        assert error_toast.id == "error-toast-analytics"

    def test_create_page_container_with_complex_children(self):
        """Test page container with complex children structure."""
        complex_children = [
            html.Div(
                [
                    html.H1("Test Page"),
                    dbc.Card(
                        [dbc.CardHeader("Test Card"), dbc.CardBody("Test Content")]
                    ),
                    dbc.Row([dbc.Col("Column 1"), dbc.Col("Column 2")]),
                ]
            )
        ]

        container = create_page_container(complex_children)

        # Check the page content contains our complex structure
        page_content = container.children[1]
        assert page_content.children == complex_children

    def test_create_page_container_empty_children(self):
        """Test page container with empty children."""
        container = create_page_container([])

        page_content = container.children[1]
        assert page_content.children == []

    def test_create_page_container_multiple_children(self):
        """Test page container with multiple children."""
        multiple_children = [
            html.H1("Title"),
            html.P("Paragraph"),
            html.Div("Div content"),
            dbc.Alert("Alert message"),
        ]

        container = create_page_container(multiple_children)

        page_content = container.children[1]
        assert page_content.children == multiple_children
        assert len(page_content.children) == 4


class TestLayoutIntegration:
    """Test integration between layout components."""

    def test_complete_layout_structure(self):
        """Test that all components work together properly."""
        test_content = [html.H1("Test Page"), html.P("This is a test page")]

        # Create complete layout
        container = create_page_container(
            test_content, page_title="Test Page", page_suffix="test"
        )

        # Verify all components are present and properly structured
        assert isinstance(container, dbc.Container)
        assert len(container.children) == 3

        # Navbar with all components
        navbar = container.children[0]
        navbar_container = navbar.children
        brand, nav, buttons = navbar_container.children

        # Brand
        assert len(brand.children) == 2  # Icon + title

        # Navigation
        assert len(nav.children) == 3  # 3 nav items

        # Theme buttons
        assert len(buttons.children) == 3  # 3 theme buttons

        # Page content
        page_content = container.children[1]
        assert page_content.children == test_content

        # Error toast
        error_toast = container.children[2]
        assert error_toast.id == "error-toast-test"

    def test_layout_component_ids_unique(self):
        """Test that component IDs are unique and properly formatted."""
        container1 = create_page_container([], page_suffix="page1")
        container2 = create_page_container([], page_suffix="page2")

        # Extract error toast IDs
        toast1_id = container1.children[2].id
        toast2_id = container2.children[2].id

        assert toast1_id == "error-toast-page1"
        assert toast2_id == "error-toast-page2"
        assert toast1_id != toast2_id

    def test_layout_consistency(self):
        """Test that layout components are consistent across calls."""
        # Create multiple containers
        containers = []
        for i in range(3):
            container = create_page_container([html.Div(f"Content {i}")])
            containers.append(container)

        # All should have the same structure
        for container in containers:
            assert len(container.children) == 3
            assert isinstance(container.children[0], dbc.Navbar)
            assert isinstance(container.children[1], html.Div)
            assert isinstance(container.children[2], dbc.Toast)
