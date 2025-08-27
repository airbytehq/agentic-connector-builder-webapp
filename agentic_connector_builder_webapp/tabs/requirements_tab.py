"""Requirements tab component."""

import reflex as rx


def requirements_tab_content() -> rx.Component:
    """Placeholder content for Requirements tab."""
    return rx.vstack(
        rx.heading("Requirements", size="6", mb=4),
        rx.text(
            "Define your connector requirements and specifications here.",
            color="gray.500",
            size="4",
            mb=4,
        ),
        rx.vstack(
            rx.text("• Data source requirements", color="gray.400"),
            rx.text("• Performance specifications", color="gray.400"),
            rx.text("• Security requirements", color="gray.400"),
            rx.text("• Compliance needs", color="gray.400"),
            spacing="2",
            align="start",
            mb=6,
        ),
        rx.button(
            "Configure Requirements",
            disabled=True,
            color_scheme="gray",
            size="3",
        ),
        spacing="4",
        align="start",
        width="100%",
    )
