"""Chat sidebar component using Reflex drawer."""

import reflex as rx


def chat_message(message: dict) -> rx.Component:
    """Render a single chat message."""
    is_user = message["role"] == "user"
    return rx.box(
        rx.text(
            message["content"],
            size="2",
            color=rx.cond(is_user, "white", "gray.100"),
        ),
        background=rx.cond(is_user, "blue.600", "gray.700"),
        padding="3",
        border_radius="lg",
        max_width="80%",
        align_self=rx.cond(is_user, "flex-end", "flex-start"),
    )


def streaming_message(content: str) -> rx.Component:
    """Render the currently streaming message."""
    return rx.box(
        rx.text(
            content,
            size="2",
            color="gray.100",
        ),
        background="gray.700",
        padding="3",
        border_radius="lg",
        max_width="80%",
        align_self="flex-start",
    )


def chat_sidebar(
    messages,
    current_streaming_message,
    input_value,
    loading,
    on_input_change,
    on_send,
) -> rx.Component:
    """Create the chat sidebar drawer content."""
    return rx.vstack(
        rx.heading("Chat Assistant", size="6", mb=4),
        rx.scroll_area(
            rx.vstack(
                rx.foreach(messages, chat_message),
                rx.cond(
                    current_streaming_message,
                    streaming_message(current_streaming_message),
                    rx.fragment(),
                ),
                spacing="3",
                width="100%",
            ),
            height="400px",
            width="100%",
        ),
        rx.form(
            rx.hstack(
                rx.input(
                    placeholder="Ask me anything about connector building...",
                    value=input_value,
                    on_change=on_input_change,
                    disabled=loading,
                    width="100%",
                    size="3",
                ),
                rx.button(
                    "Send",
                    type="submit",
                    loading=loading,
                    size="3",
                ),
                width="100%",
            ),
            on_submit=on_send,
            width="100%",
        ),
        spacing="4",
        width="100%",
        height="100%",
    )
