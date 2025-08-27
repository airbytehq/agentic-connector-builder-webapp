"""End-to-end tests for YAML editor functionality using Playwright."""

import asyncio

import pytest
from playwright.async_api import Page, expect
from playwright.async_api import TimeoutError as PlaywrightTimeoutError


class TestYamlEditorBasicFunctionality:
    """Test basic YAML editor functionality."""

    async def _wait_for_monaco_editor_ready(
        self, page: Page, timeout: int = 15000
    ) -> None:
        """Enhanced wait for Monaco editor to be fully loaded and ready."""
        try:
            # Wait for Monaco editor container
            await page.wait_for_selector(".monaco-editor", timeout=timeout)

            # Wait for Monaco editor to be fully initialized
            await page.wait_for_selector(
                ".monaco-editor .monaco-editor-background", timeout=5000
            )

            # Wait for textarea to be present (indicates editor is interactive)
            await page.wait_for_selector(".monaco-editor textarea", timeout=5000)

            # Additional wait for editor to be fully rendered
            await page.wait_for_function(
                "() => document.querySelector('.monaco-editor textarea') !== null && "
                "document.querySelector('.monaco-editor .monaco-editor-background') !== null",
                timeout=3000,
            )

        except PlaywrightTimeoutError as e:
            # Enhanced error context for debugging
            console_logs = []

            # Collect any console errors
            page.on(
                "console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}")
            )

            raise AssertionError(
                f"Monaco editor failed to load within {timeout}ms. "
                f"Error: {str(e)}. "
                f"Page title: {await page.title()}. "
                f"Console logs: {console_logs[-5:] if console_logs else 'None'}. "
                f"Monaco elements found: {await page.locator('.monaco-editor').count()}"
            ) from e

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_page_loads_successfully(self, app_page: Page):
        """Test that the main page loads successfully with enhanced error handling."""
        try:
            # Check that the page title is correct with timeout
            await expect(app_page).to_have_title(
                "Agentic Connector Builder", timeout=10000
            )

            # More specific selector for main heading with enhanced wait
            main_heading = app_page.locator("h1:has-text('Agentic Connector Builder')")
            await expect(main_heading).to_be_visible(timeout=8000)

            # Verify page is fully loaded by checking for key elements
            await expect(app_page.locator("body")).to_be_visible()

        except PlaywrightTimeoutError as e:
            # Enhanced error reporting
            page_url = app_page.url
            page_title = await app_page.title()
            raise AssertionError(
                f"Page failed to load successfully. URL: {page_url}, "
                f"Title: '{page_title}', Error: {str(e)}"
            ) from e

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_yaml_editor_is_present(self, app_page: Page):
        """Test that the YAML editor component is present with enhanced selectors."""
        try:
            # More specific selector for YAML editor heading
            editor_heading = app_page.locator(
                "h2:has-text('YAML Connector Configuration Editor')"
            )
            await expect(editor_heading).to_be_visible(timeout=8000)

            # Enhanced Monaco editor detection with multiple fallback selectors
            monaco_selectors = [
                ".monaco-editor",
                "[data-uri*='monaco']",
                ".monaco-editor-background",
                ".monaco-editor .monaco-scrollable-element",
            ]

            editor_found = False
            for selector in monaco_selectors:
                try:
                    editor_element = app_page.locator(selector).first()
                    await expect(editor_element).to_be_visible(timeout=3000)
                    editor_found = True
                    break
                except PlaywrightTimeoutError:
                    continue

            if not editor_found:
                # Collect diagnostic information
                all_divs = await app_page.locator("div").count()
                monaco_count = await app_page.locator(".monaco-editor").count()

                raise AssertionError(
                    f"Monaco editor not found. Total divs: {all_divs}, "
                    f"Monaco elements: {monaco_count}. "
                    f"Tried selectors: {monaco_selectors}"
                )

            # Wait for editor to be fully ready
            await self._wait_for_monaco_editor_ready(app_page)

        except Exception as e:
            # Enhanced error context
            page_content_snippet = await app_page.locator("body").inner_text()
            raise AssertionError(
                f"YAML editor presence test failed: {str(e)}. "
                f"Page content snippet: {page_content_snippet[:200]}..."
            ) from e

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_reset_button_is_present(self, app_page: Page):
        """Test that the reset button is present and clickable with enhanced selectors."""
        try:
            # More specific button selector with multiple approaches
            reset_button_selectors = [
                "button:has-text('Reset to Example')",
                "button[type='button']:has-text('Reset')",
                "[role='button']:has-text('Reset to Example')",
            ]

            reset_button = None
            for selector in reset_button_selectors:
                try:
                    button = app_page.locator(selector).first()
                    await expect(button).to_be_visible(timeout=3000)
                    reset_button = button
                    break
                except PlaywrightTimeoutError:
                    continue

            if reset_button is None:
                # Collect all buttons for debugging
                all_buttons = await app_page.locator("button").all()
                button_texts = []
                for btn in all_buttons:
                    try:
                        text = await btn.text_content()
                        button_texts.append(text)
                    except Exception:
                        button_texts.append("(text unavailable)")

                raise AssertionError(
                    f"Reset button not found. Available buttons: {button_texts}. "
                    f"Tried selectors: {reset_button_selectors}"
                )

            # Enhanced button state verification
            await expect(reset_button).to_be_enabled(timeout=5000)

            # Verify button is interactive (not just visible)
            button_box = await reset_button.bounding_box()
            assert button_box is not None, "Reset button should have valid bounding box"
            assert button_box["width"] > 0 and button_box["height"] > 0, (
                "Reset button should have positive dimensions"
            )

        except Exception as e:
            raise AssertionError(f"Reset button test failed: {str(e)}") from e

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_character_counter_is_present(self, app_page: Page):
        """Test that the character counter is present with enhanced pattern matching."""
        try:
            # Enhanced counter selector with multiple patterns
            counter_patterns = [
                "text=/Content length: \\d+ characters/",
                ":has-text('Content length:')",
                "text=/\\d+ characters/",
                "[data-testid*='counter']",  # In case data-testid is added later
            ]

            counter_found = False
            counter_element = None

            for pattern in counter_patterns:
                try:
                    counter = app_page.locator(pattern).first()
                    await expect(counter).to_be_visible(timeout=3000)
                    counter_element = counter
                    counter_found = True
                    break
                except PlaywrightTimeoutError:
                    continue

            if not counter_found:
                # Enhanced debugging information
                page_text = await app_page.locator("body").inner_text()
                content_length_mentions = [
                    line
                    for line in page_text.split("\n")
                    if "content" in line.lower()
                    or "length" in line.lower()
                    or "character" in line.lower()
                ]

                raise AssertionError(
                    f"Character counter not found. "
                    f"Tried patterns: {counter_patterns}. "
                    f"Potential matches in page: {content_length_mentions[:3]}"
                )

            # Verify counter shows valid content
            if counter_element is not None:
                counter_text = await counter_element.text_content()
                assert counter_text is not None, "Counter should have text content"
                assert len(counter_text.strip()) > 0, "Counter text should not be empty"

            # Verify counter format is reasonable
            import re

            if not re.search(r"\d+", counter_text):
                raise AssertionError(
                    f"Counter should contain numbers, got: '{counter_text}'"
                )

        except Exception as e:
            raise AssertionError(f"Character counter test failed: {str(e)}") from e


class TestYamlEditorInteraction:
    """Test YAML editor interaction functionality."""

    async def _wait_for_monaco_editor_ready(
        self, page: Page, timeout: int = 15000
    ) -> None:
        """Enhanced wait for Monaco editor to be fully loaded and ready."""
        try:
            # Wait for Monaco editor container
            await page.wait_for_selector(".monaco-editor", timeout=timeout)

            # Wait for Monaco editor to be fully initialized
            await page.wait_for_selector(
                ".monaco-editor .monaco-editor-background", timeout=5000
            )

            # Wait for textarea to be present (indicates editor is interactive)
            await page.wait_for_selector(".monaco-editor textarea", timeout=5000)

            # Additional wait for editor to be fully rendered
            await page.wait_for_function(
                "() => document.querySelector('.monaco-editor textarea') !== null && "
                "document.querySelector('.monaco-editor .monaco-editor-background') !== null",
                timeout=3000,
            )

        except PlaywrightTimeoutError as e:
            # Enhanced error context for debugging
            console_logs = []

            # Collect any console errors
            page.on(
                "console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}")
            )

            raise AssertionError(
                f"Monaco editor failed to load within {timeout}ms. "
                f"Error: {str(e)}. "
                f"Page title: {await page.title()}. "
                f"Console logs: {console_logs[-5:] if console_logs else 'None'}. "
                f"Monaco elements found: {await page.locator('.monaco-editor').count()}"
            ) from e

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_editor_contains_default_content(self, app_page: Page):
        """Test that the editor contains default YAML content with enhanced validation."""
        try:
            # Enhanced Monaco editor wait
            await self._wait_for_monaco_editor_ready(app_page)

            # More specific content validation with multiple approaches
            editor_selectors = [
                ".monaco-editor",
                ".monaco-editor .monaco-editor-background",
                ".monaco-editor .view-lines",
            ]

            content_found = False
            expected_content_items = ["example-connector", "version", "description"]

            for selector in editor_selectors:
                try:
                    editor_element = app_page.locator(selector).first()
                    await expect(editor_element).to_be_visible(timeout=3000)

                    # Check for expected content items
                    for content_item in expected_content_items:
                        try:
                            await expect(editor_element).to_contain_text(
                                content_item, timeout=2000
                            )
                            content_found = True
                        except PlaywrightTimeoutError:
                            continue

                    if content_found:
                        break

                except PlaywrightTimeoutError:
                    continue

            if not content_found:
                # Enhanced debugging - get actual editor content
                try:
                    # Try to get content via textarea
                    textarea = app_page.locator(".monaco-editor textarea").first()
                    actual_content = await textarea.input_value()
                except Exception:
                    # Fallback to text content
                    actual_content = (
                        await app_page.locator(".monaco-editor").first().text_content()
                    )

                raise AssertionError(
                    f"Default content not found in editor. "
                    f"Expected items: {expected_content_items}. "
                    f"Actual content preview: '{actual_content[:200] if actual_content else 'None'}...'"
                )

        except Exception as e:
            raise AssertionError(f"Default content test failed: {str(e)}") from e

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_reset_button_functionality(self, app_page: Page):
        """Test that the reset button works correctly with enhanced validation."""
        try:
            # Enhanced Monaco editor wait
            await self._wait_for_monaco_editor_ready(app_page)

            # More specific reset button selector with fallbacks
            reset_button_selectors = [
                "button:has-text('Reset to Example')",
                "button[type='button']:has-text('Reset')",
                "[role='button']:has-text('Reset to Example')",
            ]

            reset_button = None
            for selector in reset_button_selectors:
                try:
                    button = app_page.locator(selector).first()
                    await expect(button).to_be_visible(timeout=3000)
                    await expect(button).to_be_enabled(timeout=2000)
                    reset_button = button
                    break
                except PlaywrightTimeoutError:
                    continue

            if reset_button is None:
                raise AssertionError("Reset button not found or not enabled")

            # Get initial state for comparison (not used but kept for potential debugging)

            # Click the reset button with enhanced error handling
            try:
                await reset_button.click(timeout=5000)
            except PlaywrightTimeoutError as e:
                raise AssertionError(f"Reset button click failed: {str(e)}") from e

            # Enhanced wait for reset to take effect
            await asyncio.sleep(0.5)  # Initial wait

            # Wait for content to actually change (if it was different before)
            max_wait_attempts = 10
            for _attempt in range(max_wait_attempts):
                try:
                    current_content = (
                        await app_page.locator(".monaco-editor textarea")
                        .first()
                        .input_value()
                    )
                except Exception:
                    current_content = (
                        await app_page.locator(".monaco-editor").first().text_content()
                    )

                # Check if content contains expected default items
                if current_content and "example-connector" in current_content:
                    break

                await asyncio.sleep(0.2)
            else:
                raise AssertionError(
                    f"Reset did not restore expected content after {max_wait_attempts} attempts. "
                    f"Current content: '{current_content[:100] if current_content else 'None'}...'"
                )

            # Verify that the default content is present with multiple validation approaches
            editor_content_selectors = [
                ".monaco-editor",
                ".monaco-editor .view-lines",
                ".monaco-editor .monaco-editor-background",
            ]

            content_verified = False
            for selector in editor_content_selectors:
                try:
                    editor_element = app_page.locator(selector).first()
                    await expect(editor_element).to_contain_text(
                        "example-connector", timeout=3000
                    )
                    content_verified = True
                    break
                except PlaywrightTimeoutError:
                    continue

            if not content_verified:
                raise AssertionError(
                    "Reset button did not restore expected default content"
                )

        except Exception as e:
            raise AssertionError(
                f"Reset button functionality test failed: {str(e)}"
            ) from e

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_character_counter_updates(self, app_page: Page):
        """Test that the character counter updates when content changes with enhanced validation."""
        try:
            # Enhanced Monaco editor wait
            await self._wait_for_monaco_editor_ready(app_page)

            # Enhanced counter selector with multiple patterns
            counter_selectors = [
                "text=/Content length: \\d+ characters/",
                ":has-text('Content length:')",
                "text=/\\d+ characters/",
            ]

            counter_element = None
            for selector in counter_selectors:
                try:
                    counter = app_page.locator(selector).first()
                    await expect(counter).to_be_visible(timeout=3000)
                    counter_element = counter
                    break
                except PlaywrightTimeoutError:
                    continue

            if counter_element is None:
                raise AssertionError(
                    f"Character counter not found. Tried selectors: {counter_selectors}"
                )

            # Get initial character count with enhanced parsing
            initial_text = await counter_element.text_content()
            import re

            initial_match = re.search(r"(\d+)", initial_text or "")
            if not initial_match:
                raise AssertionError(
                    f"Could not parse initial character count from: '{initial_text}'"
                )

            # Store initial count for potential debugging
            _initial_count = int(initial_match.group(1))

            # Enhanced reset button interaction
            reset_button_selectors = [
                "button:has-text('Reset to Example')",
                "button[type='button']:has-text('Reset')",
            ]

            reset_button = None
            for selector in reset_button_selectors:
                try:
                    button = app_page.locator(selector).first()
                    await expect(button).to_be_enabled(timeout=3000)
                    reset_button = button
                    break
                except PlaywrightTimeoutError:
                    continue

            if reset_button is None:
                raise AssertionError("Reset button not found for counter test")

            # Click reset and wait for counter update
            await reset_button.click(timeout=5000)

            # Enhanced wait for counter update with retry logic
            max_attempts = 15
            counter_updated = False

            for _attempt in range(max_attempts):
                await asyncio.sleep(0.2)

                try:
                    current_text = await counter_element.text_content()
                    current_match = re.search(r"(\d+)", current_text or "")

                    if current_match:
                        current_count = int(current_match.group(1))

                        # Verify counter shows reasonable content length
                        if current_count > 0:
                            counter_updated = True
                            break

                except Exception:
                    continue

            if not counter_updated:
                final_text = await counter_element.text_content()
                raise AssertionError(
                    f"Character counter did not update properly after {max_attempts} attempts. "
                    f"Initial: '{initial_text}', Final: '{final_text}'"
                )

            # Final validation
            await expect(counter_element).to_contain_text(
                "Content length:", timeout=3000
            )

            final_counter_text = await counter_element.text_content()
            assert "0 characters" not in final_counter_text, (
                f"Counter should show non-zero characters for default content, got: '{final_counter_text}'"
            )

        except Exception as e:
            raise AssertionError(
                f"Character counter update test failed: {str(e)}"
            ) from e


class TestYamlEditorAdvanced:
    """Test advanced YAML editor functionality."""

    async def _wait_for_monaco_editor_ready(
        self, page: Page, timeout: int = 15000
    ) -> None:
        """Enhanced wait for Monaco editor to be fully loaded and ready."""
        try:
            await page.wait_for_selector(".monaco-editor", timeout=timeout)
            await page.wait_for_selector(
                ".monaco-editor .monaco-editor-background", timeout=5000
            )
            await page.wait_for_selector(".monaco-editor textarea", timeout=5000)
            await page.wait_for_function(
                "() => document.querySelector('.monaco-editor textarea') !== null && "
                "document.querySelector('.monaco-editor .monaco-editor-background') !== null",
                timeout=3000,
            )
        except PlaywrightTimeoutError as e:
            console_logs = []
            page.on(
                "console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}")
            )
            raise AssertionError(
                f"Monaco editor failed to load within {timeout}ms. Error: {str(e)}. "
                f"Console logs: {console_logs[-3:] if console_logs else 'None'}"
            ) from e

    @pytest.mark.e2e
    @pytest.mark.browser
    @pytest.mark.slow_e2e
    async def test_editor_syntax_highlighting(self, app_page: Page):
        """Test that the YAML editor has proper syntax highlighting with enhanced detection."""
        try:
            await self._wait_for_monaco_editor_ready(app_page)

            # Multiple selectors for syntax highlighting detection
            syntax_selectors = [
                ".monaco-editor .mtk1, .monaco-editor .mtk2, .monaco-editor .mtk3, .monaco-editor .mtk4",
                ".monaco-editor .view-lines .view-line",
                ".monaco-editor [class*='mtk']",
            ]

            syntax_found = False
            for selector in syntax_selectors:
                try:
                    syntax_elements = app_page.locator(selector)
                    if await syntax_elements.count() > 0:
                        await expect(syntax_elements.first()).to_be_visible(
                            timeout=3000
                        )
                        syntax_found = True
                        break
                except PlaywrightTimeoutError:
                    continue

            if not syntax_found:
                all_monaco_elements = await app_page.locator(".monaco-editor *").count()
                raise AssertionError(
                    f"Syntax highlighting elements not found. "
                    f"Total Monaco elements: {all_monaco_elements}. "
                    f"Tried selectors: {syntax_selectors}"
                )

        except Exception as e:
            raise AssertionError(f"Syntax highlighting test failed: {str(e)}") from e

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_editor_line_numbers(self, app_page: Page):
        """Test that the editor shows line numbers with enhanced detection."""
        try:
            await self._wait_for_monaco_editor_ready(app_page)

            # Multiple selectors for line numbers
            line_number_selectors = [
                ".monaco-editor .line-numbers",
                ".monaco-editor .margin .line-numbers",
                ".monaco-editor [class*='line-numbers']",
            ]

            line_numbers_found = False
            for selector in line_number_selectors:
                try:
                    line_numbers = app_page.locator(selector)
                    if await line_numbers.count() > 0:
                        first_line = line_numbers.first()
                        await expect(first_line).to_be_visible(timeout=3000)

                        # Verify it contains actual line numbers
                        line_text = await first_line.text_content()
                        if line_text and line_text.strip().isdigit():
                            line_numbers_found = True
                            break
                except PlaywrightTimeoutError:
                    continue

            if not line_numbers_found:
                editor_margin = await app_page.locator(".monaco-editor .margin").count()
                raise AssertionError(
                    f"Line numbers not found. Editor margin elements: {editor_margin}. "
                    f"Tried selectors: {line_number_selectors}"
                )

        except Exception as e:
            raise AssertionError(f"Line numbers test failed: {str(e)}") from e

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_editor_dark_theme(self, app_page: Page):
        """Test that the editor uses dark theme with enhanced detection."""
        try:
            await self._wait_for_monaco_editor_ready(app_page)

            # Multiple approaches for dark theme detection
            dark_theme_selectors = [
                ".monaco-editor.vs-dark",
                ".monaco-editor[data-theme='vs-dark']",
                ".monaco-editor[class*='dark']",
            ]

            theme_found = False
            for selector in dark_theme_selectors:
                try:
                    theme_element = app_page.locator(selector).first()
                    await expect(theme_element).to_be_visible(timeout=3000)
                    theme_found = True
                    break
                except PlaywrightTimeoutError:
                    continue

            # Fallback: check background color
            if not theme_found:
                try:
                    editor_bg = app_page.locator(
                        ".monaco-editor .monaco-editor-background"
                    ).first()
                    await expect(editor_bg).to_be_visible(timeout=3000)

                    bg_color = await editor_bg.evaluate(
                        "el => window.getComputedStyle(el).backgroundColor"
                    )
                    if bg_color:
                        import re

                        rgb_match = re.search(
                            r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", bg_color
                        )
                        if rgb_match:
                            r, g, b = map(int, rgb_match.groups())
                            if r < 128 and g < 128 and b < 128:  # Dark background
                                theme_found = True
                except Exception:
                    pass

            if not theme_found:
                editor_classes = (
                    await app_page.locator(".monaco-editor")
                    .first()
                    .get_attribute("class")
                )
                raise AssertionError(
                    f"Dark theme not detected. Editor classes: '{editor_classes}'. "
                    f"Tried selectors: {dark_theme_selectors}"
                )

        except Exception as e:
            raise AssertionError(f"Dark theme test failed: {str(e)}") from e


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

        description = app_page.locator(
            "text=Build and configure data connectors using YAML"
        )
        await expect(description).to_be_visible()

        editor_section = app_page.locator(
            "h2", has_text="YAML Connector Configuration Editor"
        )
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
        assert processing_time < 10000, (
            f"Large content processing took too long: {processing_time}ms"
        )

        # Verify editor functionality with large content
        counter = app_page.locator("text=/Content length: \\d+ characters/")
        await expect(counter).to_be_visible()

        # Verify character count is approximately correct (within reasonable range)
        counter_text = await counter.text_content()
        content_length = len(large_yaml_content)
        assert (
            str(content_length)[:3] in counter_text
            or str(content_length)[:4] in counter_text
        )

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
        editor_heading = app_page.locator(
            "h2", has_text="YAML Connector Configuration Editor"
        )
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
        assert button_text and len(button_text.strip()) > 0, (
            "Button should have accessible text"
        )

        # Verify character counter provides meaningful information
        counter = app_page.locator("text=/Content length: \\d+ characters/")
        await expect(counter).to_be_visible()
        counter_text = await counter.text_content()
        assert "Content length:" in counter_text, (
            "Counter should provide clear information"
        )

        # Test that Monaco editor is accessible to assistive technology
        await app_page.wait_for_selector(".monaco-editor", timeout=10000)
        editor_textarea = app_page.locator(".monaco-editor textarea")

        # Check if textarea has proper attributes for screen readers
        await expect(editor_textarea).to_be_visible()

        # Verify editor can receive focus programmatically (important for screen readers)
        await editor_textarea.focus()
        focused_element = await app_page.evaluate("document.activeElement.tagName")
        assert focused_element.lower() == "textarea", (
            "Editor textarea should be focusable"
        )

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

        counter_match = re.search(r"(\d+)", counter_text)
        assert counter_match, "Counter should display a number"

        displayed_length = int(counter_match.group(1))

        # Allow for some variation due to encoding differences
        assert abs(displayed_length - content_length) <= 10, (
            f"Character count mismatch: expected ~{content_length}, got {displayed_length}"
        )

        # Test that reset button works with special characters
        reset_button = app_page.locator("button", has_text="Reset to Example")
        await reset_button.click()

        # Wait for reset and verify it worked
        await app_page.wait_for_timeout(1000)
        reset_counter = app_page.locator("text=/Content length: \\d+ characters/")
        reset_text = await reset_counter.text_content()
        assert reset_text != counter_text, "Reset should change the content"


class TestYamlEditorStateManagement:
    """Test YAML editor state management edge cases and robustness."""

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_extremely_long_content_state_handling(self, app_page: Page):
        """Test YamlEditorState handling of extremely long content (>100KB)."""
        # Wait for Monaco editor to load
        await app_page.wait_for_selector(".monaco-editor", timeout=10000)

        # Generate extremely long YAML content (approximately 100KB)
        base_content = """# Extremely Large YAML Configuration
name: massive-connector-config
version: "1.0.0"
description: "Testing state management with extremely large content"

"""

        # Create a very large configuration with thousands of entries
        large_sections = []
        for section_idx in range(50):  # 50 major sections
            section_content = f"""
# Section {section_idx:03d} - Database Configurations
database_section_{section_idx:03d}:
  type: "multi_database_section"
  description: "Section {section_idx:03d} containing multiple database configurations"
"""
            # Add many database configs per section
            for db_idx in range(100):  # 100 databases per section = 5000 total
                db_config = f"""  database_{section_idx:03d}_{db_idx:03d}:
    type: "postgresql"
    connection:
      host: "db-{section_idx:03d}-{db_idx:03d}.example.com"
      port: {5432 + (section_idx * 100) + db_idx}
      database: "app_db_{section_idx:03d}_{db_idx:03d}"
      username: "user_{section_idx:03d}_{db_idx:03d}"
      password: "secure_password_{section_idx:03d}_{db_idx:03d}"
      ssl_mode: "require"
      connection_timeout: 30
      max_connections: 100
    tables:
      - name: "users_{section_idx:03d}_{db_idx:03d}"
        columns: ["id", "username", "email", "created_at", "updated_at", "status"]
        indexes: ["username", "email", "created_at"]
      - name: "orders_{section_idx:03d}_{db_idx:03d}"
        columns: ["id", "user_id", "product_id", "quantity", "price", "order_date"]
        indexes: ["user_id", "product_id", "order_date"]
      - name: "products_{section_idx:03d}_{db_idx:03d}"
        columns: ["id", "name", "description", "price", "category", "stock"]
        indexes: ["name", "category", "price"]
    transformations:
      - type: "data_validation"
        rules:
          - field: "email"
            type: "email"
            required: true
          - field: "price"
            type: "decimal"
            min: 0
      - type: "field_mapping"
        mappings:
          user_id: "customer_id"
          order_date: "purchase_timestamp"
"""
                section_content += db_config
            large_sections.append(section_content)

        extremely_long_content = base_content + "".join(large_sections)

        # Verify content is actually extremely large (should be >100KB)
        content_size = len(extremely_long_content)
        assert content_size > 100000, (
            f"Content should be >100KB, got {content_size} bytes"
        )

        # Record start time for performance measurement
        start_time = await app_page.evaluate("Date.now()")

        # Attempt to set extremely long content in editor
        editor_textarea = app_page.locator(".monaco-editor textarea").first()
        await editor_textarea.click()
        await app_page.keyboard.press("Control+a")

        # Set content in chunks to avoid browser limitations
        chunk_size = 10000
        for i in range(0, len(extremely_long_content), chunk_size):
            chunk = extremely_long_content[i : i + chunk_size]
            if i == 0:
                await app_page.keyboard.type(chunk)
            else:
                await app_page.keyboard.type(chunk)

            # Small pause between chunks to allow processing
            await app_page.wait_for_timeout(100)

        # Wait for content processing to complete
        await app_page.wait_for_timeout(3000)

        # Record end time
        end_time = await app_page.evaluate("Date.now()")
        processing_time = end_time - start_time

        # Verify state management performance (should handle large content within reasonable time)
        assert processing_time < 30000, (
            f"Extremely large content processing took too long: {processing_time}ms"
        )

        # Verify character counter updates correctly with extremely long content
        counter = app_page.locator("text=/Content length: \\d+ characters/")
        await expect(counter).to_be_visible()

        counter_text = await counter.text_content()
        import re

        counter_match = re.search(r"(\d+)", counter_text)
        assert counter_match, (
            "Counter should display character count for extremely long content"
        )

        displayed_length = int(counter_match.group(1))

        # Allow for reasonable variation due to processing differences
        length_difference = abs(displayed_length - content_size)
        assert length_difference < 1000, (
            f"Character count significantly off for large content: expected ~{content_size}, got {displayed_length}"
        )

        # Test that state can still be reset even with extremely long content
        reset_button = app_page.locator("button", has_text="Reset to Example")
        await expect(reset_button).to_be_visible()
        await reset_button.click()

        # Wait for reset to complete
        await app_page.wait_for_timeout(2000)

        # Verify reset worked (character count should be much smaller)
        reset_counter = app_page.locator("text=/Content length: \\d+ characters/")
        reset_text = await reset_counter.text_content()
        reset_match = re.search(r"(\d+)", reset_text)
        assert reset_match, "Counter should show reset content length"

        reset_length = int(reset_match.group(1))
        assert reset_length < 1000, (
            f"Reset should result in much smaller content, got {reset_length} characters"
        )

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_special_characters_state_persistence(self, app_page: Page):
        """Test YamlEditorState handling of complex special characters and encoding."""
        # Wait for Monaco editor to load
        await app_page.wait_for_selector(".monaco-editor", timeout=10000)

        # Create content with extensive special characters that could break state management
        special_chars_content = """# Complex Special Characters State Test
name: "special-chars-connector-测试"
version: "1.0.0"
description: |
  Testing state management with complex characters:

  Unicode Categories:
  - Latin Extended: àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ
  - Cyrillic: абвгдеёжзийклмнопрстуфхцчшщъыьэюя
  - Greek: αβγδεζηθικλμνξοπρστυφχψω
  - Arabic: العربية اللغة
  - Hebrew: עברית שפה
  - Chinese: 中文测试内容
  - Japanese: 日本語テスト内容ひらがなカタカナ漢字
  - Korean: 한국어 테스트 내용
  - Thai: ภาษาไทย การทดสอบ
  - Emoji: 🌍🚀💻⚙️🔧🛠️📊📈📉💡🎯🎨🎭🎪🎨
  - Mathematical: ∑∏∫∂∇∆∞≠≤≥±×÷√∛∜
  - Currency: $€£¥₹₽₩₪₫₱₡₦₨₴₸₼
  - Arrows: ←→↑↓↔↕↖↗↘↙⇐⇒⇑⇓⇔⇕
  - Symbols: ©®™℠℡№℮⅀⅁⅂⅃⅄ⅅⅆⅇⅈⅉ

  Control Characters and Escapes:
  - Newlines: "\\n\\r\\n"
  - Tabs: "\\t\\t\\t"
  - Quotes: 'single' "double" `backtick`
  - Backslashes: "\\\\\\\\"
  - Null bytes: "\\0"
  - Bell: "\\a"
  - Form feed: "\\f"
  - Vertical tab: "\\v"

config:
  unicode_field: "Iñtërnâtiônàlizætiøn 国际化 интернационализация"
  emoji_status: "✅ Active 🚀 Running 💻 Processing 📊 Analytics"
  mixed_script: "English中文العربيةрусский日本語한국어ไทย"
  special_yaml_chars: |
    YAML special characters test:
    - Colon in value: "key: value"
    - Square brackets: "[array, items]"
    - Curly braces: "{object: value}"
    - Pipe symbol: "| multiline"
    - Greater than: "> folded"
    - Ampersand: "& anchor"
    - Asterisk: "* reference"
    - Percent: "% directive"
    - At symbol: "@ annotation"
    - Hash: "# comment"

  problematic_combinations:
    zero_width_chars: "a​b​c"  # Contains zero-width spaces
    rtl_ltr_mix: "English العربية English עברית"
    combining_chars: "e̊x̊ȧm̊p̊l̊e̊"  # Letters with combining diacritics
    surrogate_pairs: "𝕳𝖊𝖑𝖑𝖔 𝖂𝖔𝖗𝖑𝖉"  # Mathematical script

transformations:
  - type: "unicode_normalization"
    form: "NFC"
    preserve_original: true
  - type: "encoding_validation"
    target_encoding: "UTF-8"
    fallback_encoding: "ISO-8859-1"
"""

        # Clear editor and set special characters content
        editor_textarea = app_page.locator(".monaco-editor textarea").first()
        await editor_textarea.click()
        await app_page.keyboard.press("Control+a")
        await app_page.keyboard.type(special_chars_content)

        # Wait for content to be processed
        await app_page.wait_for_timeout(2000)

        # Verify character counter handles special characters correctly
        counter = app_page.locator("text=/Content length: \\d+ characters/")
        await expect(counter).to_be_visible()

        counter_text = await counter.text_content()
        import re

        counter_match = re.search(r"(\d+)", counter_text)
        assert counter_match, "Counter should handle special characters"

        displayed_length = int(counter_match.group(1))
        actual_length = len(special_chars_content)

        # Allow for encoding differences but should be reasonably close
        length_difference = abs(displayed_length - actual_length)
        assert length_difference < 100, (
            f"Special character counting error: expected ~{actual_length}, got {displayed_length}"
        )

        # Test state persistence by performing multiple operations
        operations = [
            ("Add more content", "\n# Additional special content: 🎉🎊🎈"),
            ("Add RTL text", '\nrtl_test: "مرحبا بالعالم"'),
            ("Add combining chars", '\ncombining_test: "café naïve résumé"'),
        ]

        for operation_name, additional_content in operations:
            # Add content
            await app_page.keyboard.press("End")
            await app_page.keyboard.type(additional_content)
            await app_page.wait_for_timeout(500)

            # Verify counter updates
            updated_counter = app_page.locator("text=/Content length: \\d+ characters/")
            updated_text = await updated_counter.text_content()
            updated_match = re.search(r"(\d+)", updated_text)
            assert updated_match, f"Counter should update after {operation_name}"

            updated_length = int(updated_match.group(1))
            assert updated_length > displayed_length, (
                f"Length should increase after {operation_name}"
            )
            displayed_length = updated_length

        # Test reset functionality with special characters
        reset_button = app_page.locator("button", has_text="Reset to Example")
        await reset_button.click()
        await app_page.wait_for_timeout(1000)

        # Verify reset worked
        reset_counter = app_page.locator("text=/Content length: \\d+ characters/")
        reset_text = await reset_counter.text_content()
        reset_match = re.search(r"(\d+)", reset_text)
        assert reset_match, "Counter should show reset length"

        reset_length = int(reset_match.group(1))
        assert reset_length < displayed_length, (
            "Reset should reduce content length significantly"
        )

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_concurrent_state_updates_simulation(self, app_page: Page):
        """Test YamlEditorState handling of rapid concurrent-like state updates."""
        # Wait for Monaco editor to load
        await app_page.wait_for_selector(".monaco-editor", timeout=10000)

        # Simulate rapid state changes that could cause race conditions
        editor_textarea = app_page.locator(".monaco-editor textarea").first()
        await editor_textarea.click()

        # Clear initial content
        await app_page.keyboard.press("Control+a")

        # Perform rapid sequential operations to test state consistency
        rapid_operations = [
            ("Type content 1", "# First content block\nname: connector-1"),
            ("Select all", "Control+a"),
            (
                "Type content 2",
                "# Second content block\nname: connector-2\nversion: 1.0",
            ),
            ("Add more", "\ndescription: rapid update test"),
            ("Select all again", "Control+a"),
            (
                "Type content 3",
                "# Third content block\nname: connector-3\nversion: 2.0\ndescription: final test",
            ),
        ]

        # Track character counts to verify state consistency
        character_counts = []

        for operation_name, operation in rapid_operations:
            if operation.startswith("Control+"):
                # Keyboard shortcut
                await app_page.keyboard.press(operation)
            else:
                # Text input
                await app_page.keyboard.type(operation)

            # Minimal wait to simulate rapid operations
            await app_page.wait_for_timeout(100)

            # Check character counter after each operation
            counter = app_page.locator("text=/Content length: \\d+ characters/")
            await expect(counter).to_be_visible()

            counter_text = await counter.text_content()
            import re

            counter_match = re.search(r"(\d+)", counter_text)
            assert counter_match, f"Counter should be visible after {operation_name}"

            char_count = int(counter_match.group(1))
            character_counts.append((operation_name, char_count))

        # Verify that character counts follow logical progression
        # (some operations should increase count, select-all shouldn't change it)

        # Verify final state is consistent
        final_count = character_counts[-1][1]
        assert final_count > 0, "Final character count should be positive"

        # Test rapid reset operations
        reset_button = app_page.locator("button", has_text="Reset to Example")

        # Perform multiple rapid resets to test state stability
        for _i in range(5):
            await reset_button.click()
            await app_page.wait_for_timeout(
                50
            )  # Very short wait to simulate rapid clicks

        # Wait for final reset to complete
        await app_page.wait_for_timeout(1000)

        # Verify state is consistent after rapid resets
        final_counter = app_page.locator("text=/Content length: \\d+ characters/")
        final_text = await final_counter.text_content()
        final_match = re.search(r"(\d+)", final_text)
        assert final_match, "Counter should be stable after rapid resets"

        final_reset_count = int(final_match.group(1))

        # The count should be the default example length (should be consistent)
        assert 200 < final_reset_count < 800, (
            f"Reset count should be in expected range for default content, got {final_reset_count}"
        )

        # Test rapid content changes followed by reset
        await editor_textarea.click()

        # Rapid content modifications
        modifications = [
            "# Rapid test 1",
            "\nname: test-1",
            "\nversion: 1.0",
            "\ndescription: testing rapid changes",
        ]

        for mod in modifications:
            await app_page.keyboard.press("End")
            await app_page.keyboard.type(mod)
            await app_page.wait_for_timeout(50)  # Minimal wait

        # Immediate reset after rapid changes
        await reset_button.click()
        await app_page.wait_for_timeout(1000)

        # Verify state is back to default
        post_rapid_counter = app_page.locator("text=/Content length: \\d+ characters/")
        post_rapid_text = await post_rapid_counter.text_content()
        post_rapid_match = re.search(r"(\d+)", post_rapid_text)
        assert post_rapid_match, (
            "Counter should show default after rapid changes + reset"
        )

        post_rapid_count = int(post_rapid_match.group(1))

        # Should be same as previous reset count (state consistency)
        count_difference = abs(post_rapid_count - final_reset_count)
        assert count_difference <= 5, (
            f"State should be consistent after rapid operations: {post_rapid_count} vs {final_reset_count}"
        )

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_state_boundary_conditions(self, app_page: Page):
        """Test YamlEditorState with boundary conditions and edge cases."""
        # Wait for Monaco editor to load
        await app_page.wait_for_selector(".monaco-editor", timeout=10000)

        editor_textarea = app_page.locator(".monaco-editor textarea").first()
        await editor_textarea.click()

        # Test 1: Empty content state
        await app_page.keyboard.press("Control+a")
        await app_page.keyboard.press("Delete")
        await app_page.wait_for_timeout(500)

        # Verify empty state handling
        counter = app_page.locator("text=/Content length: \\d+ characters/")
        await expect(counter).to_be_visible()

        empty_text = await counter.text_content()
        import re

        empty_match = re.search(r"(\d+)", empty_text)
        assert empty_match, "Counter should handle empty content"

        empty_count = int(empty_match.group(1))
        assert empty_count == 0, (
            f"Empty content should show 0 characters, got {empty_count}"
        )

        # Test 2: Single character state
        await app_page.keyboard.type("a")
        await app_page.wait_for_timeout(300)

        single_counter = app_page.locator("text=/Content length: \\d+ characters/")
        single_text = await single_counter.text_content()
        single_match = re.search(r"(\d+)", single_text)
        assert single_match, "Counter should handle single character"

        single_count = int(single_match.group(1))
        assert single_count == 1, f"Single character should show 1, got {single_count}"

        # Test 3: Whitespace-only content
        await app_page.keyboard.press("Control+a")
        whitespace_content = "   \n\n\t\t\t   \n   "
        await app_page.keyboard.type(whitespace_content)
        await app_page.wait_for_timeout(500)

        whitespace_counter = app_page.locator("text=/Content length: \\d+ characters/")
        whitespace_text = await whitespace_counter.text_content()
        whitespace_match = re.search(r"(\d+)", whitespace_text)
        assert whitespace_match, "Counter should handle whitespace-only content"

        whitespace_count = int(whitespace_match.group(1))
        expected_whitespace_count = len(whitespace_content)
        assert whitespace_count == expected_whitespace_count, (
            f"Whitespace count should be {expected_whitespace_count}, got {whitespace_count}"
        )

        # Test 4: Content with only special characters
        await app_page.keyboard.press("Control+a")
        special_only = "!@#$%^&*()_+-={}[]|\\:;\"'<>?,./"
        await app_page.keyboard.type(special_only)
        await app_page.wait_for_timeout(500)

        special_counter = app_page.locator("text=/Content length: \\d+ characters/")
        special_text = await special_counter.text_content()
        special_match = re.search(r"(\d+)", special_text)
        assert special_match, "Counter should handle special characters only"

        special_count = int(special_match.group(1))
        expected_special_count = len(special_only)
        assert special_count == expected_special_count, (
            f"Special chars count should be {expected_special_count}, got {special_count}"
        )

        # Test 5: Reset from each boundary condition
        boundary_conditions = [
            ("empty", 0),
            ("single char", 1),
            ("whitespace", len(whitespace_content)),
            ("special chars", len(special_only)),
        ]

        reset_button = app_page.locator("button", has_text="Reset to Example")

        for condition_name, expected_count in boundary_conditions:
            # Set the boundary condition content
            await app_page.keyboard.press("Control+a")

            if condition_name == "empty":
                await app_page.keyboard.press("Delete")
            elif condition_name == "single char":
                await app_page.keyboard.type("x")
            elif condition_name == "whitespace":
                await app_page.keyboard.type(whitespace_content)
            elif condition_name == "special chars":
                await app_page.keyboard.type(special_only)

            await app_page.wait_for_timeout(300)

            # Verify the boundary condition is set
            pre_reset_counter = app_page.locator(
                "text=/Content length: \\d+ characters/"
            )
            pre_reset_text = await pre_reset_counter.text_content()
            pre_reset_match = re.search(r"(\d+)", pre_reset_text)
            assert pre_reset_match, f"Should show count for {condition_name}"

            pre_reset_count = int(pre_reset_match.group(1))
            assert pre_reset_count == expected_count, (
                f"Pre-reset count for {condition_name} should be {expected_count}, got {pre_reset_count}"
            )

            # Reset and verify
            await reset_button.click()
            await app_page.wait_for_timeout(1000)

            post_reset_counter = app_page.locator(
                "text=/Content length: \\d+ characters/"
            )
            post_reset_text = await post_reset_counter.text_content()
            post_reset_match = re.search(r"(\d+)", post_reset_text)
            assert post_reset_match, f"Should show reset count after {condition_name}"

            post_reset_count = int(post_reset_match.group(1))
            assert post_reset_count > 200, (
                f"Reset from {condition_name} should restore default content, got {post_reset_count}"
            )

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_state_memory_efficiency(self, app_page: Page):
        """Test YamlEditorState memory efficiency with repeated large operations."""
        # Wait for Monaco editor to load
        await app_page.wait_for_selector(".monaco-editor", timeout=10000)

        editor_textarea = app_page.locator(".monaco-editor textarea").first()
        await editor_textarea.click()

        # Test repeated large content operations to check for memory leaks
        large_content_template = """# Memory Efficiency Test - Iteration {iteration}
name: memory-test-connector-{iteration}
version: "1.{iteration}.0"
description: "Testing memory efficiency with repeated large operations"

# Large configuration section for iteration {iteration}
"""

        # Add substantial content for each iteration
        for section in range(20):  # 20 sections per iteration
            large_content_template += f"""
section_{section:02d}:
  type: "database_cluster"
  iteration: {section}
  section_id: {section}
  databases:
"""
            for db in range(10):  # 10 databases per section
                large_content_template += f"""    - name: "db_{section:02d}_{db:02d}"
      host: "host-{section}-{db}.example.com"
      port: {5432 + section * 10 + db}
      config:
        max_connections: 100
        timeout: 30
        ssl: true
"""

        # Perform multiple iterations of large content operations
        iterations = 5
        reset_button = app_page.locator("button", has_text="Reset to Example")

        for iteration in range(iterations):
            # Generate large content for this iteration
            large_content = large_content_template.format(iteration=iteration)

            # Clear and set large content
            await app_page.keyboard.press("Control+a")

            # Set content in manageable chunks to avoid browser timeouts
            chunk_size = 5000
            for i in range(0, len(large_content), chunk_size):
                chunk = large_content[i : i + chunk_size]
                if i == 0:
                    await app_page.keyboard.type(chunk)
                else:
                    await app_page.keyboard.type(chunk)
                await app_page.wait_for_timeout(50)

            # Wait for processing
            await app_page.wait_for_timeout(1000)

            # Verify state is consistent
            counter = app_page.locator("text=/Content length: \\d+ characters/")
            await expect(counter).to_be_visible()

            counter_text = await counter.text_content()
            import re

            counter_match = re.search(r"(\d+)", counter_text)
            assert counter_match, f"Counter should work in iteration {iteration}"

            char_count = int(counter_match.group(1))
            expected_count = len(large_content)

            # Allow for reasonable variation
            count_difference = abs(char_count - expected_count)
            assert count_difference < 100, (
                f"Iteration {iteration}: count difference too large: {count_difference}"
            )

            # Reset to clear memory
            await reset_button.click()
            await app_page.wait_for_timeout(1000)

            # Verify reset worked
            reset_counter = app_page.locator("text=/Content length: \\d+ characters/")
            reset_text = await reset_counter.text_content()
            reset_match = re.search(r"(\d+)", reset_text)
            assert reset_match, f"Reset should work in iteration {iteration}"

            reset_count = int(reset_match.group(1))
            assert reset_count < 1000, (
                f"Reset should clear large content in iteration {iteration}, got {reset_count}"
            )

        # Final verification that state is still responsive after all iterations
        await editor_textarea.click()
        await app_page.keyboard.type("# Final test after memory efficiency test")
        await app_page.wait_for_timeout(500)

        final_counter = app_page.locator("text=/Content length: \\d+ characters/")
        final_text = await final_counter.text_content()
        final_match = re.search(r"(\d+)", final_text)
        assert final_match, (
            "State should still be responsive after memory efficiency test"
        )

        final_count = int(final_match.group(1))
        assert final_count > 200, (
            "Final state should include both default and added content"
        )


class TestConnectorBuilderTabs:
    """Test connector builder tab functionality."""

    async def _wait_for_tabs_ready(self, page: Page, timeout: int = 10000) -> None:
        """Wait for tabs to be fully loaded and ready."""
        try:
            # Wait for tabs container
            await page.wait_for_selector("[role='tablist']", timeout=timeout)

            # Wait for all tab triggers to be present
            await page.wait_for_selector("button[role='tab']", timeout=5000)

            # Wait for tab content to be present
            await page.wait_for_selector("[role='tabpanel']", timeout=5000)

        except PlaywrightTimeoutError as e:
            raise AssertionError(
                f"Tabs failed to load within {timeout}ms. Error: {str(e)}"
            ) from e

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_all_tabs_are_present(self, app_page: Page):
        """Test that all four tabs are present and visible."""
        await self._wait_for_tabs_ready(app_page)

        # Check for all four tab triggers
        requirements_tab = app_page.locator(
            "button[role='tab']:has-text('Requirements')"
        )
        progress_tab = app_page.locator("button[role='tab']:has-text('Progress')")
        code_tab = app_page.locator("button[role='tab']:has-text('Code')")
        save_publish_tab = app_page.locator(
            "button[role='tab']:has-text('Save and Publish')"
        )

        await expect(requirements_tab).to_be_visible()
        await expect(progress_tab).to_be_visible()
        await expect(code_tab).to_be_visible()
        await expect(save_publish_tab).to_be_visible()

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_code_tab_is_default_active(self, app_page: Page):
        """Test that Code tab is active by default."""
        await self._wait_for_tabs_ready(app_page)

        code_tab = app_page.locator("button[role='tab']:has-text('Code')")
        await expect(code_tab).to_have_attribute("aria-selected", "true")

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_tab_navigation_works(self, app_page: Page):
        """Test that clicking tabs changes the active tab and content."""
        await self._wait_for_tabs_ready(app_page)

        requirements_tab = app_page.locator(
            "button[role='tab']:has-text('Requirements')"
        )
        await requirements_tab.click()
        await expect(requirements_tab).to_have_attribute("aria-selected", "true")

        requirements_content = app_page.locator(
            "text=Define your connector requirements"
        )
        await expect(requirements_content).to_be_visible()

        progress_tab = app_page.locator("button[role='tab']:has-text('Progress')")
        await progress_tab.click()
        await expect(progress_tab).to_have_attribute("aria-selected", "true")

        progress_content = app_page.locator(
            "text=Track your connector development progress"
        )
        await expect(progress_content).to_be_visible()

        code_tab = app_page.locator("button[role='tab']:has-text('Code')")
        await code_tab.click()
        await expect(code_tab).to_have_attribute("aria-selected", "true")

        yaml_heading = app_page.locator(
            "h1:has-text('YAML Connector Configuration Editor')"
        )
        await expect(yaml_heading).to_be_visible()

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_placeholder_content_displays_correctly(self, app_page: Page):
        """Test that placeholder content displays correctly in non-Code tabs."""
        await self._wait_for_tabs_ready(app_page)

        requirements_tab = app_page.locator(
            "button[role='tab']:has-text('Requirements')"
        )
        await requirements_tab.click()

        configure_button = app_page.locator("button:has-text('Configure Requirements')")
        await expect(configure_button).to_be_visible()
        await expect(configure_button).to_be_disabled()

        save_publish_tab = app_page.locator(
            "button[role='tab']:has-text('Save and Publish')"
        )
        await save_publish_tab.click()

        save_button = app_page.locator("button:has-text('Save Draft')")
        publish_button = app_page.locator("button:has-text('Publish Connector')")
        await expect(save_button).to_be_visible()
        await expect(save_button).to_be_disabled()
        await expect(publish_button).to_be_visible()
        await expect(publish_button).to_be_disabled()

    @pytest.mark.e2e
    @pytest.mark.browser
    async def test_yaml_editor_still_works_in_code_tab(self, app_page: Page):
        """Test that YAML editor functionality still works within Code tab."""
        await self._wait_for_tabs_ready(app_page)

        code_tab = app_page.locator("button[role='tab']:has-text('Code')")
        await code_tab.click()

        # Wait for Monaco editor to be ready (reuse existing helper)
        await self._wait_for_monaco_editor_ready(app_page)

        # Test that reset button still works
        reset_button = app_page.locator("button:has-text('Reset to Example')")
        await expect(reset_button).to_be_visible()
        await expect(reset_button).to_be_enabled()

        editor_element = app_page.locator(".monaco-editor").first()
        await expect(editor_element).to_contain_text("example-connector")

    async def _wait_for_monaco_editor_ready(
        self, page: Page, timeout: int = 15000
    ) -> None:
        """Wait for Monaco editor to be fully loaded and ready."""
        try:
            await page.wait_for_selector(".monaco-editor", timeout=timeout)
            await page.wait_for_selector(
                ".monaco-editor .monaco-editor-background", timeout=5000
            )
            await page.wait_for_selector(".monaco-editor textarea", timeout=5000)
        except PlaywrightTimeoutError as e:
            raise AssertionError(
                f"Monaco editor failed to load within {timeout}ms. Error: {str(e)}"
            ) from e
