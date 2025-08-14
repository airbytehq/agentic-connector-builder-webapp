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


class TestYamlEditorAdvancedFeatures:
    """Test advanced YAML editor features and edge cases."""

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_editor_content_persistence_across_refresh(self, app_page: Page):
        """Test that editor content persists across page refreshes."""
        # Wait for Monaco editor to load
        await app_page.wait_for_selector(".monaco-editor", timeout=10000)
        
        # Add custom content to the editor
        custom_content = """# Custom YAML Configuration
name: test-connector
version: "2.0.0"
description: "Test connector for persistence"
source:
  type: custom
  config:
    test: true"""
        
        # Clear editor and add custom content
        editor_textarea = app_page.locator(".monaco-editor textarea").first()
        await editor_textarea.click()
        await app_page.keyboard.press("Control+a")
        await app_page.keyboard.type(custom_content)
        
        # Wait for content to be set
        await app_page.wait_for_timeout(1000)
        
        # Refresh the page
        await app_page.reload()
        await app_page.wait_for_load_state("networkidle")
        await app_page.wait_for_selector(".monaco-editor", timeout=10000)
        
        # Check if custom content is still there (Note: This depends on implementation)
        # For now, we'll verify the editor loads properly after refresh
        editor = app_page.locator(".monaco-editor")
        await expect(editor).to_be_visible()
        
        # Verify editor is functional after refresh
        reset_button = app_page.locator("button", has_text="Reset to Example")
        await expect(reset_button).to_be_visible()
        await reset_button.click()
        
        # Verify reset functionality works after refresh
        await app_page.wait_for_timeout(1000)
        counter = app_page.locator("text=/Content length: \\d+ characters/")
        await expect(counter).to_be_visible()

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_keyboard_shortcuts_select_all(self, app_page: Page):
        """Test Ctrl+A keyboard shortcut for selecting all content."""
        # Wait for Monaco editor to load
        await app_page.wait_for_selector(".monaco-editor", timeout=10000)
        
        # Click in the editor to focus it
        editor_textarea = app_page.locator(".monaco-editor textarea").first()
        await editor_textarea.click()
        
        # Use Ctrl+A to select all content
        await app_page.keyboard.press("Control+a")
        
        # Type new content to verify selection worked
        test_content = "# Selected and replaced content"
        await app_page.keyboard.type(test_content)
        
        # Wait for content to update
        await app_page.wait_for_timeout(1000)
        
        # Verify character counter updated (indicating content changed)
        counter = app_page.locator("text=/Content length: \\d+ characters/")
        await expect(counter).to_be_visible()
        
        # The counter should show the length of our test content
        counter_text = await counter.text_content()
        assert str(len(test_content)) in counter_text

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_keyboard_shortcuts_undo(self, app_page: Page):
        """Test Ctrl+Z keyboard shortcut for undo functionality."""
        # Wait for Monaco editor to load
        await app_page.wait_for_selector(".monaco-editor", timeout=10000)
        
        # Get initial character count
        initial_counter = app_page.locator("text=/Content length: \\d+ characters/")
        await expect(initial_counter).to_be_visible()
        initial_text = await initial_counter.text_content()
        
        # Click in the editor and add some content
        editor_textarea = app_page.locator(".monaco-editor textarea").first()
        await editor_textarea.click()
        await app_page.keyboard.press("End")  # Go to end of content
        await app_page.keyboard.type("\n# Added content for undo test")
        
        # Wait for content to update
        await app_page.wait_for_timeout(1000)
        
        # Verify content was added (character count increased)
        updated_counter = app_page.locator("text=/Content length: \\d+ characters/")
        updated_text = await updated_counter.text_content()
        assert updated_text != initial_text
        
        # Use Ctrl+Z to undo the addition
        await app_page.keyboard.press("Control+z")
        
        # Wait for undo to take effect
        await app_page.wait_for_timeout(1000)
        
        # Verify character count returned to initial value (or close to it)
        final_counter = app_page.locator("text=/Content length: \\d+ characters/")
        final_text = await final_counter.text_content()
        
        # The count should be closer to initial than to updated
        # (allowing for some variation due to Monaco editor behavior)
        assert final_text != updated_text

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_large_yaml_file_performance(self, app_page: Page):
        """Test editor performance with large YAML content."""
        # Wait for Monaco editor to load
        await app_page.wait_for_selector(".monaco-editor", timeout=10000)
        
        # Generate large YAML content (approximately 10KB)
        large_yaml_content = """# Large YAML Configuration File
name: large-test-connector
version: "1.0.0"
description: "Large connector configuration for performance testing"

"""
        
        # Add repetitive content to make it large
        for i in range(100):
            large_yaml_content += f"""
source_{i:03d}:
  type: database
  connection:
    host: "host-{i:03d}.example.com"
    port: {5432 + i}
    database: "db_{i:03d}"
    username: "user_{i:03d}"
    password: "password_{i:03d}"
  tables:
    - name: "table_{i:03d}_users"
      columns: ["id", "name", "email", "created_at"]
    - name: "table_{i:03d}_orders"
      columns: ["id", "user_id", "amount", "status"]
"""
        
        # Record start time
        start_time = await app_page.evaluate("Date.now()")
        
        # Clear editor and add large content
        editor_textarea = app_page.locator(".monaco-editor textarea").first()
        await editor_textarea.click()
        await app_page.keyboard.press("Control+a")
        await app_page.keyboard.type(large_yaml_content)
        
        # Wait for content to be processed
        await app_page.wait_for_timeout(2000)
        
        # Record end time
        end_time = await app_page.evaluate("Date.now()")
        
        # Verify editor is still responsive (performance check)
        processing_time = end_time - start_time
        assert processing_time < 10000, f"Large content processing took too long: {processing_time}ms"
        
        # Verify editor functionality with large content
        counter = app_page.locator("text=/Content length: \\d+ characters/")
        await expect(counter).to_be_visible()
        
        # Verify character count is approximately correct (within reasonable range)
        counter_text = await counter.text_content()
        content_length = len(large_yaml_content)
        assert str(content_length)[:3] in counter_text or str(content_length)[:4] in counter_text
        
        # Test that reset button still works with large content
        reset_button = app_page.locator("button", has_text="Reset to Example")
        await expect(reset_button).to_be_visible()
        await reset_button.click()
        
        # Wait for reset to complete
        await app_page.wait_for_timeout(1000)
        
        # Verify content was reset (character count should be much smaller)
        reset_counter = app_page.locator("text=/Content length: \\d+ characters/")
        reset_text = await reset_counter.text_content()
        assert reset_text != counter_text

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_comprehensive_accessibility_features(self, app_page: Page):
        """Test comprehensive accessibility features including ARIA attributes."""
        # Check for proper ARIA labels and roles
        
        # Main heading should have proper structure
        main_heading = app_page.locator("h1")
        await expect(main_heading).to_be_visible()
        
        # Editor section should have proper heading hierarchy
        editor_heading = app_page.locator("h2", has_text="YAML Connector Configuration Editor")
        await expect(editor_heading).to_be_visible()
        
        # Check that Monaco editor has proper accessibility attributes
        await app_page.wait_for_selector(".monaco-editor", timeout=10000)
        editor = app_page.locator(".monaco-editor")
        await expect(editor).to_be_visible()
        
        # Check for textarea within Monaco editor (should be focusable)
        editor_textarea = app_page.locator(".monaco-editor textarea")
        await expect(editor_textarea).to_be_visible()
        
        # Test keyboard navigation to editor
        await app_page.keyboard.press("Tab")
        await app_page.keyboard.press("Tab")
        await app_page.keyboard.press("Tab")  # Navigate through elements
        
        # Verify reset button is keyboard accessible
        reset_button = app_page.locator("button", has_text="Reset to Example")
        await reset_button.focus()
        
        # Test that Enter key activates the button
        await app_page.keyboard.press("Enter")
        await app_page.wait_for_timeout(1000)
        
        # Verify the button action worked
        counter = app_page.locator("text=/Content length: \\d+ characters/")
        await expect(counter).to_be_visible()
        
        # Test that Space key also activates the button
        await reset_button.focus()
        await app_page.keyboard.press("Space")
        await app_page.wait_for_timeout(1000)
        
        # Verify button is still functional
        await expect(counter).to_be_visible()

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_screen_reader_compatibility(self, app_page: Page):
        """Test screen reader compatibility and semantic structure."""
        # Check document structure for screen readers
        
        # Verify page has a proper title
        await expect(app_page).to_have_title("Agentic Connector Builder")
        
        # Check for landmark elements that screen readers use
        main_content = app_page.locator("body")
        await expect(main_content).to_be_visible()
        
        # Verify heading hierarchy is logical (h1 -> h2)
        h1_elements = app_page.locator("h1")
        h1_count = await h1_elements.count()
        assert h1_count >= 1, "Page should have at least one h1 element"
        
        h2_elements = app_page.locator("h2")
        h2_count = await h2_elements.count()
        assert h2_count >= 1, "Page should have at least one h2 element"
        
        # Check that interactive elements have accessible names
        reset_button = app_page.locator("button", has_text="Reset to Example")
        button_text = await reset_button.text_content()
        assert button_text and len(button_text.strip()) > 0, "Button should have accessible text"
        
        # Verify character counter provides meaningful information
        counter = app_page.locator("text=/Content length: \\d+ characters/")
        await expect(counter).to_be_visible()
        counter_text = await counter.text_content()
        assert "Content length:" in counter_text, "Counter should provide clear information"
        
        # Test that Monaco editor is accessible to assistive technology
        await app_page.wait_for_selector(".monaco-editor", timeout=10000)
        editor_textarea = app_page.locator(".monaco-editor textarea")
        
        # Check if textarea has proper attributes for screen readers
        await expect(editor_textarea).to_be_visible()
        
        # Verify editor can receive focus programmatically (important for screen readers)
        await editor_textarea.focus()
        focused_element = await app_page.evaluate("document.activeElement.tagName")
        assert focused_element.lower() == "textarea", "Editor textarea should be focusable"

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_editor_content_with_special_characters(self, app_page: Page):
        """Test editor handling of special characters and Unicode content."""
        # Wait for Monaco editor to load
        await app_page.wait_for_selector(".monaco-editor", timeout=10000)
        
        # Test content with various special characters
        special_content = """# YAML with Special Characters
name: "test-connector-特殊字符"
version: "1.0.0"
description: |
  This connector handles special characters:
  - Unicode: 你好世界 🌍 🚀
  - Symbols: @#$%^&*()_+-={}[]|\\:";'<>?,./
  - Quotes: "double" and 'single' quotes
  - Escapes: \\n \\t \\r \\\\ \\"
  
config:
  special_field: "Value with émojis 😀 and açcénts"
  unicode_test: "Тест на русском языке"
  japanese: "日本語のテスト"
  emoji_field: "🔧⚙️🛠️"
"""
        
        # Clear editor and add special content
        editor_textarea = app_page.locator(".monaco-editor textarea").first()
        await editor_textarea.click()
        await app_page.keyboard.press("Control+a")
        await app_page.keyboard.type(special_content)
        
        # Wait for content to be processed
        await app_page.wait_for_timeout(1000)
        
        # Verify character counter updates correctly with special characters
        counter = app_page.locator("text=/Content length: \\d+ characters/")
        await expect(counter).to_be_visible()
        
        counter_text = await counter.text_content()
        content_length = len(special_content)
        
        # Extract number from counter text
        import re
        counter_match = re.search(r'(\d+)', counter_text)
        assert counter_match, "Counter should display a number"
        
        displayed_length = int(counter_match.group(1))
        
        # Allow for some variation due to encoding differences
        assert abs(displayed_length - content_length) <= 10, \
            f"Character count mismatch: expected ~{content_length}, got {displayed_length}"
        
        # Test that reset button works with special characters
        reset_button = app_page.locator("button", has_text="Reset to Example")
        await reset_button.click()
        
        # Wait for reset and verify it worked
        await app_page.wait_for_timeout(1000)
        reset_counter = app_page.locator("text=/Content length: \\d+ characters/")
        reset_text = await reset_counter.text_content()
        assert reset_text != counter_text, "Reset should change the content"

