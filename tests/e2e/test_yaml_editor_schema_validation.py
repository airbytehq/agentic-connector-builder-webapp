"""Failing Playwright tests demonstrating missing JSON schema integration in Monaco YAML editor.

These tests are designed to FAIL and demonstrate the missing functionality:
1. Hover tooltips for YAML keys from JSON schema
2. Syntax error highlighting with red squiggly lines
3. Schema validation error highlighting
"""

import pytest
from playwright.async_api import Page, expect


class TestYamlEditorSchemaIntegration:
    """Test JSON schema integration features that are currently missing."""

    async def _wait_for_monaco_editor_ready(
        self, page: Page, timeout: int = 15000
    ) -> None:
        """Wait for Monaco editor to be fully loaded and ready."""
        await page.wait_for_selector(".monaco-editor", timeout=timeout)
        await page.wait_for_selector(
            ".monaco-editor .monaco-editor-background", timeout=5000
        )
        await page.wait_for_selector(".monaco-editor textarea", timeout=5000)

    @pytest.mark.e2e
    @pytest.mark.browser
    @pytest.mark.xfail(reason="JSON schema tooltips not implemented yet")
    async def test_hover_tooltip_shows_schema_description(self, app_page: Page):
        """Test that hovering over YAML keys shows JSON schema descriptions.

        EXPECTED TO FAIL: Current Monaco editor lacks JSON schema integration.
        """
        await self._wait_for_monaco_editor_ready(app_page)

        name_key_element = app_page.locator(".monaco-editor").get_by_text("name:")
        await name_key_element.hover()

        await app_page.wait_for_timeout(1000)

        tooltip_selector = ".monaco-editor .monaco-hover"
        tooltip = app_page.locator(tooltip_selector)

        await expect(tooltip).to_be_visible(timeout=3000)
        await expect(tooltip).to_contain_text("connector name", case_sensitive=False)

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_syntax_error_shows_red_squiggly(self, app_page: Page):
        """Test that YAML syntax errors show red squiggly underlines."""
        await self._wait_for_monaco_editor_ready(app_page)

        editor_textarea = app_page.locator(".monaco-editor textarea")
        await editor_textarea.click()
        await editor_textarea.fill("invalid: yaml: [unclosed bracket")

        await app_page.wait_for_timeout(2000)

        error_decoration_selector = ".monaco-editor .squiggly-error"
        error_decoration = app_page.locator(error_decoration_selector)

        await expect(error_decoration).to_be_visible(timeout=3000)

    @pytest.mark.e2e
    @pytest.mark.browser
    @pytest.mark.xfail(reason="JSON schema validation not implemented")
    async def test_schema_validation_error_shows_red_squiggly(self, app_page: Page):
        """Test that JSON schema validation errors show red squiggly underlines.

        EXPECTED TO FAIL: Current Monaco editor lacks JSON schema validation.
        """
        await self._wait_for_monaco_editor_ready(app_page)

        invalid_schema_yaml = """
name: 123  # Should be string, not number
version: "1.0.0"
description: "Test connector"
source:
  type: "invalid_source_type"  # Should be from allowed enum
"""

        editor_textarea = app_page.locator(".monaco-editor textarea")
        await editor_textarea.click()
        await editor_textarea.fill(invalid_schema_yaml)

        await app_page.wait_for_timeout(2000)

        error_decoration_selector = ".monaco-editor .squiggly-error"
        error_decorations = app_page.locator(error_decoration_selector)

        await expect(error_decorations).to_have_count(2)  # name and source.type errors

    @pytest.mark.e2e
    @pytest.mark.browser
    @pytest.mark.xfail(reason="Error markers in gutter not implemented")
    async def test_error_markers_in_gutter(self, app_page: Page):
        """Test that validation errors show markers in the editor gutter.

        EXPECTED TO FAIL: Current Monaco editor lacks error marker integration.
        """
        await self._wait_for_monaco_editor_ready(app_page)

        editor_textarea = app_page.locator(".monaco-editor textarea")
        await editor_textarea.click()
        await editor_textarea.fill("invalid: yaml: syntax: error")

        await app_page.wait_for_timeout(2000)

        error_marker_selector = ".monaco-editor .margin .fa-exclamation-triangle"
        error_marker = app_page.locator(error_marker_selector)

        await expect(error_marker).to_be_visible(timeout=3000)

    @pytest.mark.e2e
    @pytest.mark.browser
    @pytest.mark.xfail(reason="Problems panel not implemented")
    async def test_problems_panel_shows_validation_errors(self, app_page: Page):
        """Test that validation errors appear in a problems/diagnostics panel.

        EXPECTED TO FAIL: Current implementation has no problems panel.
        """
        await self._wait_for_monaco_editor_ready(app_page)

        editor_textarea = app_page.locator(".monaco-editor textarea")
        await editor_textarea.click()
        await editor_textarea.fill("name: 123\nversion: invalid")

        await app_page.wait_for_timeout(2000)

        problems_panel_selector = ".problems-panel, .diagnostics-panel, .error-list"
        problems_panel = app_page.locator(problems_panel_selector)

        await expect(problems_panel).to_be_visible(timeout=3000)
        await expect(problems_panel).to_contain_text(
            "validation error", case_sensitive=False
        )
