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


def index() -> rx.Component:
    """Main page with tabbed connector builder interface and fixed chat sidebar."""
    return rx.box(
        rx.box(
            chat_sidebar(
                messages=ChatAgentState.chat_messages,
                current_streaming_message=ChatAgentState.current_streaming_message,
                input_value=ChatAgentState.chat_input,
                loading=ChatAgentState.chat_loading,
                on_input_change=ChatAgentState.set_chat_input,
                on_send=ChatAgentState.send_message,
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
                            has_api_key=UIState.has_api_key,
                            on_click=UIState.open_settings_modal,
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
            is_open=UIState.settings_modal_open,
            openai_api_key=UIState.openai_api_key_input,
            has_env_api_key=UIState.has_env_api_key,
            on_open_change=UIState.close_settings_modal,
            on_api_key_change=UIState.set_openai_api_key_input,
            on_save=UIState.save_settings,
        ),
    )
