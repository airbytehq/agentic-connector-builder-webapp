"""Progress tab component."""

import reflex as rx


def progress_tab_content() -> rx.Component:
    """Placeholder content for Progress tab."""
    return rx.vstack(
        rx.heading("Progress", size="6", mb=4),
        rx.text(
            "Track your connector development progress here.",
            color="gray.500",
            size="4",
            mb=4,
        ),
        rx.vstack(
            rx.hstack(
                rx.text("○", color="gray.400"),
                rx.text("Requirements defined", color="gray.400"),
                spacing="2",
            ),
            rx.hstack(
                rx.text("○", color="gray.400"),
                rx.text("Configuration completed", color="gray.400"),
                spacing="2",
            ),
            rx.hstack(
                rx.text("○", color="gray.400"),
                rx.text("Testing completed", color="gray.400"),
                spacing="2",
            ),
            rx.hstack(
                rx.text("○", color="gray.400"),
                rx.text("Ready for deployment", color="gray.400"),
                spacing="2",
            ),
            spacing="3",
            align="start",
            mb=6,
        ),
        rx.button(
            "View Detailed Progress",
            disabled=True,
            color_scheme="gray",
            size="3",
        ),
        spacing="4",
        align="start",
        width="100%",
    )
