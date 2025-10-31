"""Main Reflex application with YAML editor using reflex-monaco."""

import os
from pathlib import Path
from typing import Any

import reflex as rx
from dotenv import load_dotenv
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

from .components import chat_sidebar, settings_button, settings_modal
from .tabs import (
    code_tab_content,
    progress_tab_content,
    requirements_tab_content,
    save_publish_tab_content,
)

env_file = Path.cwd() / ".env"
if env_file.exists():
    load_dotenv(env_file)

SIDEBAR_WIDTH_PERCENT = "33.333%"
MAIN_CONTENT_WIDTH_PERCENT = "66.667%"
HISTORY_MAX_MESSAGES = (
    20  # Maximum number of messages to include in conversation history
)


class ConnectorBuilderState(rx.State):
    """State management for the YAML editor and tabs."""

    current_tab: str = "requirements"

    source_api_name: str = ""
    connector_name: str = ""
    documentation_urls: str = ""
    functional_requirements: str = ""
    test_list: str = ""

    settings_modal_open: bool = False
    openai_api_key_input: str = ""

    yaml_content: str = """# Example YAML configuration
name: example-connector
version: "1.0.0"
description: "A sample connector configuration"

source:
  type: api
  url: "https://api.example.com"
destination:
  type: database
  connection:
    host: localhost
    port: 5432
    database: example_db

transformations:
  - type: field_mapping
    mappings:
      id: user_id
      name: full_name
      email: email_address
"""

    chat_messages: list[dict[str, str]] = [
        {
            "role": "assistant",
            "content": "Welcome! 👋\n\nWhat connector do you want to build today?",
        }
    ]
    chat_input: str = ""
    current_streaming_message: str = ""
    chat_loading: bool = False

    def get_content_length(self) -> int:
        """Get the content length."""
        return len(self.yaml_content)

    def update_yaml_content(self, content: str):
        """Update the YAML content when editor changes."""
        self.yaml_content = content

    def reset_yaml_content(self):
        """Reset YAML content to default example."""
        self.yaml_content = """# Example YAML configuration
name: example-connector
version: "1.0.0"
description: "A sample connector configuration"

source:
  type: api
  url: "https://api.example.com"
destination:
  type: database
  connection:
    host: localhost
    port: 5432
    database: example_db

transformations:
  - type: field_mapping
    mappings:
      id: user_id
      name: full_name
      email: email_address
"""

    def set_current_tab(self, tab: str):
        """Set the current active tab."""
        self.current_tab = tab

    def set_chat_input(self, value: str):
        """Set the chat input value."""
        self.chat_input = value

    def set_source_api_name(self, value: str):
        """Set the source API name."""
        self.source_api_name = value

    def set_connector_name(self, value: str):
        """Set the connector name."""
        self.connector_name = value

    def set_documentation_urls(self, value: str):
        """Set the documentation URLs."""
        self.documentation_urls = value

    def set_functional_requirements(self, value: str):
        """Set the functional requirements."""
        self.functional_requirements = value

    def set_test_list(self, value: str):
        """Set the test list."""
        self.test_list = value

    def _convert_to_pydantic_history(
        self, messages: list[dict[str, str]]
    ) -> list[ModelMessage]:
        """Convert chat messages to PydanticAI message format.

        Args:
            messages: List of message dicts with 'role' and 'content' keys

        Returns:
            List of ModelMessage objects for PydanticAI
        """
        history = []
        for msg in messages:
            try:
                role = msg.get("role", "")
                content = msg.get("content", "")

                if role == "user":
                    history.append(
                        ModelRequest(parts=[UserPromptPart(content=content)])
                    )
                elif role == "assistant":
                    history.append(ModelResponse(parts=[TextPart(content=content)]))
            except Exception as e:
                print(f"Warning: Failed to convert message to PydanticAI format: {e}")
                continue

        return history

    def open_settings_modal(self):
        """Open the settings modal."""
        self.settings_modal_open = True

    def close_settings_modal(self):
        """Close the settings modal."""
        self.settings_modal_open = False

    def set_openai_api_key_input(self, value: str):
        """Set the OpenAI API key input value."""
        self.openai_api_key_input = value

    def save_settings(self):
        """Save settings (currently just closes modal as state is already updated)."""
        self.settings_modal_open = False

    def get_effective_api_key(self) -> str:
        """Get the effective OpenAI API key (UI input takes precedence over env var)."""
        if self.openai_api_key_input:
            return self.openai_api_key_input
        return os.environ.get("OPENAI_API_KEY", "")

    @rx.var
    def has_api_key(self) -> bool:
        """Check if an API key is configured (either from env var or UI input)."""
        return bool(self.get_effective_api_key())

    @rx.var
    def has_env_api_key(self) -> bool:
        """Check if an API key is available from environment variables (not UI input)."""
        return bool(os.environ.get("OPENAI_API_KEY", ""))

    _cached_agent: Any = None
    _cached_api_key: str | None = None
    _agent_started: bool = False

    async def _ensure_agent_started(self, effective_api_key: str):
        """Ensure the agent context is started and MCP server is running.

        This keeps the MCP server process alive for the duration of the session
        instead of starting/stopping it on each message.
        """
        from .chat_agent import create_chat_agent

        if self._cached_agent is not None and self._cached_api_key != effective_api_key:
            try:
                await self._cached_agent.__aexit__(None, None, None)
            except Exception as e:
                print(
                    f"[_ensure_agent_started] Error during agent cleanup when API key changed: {e}"
                )
            self._cached_agent = None
            self._agent_started = False

        if self._cached_agent is None:
            self._cached_agent = create_chat_agent()
            self._cached_api_key = effective_api_key
            self._agent_started = False

        if not self._agent_started:
            try:
                await self._cached_agent.__aenter__()
                self._agent_started = True
            except Exception as e:
                print(
                    f"[_ensure_agent_started] Error starting agent context for MCP server: {e}"
                )
                self._cached_agent = None
                self._agent_started = False
                raise

    async def handle_chat_keydown(self, key: str, **kwargs):
        """Handle keyboard events in the chat input."""
        if self.chat_loading:
            return

        modifiers = kwargs.get('kwargs', {})
        ctrl_key = modifiers.get('ctrl_key', False)
        meta_key = modifiers.get('meta_key', False)
        shift_key = modifiers.get('shift_key', False)

        should_submit = False

        if key == "Enter":
            if ctrl_key or meta_key:
                should_submit = True
            elif not shift_key:
                should_submit = True

        if should_submit:
            return self.send_message()

    async def send_message(self):
        """Send a message to the chat agent and get streaming response."""
        if not self.chat_input.strip():
            return

        from .chat_agent import SessionDeps

        user_message = self.chat_input.strip()
        self.chat_messages.append({"role": "user", "content": user_message})
        self.chat_input = ""
        self.chat_loading = True
        self.current_streaming_message = ""
        yield

        session_deps = SessionDeps(
            yaml_content=self.yaml_content,
            connector_name=self.connector_name,
            source_api_name=self.source_api_name,
            documentation_urls=self.documentation_urls,
            functional_requirements=self.functional_requirements,
            test_list=self.test_list,
            set_source_api_name=self.set_source_api_name,
            set_connector_name=self.set_connector_name,
            set_documentation_urls=self.set_documentation_urls,
            set_functional_requirements=self.set_functional_requirements,
            set_test_list=self.set_test_list,
        )

        recent_messages = self.chat_messages[:-1][-HISTORY_MAX_MESSAGES:]
        message_history = self._convert_to_pydantic_history(recent_messages)

        effective_api_key = self.get_effective_api_key()
        original_api_key = os.environ.get("OPENAI_API_KEY")

        try:
            if effective_api_key:
                os.environ["OPENAI_API_KEY"] = effective_api_key

            await self._ensure_agent_started(effective_api_key)
            agent = self._cached_agent

            async with agent.run_stream(
                user_message, deps=session_deps, message_history=message_history
            ) as response:
                async for text in response.stream_text():
                    self.current_streaming_message = text
                    yield

                try:
                    final_output = await response.get_output()
                    if isinstance(final_output, str):
                        self.current_streaming_message = final_output
                except Exception as e:
                    print(f"[send_message] get_output failed: {type(e).__name__}: {e}")

            self.chat_messages.append(
                {"role": "assistant", "content": self.current_streaming_message}
            )
            self.current_streaming_message = ""

            if session_deps.yaml_content != self.yaml_content:
                self.yaml_content = session_deps.yaml_content
                yield

        except Exception as e:
            self.chat_messages.append(
                {
                    "role": "assistant",
                    "content": f"Sorry, I encountered an error: {str(e)}",
                }
            )
            self.current_streaming_message = ""
        finally:
            if original_api_key is not None:
                os.environ["OPENAI_API_KEY"] = original_api_key
            elif effective_api_key:
                os.environ.pop("OPENAI_API_KEY", None)
            self.chat_loading = False


def connector_builder_tabs() -> rx.Component:
    """Create the main tabs component with all modalities."""
    return rx.tabs.root(
        rx.tabs.list(
            rx.tabs.trigger("📋 Define Requirements", value="requirements"),
            rx.tabs.trigger("⚙️ Connector Build Progress", value="progress"),
            rx.tabs.trigger("</> Code Review", value="code"),
            rx.tabs.trigger("💾 Save and Publish", value="save_publish"),
        ),
        rx.tabs.content(
            requirements_tab_content(
                source_api_name=ConnectorBuilderState.source_api_name,
                connector_name=ConnectorBuilderState.connector_name,
                documentation_urls=ConnectorBuilderState.documentation_urls,
                functional_requirements=ConnectorBuilderState.functional_requirements,
                test_list=ConnectorBuilderState.test_list,
                on_source_api_name_change=ConnectorBuilderState.set_source_api_name,
                on_connector_name_change=ConnectorBuilderState.set_connector_name,
                on_documentation_urls_change=ConnectorBuilderState.set_documentation_urls,
                on_functional_requirements_change=ConnectorBuilderState.set_functional_requirements,
                on_test_list_change=ConnectorBuilderState.set_test_list,
            ),
            value="requirements",
        ),
        rx.tabs.content(
            progress_tab_content(),
            value="progress",
        ),
        rx.tabs.content(
            code_tab_content(
                yaml_content=ConnectorBuilderState.yaml_content,
                on_change=ConnectorBuilderState.update_yaml_content,
                on_reset=ConnectorBuilderState.reset_yaml_content,
            ),
            value="code",
        ),
        rx.tabs.content(
            save_publish_tab_content(),
            value="save_publish",
        ),
        default_value="requirements",
        value=ConnectorBuilderState.current_tab,
        on_change=ConnectorBuilderState.set_current_tab,
        width="100%",
    )


def index() -> rx.Component:
    """Main page with tabbed connector builder interface and fixed chat sidebar."""
    return rx.box(
        rx.box(
            chat_sidebar(
                messages=ConnectorBuilderState.chat_messages,
                current_streaming_message=ConnectorBuilderState.current_streaming_message,
                input_value=ConnectorBuilderState.chat_input,
                loading=ConnectorBuilderState.chat_loading,
                on_input_change=ConnectorBuilderState.set_chat_input,
                on_send=ConnectorBuilderState.send_message,
                on_key_down=ConnectorBuilderState.handle_chat_keydown,
            ),
            position="fixed",
            left="0",
            top="0",
            width=SIDEBAR_WIDTH_PERCENT,
            height="100vh",
            background="gray.900",
            border_right="2px solid",
            border_color="gray.700",
            padding="6",
            overflow_y="auto",
            z_index="10",
        ),
        rx.box(
            rx.container(
                rx.vstack(
                    rx.flex(
                        rx.heading(
                            "Agentic Connector Builder",
                            size="9",
                            text_align="center",
                        ),
                        settings_button(
                            has_api_key=ConnectorBuilderState.has_api_key,
                            on_click=ConnectorBuilderState.open_settings_modal,
                        ),
                        justify="center",
                        align="center",
                        gap="4",
                        width="100%",
                        mb=6,
                    ),
                    rx.text(
                        "Build and configure data connectors using YAML",
                        text_align="center",
                        color="gray.600",
                        mb=8,
                    ),
                    connector_builder_tabs(),
                    spacing="6",
                    width="100%",
                    max_width="1200px",
                    mx="auto",
                    py=8,
                ),
                width="100%",
                height="100vh",
            ),
            margin_left=SIDEBAR_WIDTH_PERCENT,
            width=MAIN_CONTENT_WIDTH_PERCENT,
        ),
        settings_modal(
            is_open=ConnectorBuilderState.settings_modal_open,
            openai_api_key=ConnectorBuilderState.openai_api_key_input,
            has_env_api_key=ConnectorBuilderState.has_env_api_key,
            on_open_change=ConnectorBuilderState.close_settings_modal,
            on_api_key_change=ConnectorBuilderState.set_openai_api_key_input,
            on_save=ConnectorBuilderState.save_settings,
        ),
    )


# Create the Reflex app
app = rx.App(
    theme=rx.theme(
        appearance="dark",
        has_background=True,
        radius="medium",
        accent_color="blue",
    )
)

# Add the main page
app.add_page(index, route="/", title="Agentic Connector Builder")
