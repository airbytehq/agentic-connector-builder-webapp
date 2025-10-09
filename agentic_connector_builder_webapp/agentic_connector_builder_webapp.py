"""Main Reflex application with YAML editor using reflex-monaco."""

import reflex as rx

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

    chat_messages: list[dict[str, str]] = []
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

    async def send_message(self):
        """Send a message to the chat agent and get streaming response."""
        if not self.chat_input.strip():
            return

        from .chat_agent import SessionDeps, chat_agent

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
        )

        try:
            async with chat_agent:
                async with chat_agent.run_stream(
                    user_message, deps=session_deps
                ) as response:
                    async for text in response.stream_text():
                        self.current_streaming_message = text
                        yield

                self.chat_messages.append(
                    {"role": "assistant", "content": self.current_streaming_message}
                )
                self.current_streaming_message = ""

                if session_deps.yaml_content != self.yaml_content:
                    self.yaml_content = session_deps.yaml_content
                    yield  # Trigger UI update for yaml_content change

        except Exception as e:
            self.chat_messages.append(
                {
                    "role": "assistant",
                    "content": f"Sorry, I encountered an error: {str(e)}",
                }
            )
            self.current_streaming_message = ""
        finally:
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
