"""Main Reflex application with YAML editor using reflex-monaco."""

import asyncio
import json
from datetime import UTC, datetime

import reflex as rx
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

from .components import chat_sidebar
from .tabs import (
    code_tab_content,
    progress_tab_content,
    requirements_tab_content,
    save_publish_tab_content,
)

SIDEBAR_WIDTH_PERCENT = "33.333%"
MAIN_CONTENT_WIDTH_PERCENT = "66.667%"


class ConnectorBuilderState(rx.State):
    """State management for the YAML editor and tabs."""

    current_tab: str = "requirements"

    source_api_name: str = ""
    connector_name: str = ""
    documentation_urls: str = ""
    functional_requirements: str = ""
    test_list: str = ""

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

    chat_messages: list[ModelMessage] = []
    chat_input: str = ""
    current_streaming_message: str = ""
    chat_loading: bool = False
    agent_paused: bool = False
    agent_running: bool = False
    agent_should_stop: bool = False

    @rx.var
    def display_messages(self) -> list[dict[str, str]]:
        """Convert ModelMessage objects to simple dicts for UI display."""
        result = []
        for msg in self.chat_messages:
            try:
                if isinstance(msg, ModelRequest):
                    content = msg.parts[0].content if msg.parts else ""
                    result.append({"role": "user", "content": str(content)})
                elif isinstance(msg, ModelResponse):
                    content = ""
                    for part in msg.parts:
                        if hasattr(part, "content"):
                            part_content = part.content
                            if isinstance(part_content, (dict, list)):
                                content += json.dumps(part_content, indent=2)
                            else:
                                content += str(part_content)
                    result.append({"role": "assistant", "content": content})
            except Exception:
                continue
        return result

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

    async def toggle_pause(self):
        """Toggle pause state for the agent."""
        if self.agent_paused:
            self.agent_paused = False
            yield
            async for _ in self._run_autonomous_loop():
                yield
        else:
            self.agent_paused = True
            yield

    async def send_message(self):
        """Send a message to the chat agent and start autonomous loop."""
        if not self.chat_input.strip():
            return

        user_message = self.chat_input.strip()

        user_msg = ModelRequest(
            parts=[UserPromptPart(content=user_message, timestamp=datetime.now(tz=UTC))]
        )
        self.chat_messages.append(user_msg)
        self.chat_input = ""
        self.chat_loading = True
        self.agent_running = True
        self.agent_paused = False
        self.agent_should_stop = False
        self.current_streaming_message = ""
        yield

        async for _ in self._run_autonomous_loop():
            yield

    async def _run_autonomous_loop(self):
        """Run the agent in an autonomous loop until paused or stopped."""
        from .chat_agent import SessionDeps, chat_agent

        while not self.agent_paused and not self.agent_should_stop:
            session_deps = SessionDeps(
                yaml_content=self.yaml_content,
                connector_name=self.connector_name,
                source_api_name=self.source_api_name,
                documentation_urls=self.documentation_urls,
                functional_requirements=self.functional_requirements,
                test_list=self.test_list,
            )

            try:
                async with chat_agent:
                    if len(self.chat_messages) == 1:
                        prompt = self.chat_messages[0].parts[0].content
                        message_history = []
                    else:
                        prompt = "Continue working on the task."
                        message_history = self.chat_messages

                    async with chat_agent.run_stream(
                        prompt, message_history=message_history, deps=session_deps
                    ) as response:
                        async for text in response.stream_text():
                            if self.agent_paused:
                                break
                            self.current_streaming_message = str(text)
                            yield

                        if not self.agent_paused:
                            new_messages = response.new_messages()
                            self.chat_messages.extend(new_messages)
                            self.current_streaming_message = ""

                            for msg in new_messages:
                                if hasattr(msg, "parts"):
                                    for part in msg.parts:
                                        if hasattr(part, "content"):
                                            content = str(part.content)
                                            if (
                                                "✅ Task completed successfully"
                                                in content
                                                or "❌ Task failed" in content
                                            ):
                                                self.agent_should_stop = True
                                                break
                                if self.agent_should_stop:
                                    break

                            if session_deps.yaml_content != self.yaml_content:
                                self.yaml_content = session_deps.yaml_content

                            yield

            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                error_response = ModelResponse(
                    parts=[TextPart(error_msg)], timestamp=datetime.now(tz=UTC)
                )
                self.chat_messages.append(error_response)
                self.current_streaming_message = ""
                self.agent_should_stop = True
                yield
                break  # Exit loop on error

            if not self.agent_paused and not self.agent_should_stop:
                await asyncio.sleep(1.0)
                yield  # Yield after sleep to maintain generator

        self.chat_loading = False
        self.agent_running = False


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
                messages=ConnectorBuilderState.display_messages,
                current_streaming_message=ConnectorBuilderState.current_streaming_message,
                input_value=ConnectorBuilderState.chat_input,
                loading=ConnectorBuilderState.chat_loading,
                agent_paused=ConnectorBuilderState.agent_paused,
                agent_running=ConnectorBuilderState.agent_running,
                on_input_change=ConnectorBuilderState.set_chat_input,
                on_send=ConnectorBuilderState.send_message,
                on_toggle_pause=ConnectorBuilderState.toggle_pause,
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
                    rx.heading(
                        "Agentic Connector Builder",
                        size="9",
                        text_align="center",
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
