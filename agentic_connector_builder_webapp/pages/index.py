"""Main page."""

from pathlib import Path

import reflex as rx
from dotenv import load_dotenv

from ..components import chat_sidebar, settings_button, settings_modal
from ..state import ChatAgentState, UIState
from ..tabs.tabs import connector_builder_tabs

env_file = Path.cwd() / ".env"
if env_file.exists():
    load_dotenv(env_file)

SIDEBAR_WIDTH_PERCENT = "33.333%"
MAIN_CONTENT_WIDTH_PERCENT = "66.667%"
HEADER_HEIGHT = "72px"


def index() -> rx.Component:
    """Main page with tabbed connector builder interface, fixed header, and fixed chat sidebar."""
    return rx.box(
        rx.box(
            rx.box(
                rx.flex(
                    rx.flex(
                        rx.box(
                            rx.link(
                                rx.image(
                                    src="/airbyte-logo-light.png",
                                    alt="Airbyte Logo",
                                    height="60px",
                                    width="auto",
                                    class_name="logo",
                                ),
                                href="https://airbyte.com",
                                is_external=True,
                            ),
                            mx="2",
                        ),
                        rx.heading(
                            "AI Connector Builder",
                            size="8",
                            class_name="header-title",
                        ),
                        gap="4",
                        align="center",
                    ),
                    settings_button(
                        has_api_key=UIState.has_api_key,
                        on_click=UIState.open_settings_modal,
                    ),
                    justify="between",
                    align="center",
                    width="100%",
                ),
                px="6",
                height=HEADER_HEIGHT,
                display="flex",
                align_items="center",
                class_name="app-header",
            ),
            position="fixed",
            top="0",
            left="0",
            width="100%",
            z_index="20",
            background="gray.900",
            border_bottom="1px solid",
            border_color="gray.600",
        ),
        rx.box(
            chat_sidebar(
                messages=ChatAgentState.chat_messages,
                current_streaming_message=ChatAgentState.current_streaming_message,
                input_value=ChatAgentState.chat_input,
                agent_running=ChatAgentState.agent_running,
                on_input_change=ChatAgentState.set_chat_input,
                on_send=ChatAgentState.send_message,
            ),
            position="fixed",
            left="0",
            top=HEADER_HEIGHT,
            width=SIDEBAR_WIDTH_PERCENT,
            height=f"calc(100vh - {HEADER_HEIGHT})",
            background="gray.900",
            border_right="1px solid",
            border_color="gray.600",
            padding="6",
            overflow_y="auto",
            z_index="10",
        ),
        rx.box(
            rx.container(
                rx.vstack(
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
            ),
            margin_left=SIDEBAR_WIDTH_PERCENT,
            margin_top=HEADER_HEIGHT,
            width=MAIN_CONTENT_WIDTH_PERCENT,
        ),
        settings_modal(
            is_open=UIState.settings_modal_open,
            openai_api_key=UIState.openai_api_key_input,
            has_env_api_key=UIState.has_env_api_key,
            on_open_change=UIState.close_settings_modal,
            on_api_key_change=UIState.set_openai_api_key_input,
            on_save=UIState.save_settings,
        ),
    )
