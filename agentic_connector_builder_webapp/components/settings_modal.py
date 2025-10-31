"""Settings modal component for OpenAI API key configuration."""

import reflex as rx


def settings_modal(
    is_open: bool,
    openai_api_key: str,
    on_open_change: callable,
    on_api_key_change: callable,
    on_save: callable,
) -> rx.Component:
    """Create a settings modal for configuring OpenAI API key.

    Args:
        is_open: Whether the modal is open
        openai_api_key: Current API key value
        on_open_change: Callback when modal open state changes
        on_api_key_change: Callback when API key input changes
        on_save: Callback when save button is clicked

    Returns:
        Settings modal component
    """
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Settings"),
            rx.dialog.description(
                "Configure your OpenAI API key for the AI assistant.",
                size="2",
                mb="4",
            ),
            rx.flex(
                rx.text(
                    "OpenAI API Key",
                    as_="div",
                    size="2",
                    mb="1",
                    weight="bold",
                ),
                rx.input(
                    placeholder="sk-...",
                    type="password",
                    value=openai_api_key,
                    on_change=on_api_key_change,
                    width="100%",
                ),
                rx.text(
                    "Your API key is stored locally in your browser session and is not sent to any server except OpenAI.",
                    size="1",
                    color="gray",
                    mt="2",
                ),
                rx.text(
                    "Don't have a key? ",
                    rx.link(
                        "Click here to create a new key.",
                        href="https://platform.openai.com/api-keys",
                        target="_blank",
                        rel="noopener noreferrer",
                        color="blue",
                    ),
                    size="1",
                    color="gray",
                    mt="1",
                ),
                direction="column",
                spacing="3",
            ),
            rx.flex(
                rx.dialog.close(
                    rx.button(
                        "Cancel",
                        variant="soft",
                        color_scheme="gray",
                    ),
                ),
                rx.dialog.close(
                    rx.button(
                        "Save",
                        on_click=on_save,
                    ),
                ),
                spacing="3",
                mt="4",
                justify="end",
            ),
            max_width="450px",
        ),
        open=is_open,
        on_open_change=on_open_change,
    )


def settings_button(
    has_api_key: bool,
    on_click: callable,
) -> rx.Component:
    """Create a settings button with optional warning indicator.

    Args:
        has_api_key: Whether an API key is configured
        on_click: Callback when button is clicked

    Returns:
        Settings button component with gear icon and optional warning
    """
    return rx.button(
        rx.icon(
            "settings",
            size=20,
        ),
        rx.cond(
            has_api_key,
            rx.fragment(),
            rx.icon(
                "circle-alert",
                size=16,
                color="red",
                position="absolute",
                top="-4px",
                right="-4px",
            ),
        ),
        on_click=on_click,
        variant="soft",
        color_scheme="gray",
        size="3",
        position="relative",
        cursor="pointer",
    )
