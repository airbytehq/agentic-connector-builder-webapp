"""Chat sidebar component using Reflex drawer."""

import reflex as rx


def chat_bubble(message_str, is_user: bool) -> rx.Component:
    """Render a chat bubble."""
    return rx.card(
        rx.text(
            message_str,
            size="2",
            color=rx.cond(is_user, "white", "gray.100"),
        ),
        background=rx.cond(is_user, "blue.500", "gray.800"),
        border="1px solid silver",
        padding="20",
        p="20",
        border_radius="16px",
        max_width="85%",
        align_self=rx.cond(is_user, "flex-end", "flex-start"),
        margin_left=rx.cond(is_user, "auto", "8px"),
        margin_right=rx.cond(is_user, "8px", "auto"),
        margin_top="4px",
        margin_bottom="4px",
    )


def chat_message(message: dict) -> rx.Component:
    """Render a single chat message."""
    return chat_bubble(
        message["content"],
        is_user=message["role"] == "user",
    )


def streaming_message(content: str) -> rx.Component:
    """Render the currently streaming message."""
    return chat_bubble(
        content + "\n\n ... ",
        is_user=False,
    )


def chat_sidebar(
    messages,
    current_streaming_message,
    input_value,
    loading,
    on_input_change,
    on_send,
) -> rx.Component:
    """Create the fixed chat sidebar component."""
    return rx.vstack(
        rx.vstack(
            rx.heading("💬 Chat Assistant", size="7", weight="bold"),
            rx.text(
                "Ask questions about connector building",
                size="2",
                color="gray.400",
            ),
            spacing="2",
            mb=6,
            pb=4,
            border_bottom="1px solid",
            border_color="gray.700",
            width="100%",
        ),
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
            flex="1",
            width="100%",
        ),
        rx.form(
            rx.hstack(
                rx.text_area(
                    placeholder="Ask me anything about connector building...",
                    value=input_value,
                    on_change=on_input_change,
                    disabled=loading,
                    width="100%",
                    size="3",
                ),
                rx.tooltip(
                    rx.button(
                        "Send",
                        type="submit",
                        loading=loading,
                        size="3",
                    ),
                    content="Press Cmd+Enter to send your message",
                ),
                width="100%",
            ),
            on_submit=on_send,
            width="100%",
            mt=4,
        ),
        spacing="4",
        width="100%",
        height="100%",
    )
