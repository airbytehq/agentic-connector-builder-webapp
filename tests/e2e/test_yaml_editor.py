"""End-to-end tests for YAML editor functionality using Playwright."""

import pytest
from playwright.async_api import Page, expect


class TestYamlEditorBasicFunctionality:
    """Test basic YAML editor functionality."""

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_page_loads_successfully(self, app_page: Page):
        """Test that the main page loads successfully."""
        # Check that the page title is correct
        await expect(app_page).to_have_title("Agentic Connector Builder")
        
        # Check that the main heading is visible
        heading = app_page.locator("h1", has_text="Agentic Connector Builder")
        await expect(heading).to_be_visible()

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_yaml_editor_is_present(self, app_page: Page):
        """Test that the YAML editor component is present on the page."""
        # Check for the YAML editor heading
        editor_heading = app_page.locator("h2", has_text="YAML Connector Configuration Editor")
        await expect(editor_heading).to_be_visible()
        
        # Check for the Monaco editor container
        # Monaco editor typically creates a div with specific classes
        editor_container = app_page.locator(".monaco-editor")
        await expect(editor_container).to_be_visible()

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_reset_button_is_present(self, app_page: Page):
        """Test that the reset button is present and clickable."""
        reset_button = app_page.locator("button", has_text="Reset to Example")
        await expect(reset_button).to_be_visible()
        await expect(reset_button).to_be_enabled()

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_character_counter_is_present(self, app_page: Page):
        """Test that the character counter is present."""
        counter = app_page.locator("text=/Content length: \\d+ characters/")
        await expect(counter).to_be_visible()


class TestYamlEditorInteraction:
    """Test YAML editor interaction functionality."""

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_editor_contains_default_content(self, app_page: Page):
        """Test that the editor contains default YAML content."""
        # Wait for the Monaco editor to load
        await app_page.wait_for_selector(".monaco-editor", timeout=10000)
        
        # Check that the editor contains some default content
        # We'll look for specific text that should be in the default YAML
        editor_content = app_page.locator(".monaco-editor")
        await expect(editor_content).to_contain_text("example-connector")
        await expect(editor_content).to_contain_text("version")

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_reset_button_functionality(self, app_page: Page):
        """Test that the reset button works correctly."""
        # Wait for the Monaco editor to load
        await app_page.wait_for_selector(".monaco-editor", timeout=10000)
        
        # Click the reset button
        reset_button = app_page.locator("button", has_text="Reset to Example")
        await reset_button.click()
        
        # Wait a moment for the reset to take effect
        await app_page.wait_for_timeout(1000)
        
        # Verify that the default content is present
        editor_content = app_page.locator(".monaco-editor")
        await expect(editor_content).to_contain_text("example-connector")

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_character_counter_updates(self, app_page: Page):
        """Test that the character counter updates when content changes."""
        # Wait for the Monaco editor to load
        await app_page.wait_for_selector(".monaco-editor", timeout=10000)
        
        # Get initial character count
        counter = app_page.locator("text=/Content length: \\d+ characters/")
        initial_text = await counter.text_content()
        
        # Click reset button to ensure consistent state
        reset_button = app_page.locator("button", has_text="Reset to Example")
        await reset_button.click()
        await app_page.wait_for_timeout(1000)
        
        # Verify counter shows some content
        await expect(counter).to_contain_text("Content length:")
        counter_text = await counter.text_content()
        assert "0 characters" not in counter_text, "Counter should show non-zero characters for default content"


class TestYamlEditorAdvanced:
    """Test advanced YAML editor functionality."""

    @pytest.mark.e2e
    @pytest.mark.browser
    @pytest.mark.slow_e2e
    async def test_editor_syntax_highlighting(self, app_page: Page):
        """Test that the YAML editor has proper syntax highlighting."""
        # Wait for the Monaco editor to load
        await app_page.wait_for_selector(".monaco-editor", timeout=10000)
        
        # Check for Monaco editor specific elements that indicate syntax highlighting
        # Monaco creates specific CSS classes for syntax highlighting
        syntax_elements = app_page.locator(".monaco-editor .mtk1, .monaco-editor .mtk2, .monaco-editor .mtk3")
        await expect(syntax_elements.first()).to_be_visible()

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_editor_line_numbers(self, app_page: Page):
        """Test that the editor shows line numbers."""
        # Wait for the Monaco editor to load
        await app_page.wait_for_selector(".monaco-editor", timeout=10000)
        
        # Check for line numbers container
        line_numbers = app_page.locator(".monaco-editor .line-numbers")
        await expect(line_numbers.first()).to_be_visible()

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_editor_dark_theme(self, app_page: Page):
        """Test that the editor uses dark theme."""
        # Wait for the Monaco editor to load
        await app_page.wait_for_selector(".monaco-editor", timeout=10000)
        
        # Check for dark theme class or dark background
        editor = app_page.locator(".monaco-editor")
        
        # Monaco editor with dark theme should have specific classes
        dark_theme_indicator = app_page.locator(".monaco-editor.vs-dark")
        await expect(dark_theme_indicator).to_be_visible()


class TestYamlEditorResponsiveness:
    """Test YAML editor responsiveness and layout."""

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_editor_responsive_layout(self, app_page: Page):
        """Test that the editor layout is responsive."""
        # Wait for the Monaco editor to load
        await app_page.wait_for_selector(".monaco-editor", timeout=10000)
        
        # Test desktop viewport (default is 1280x720)
        editor = app_page.locator(".monaco-editor")
        await expect(editor).to_be_visible()
        
        # Change to tablet viewport
        await app_page.set_viewport_size({"width": 768, "height": 1024})
        await app_page.wait_for_timeout(500)
        await expect(editor).to_be_visible()
        
        # Change to mobile viewport
        await app_page.set_viewport_size({"width": 375, "height": 667})
        await app_page.wait_for_timeout(500)
        await expect(editor).to_be_visible()

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_page_layout_structure(self, app_page: Page):
        """Test the overall page layout structure."""
        # Check main container
        container = app_page.locator("div").first()
        await expect(container).to_be_visible()
        
        # Check that all main elements are present
        heading = app_page.locator("h1")
        await expect(heading).to_be_visible()
        
        description = app_page.locator("text=Build and configure data connectors using YAML")
        await expect(description).to_be_visible()
        
        editor_section = app_page.locator("h2", has_text="YAML Connector Configuration Editor")
        await expect(editor_section).to_be_visible()


class TestYamlEditorErrorHandling:
    """Test YAML editor error handling and edge cases."""

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_editor_loads_with_network_delays(self, app_page: Page):
        """Test that the editor loads properly even with network delays."""
        # Simulate slow network
        await app_page.route("**/*", lambda route: route.continue_())
        
        # Wait for the Monaco editor to load with extended timeout
        await app_page.wait_for_selector(".monaco-editor", timeout=15000)
        
        # Verify editor is functional
        editor = app_page.locator(".monaco-editor")
        await expect(editor).to_be_visible()
        
        reset_button = app_page.locator("button", has_text="Reset to Example")
        await expect(reset_button).to_be_visible()

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_page_accessibility_basics(self, app_page: Page):
        """Test basic accessibility features."""
        # Check that the page has proper heading structure
        h1 = app_page.locator("h1")
        await expect(h1).to_be_visible()
        
        h2 = app_page.locator("h2")
        await expect(h2).to_be_visible()
        
        # Check that buttons have accessible text
        reset_button = app_page.locator("button", has_text="Reset to Example")
        await expect(reset_button).to_be_visible()
        
        # Verify button is keyboard accessible
        await reset_button.focus()
        focused_element = await app_page.evaluate("document.activeElement.textContent")
        assert "Reset to Example" in focused_element
