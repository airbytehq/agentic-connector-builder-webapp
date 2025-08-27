"""Save and Publish tab component."""

import reflex as rx


def save_publish_tab_content() -> rx.Component:
    """Placeholder content for Save and Publish tab."""
    return rx.vstack(
        rx.heading("Save and Publish", size="6", mb=4),
        rx.text(
            "Save your connector configuration and publish it for use.",
            color="gray.500",
            size="4",
            mb=4,
        ),
        rx.vstack(
            rx.hstack(
                rx.button(
                    "Save Draft",
                    disabled=True,
                    color_scheme="gray",
                    size="3",
                ),
                rx.button(
                    "Validate Configuration",
                    disabled=True,
                    color_scheme="gray",
                    size="3",
                ),
                spacing="3",
            ),
            rx.button(
                "Publish Connector",
                disabled=True,
                color_scheme="gray",
                size="3",
                width="200px",
            ),
            spacing="4",
            align="start",
            mb=6,
        ),
        rx.text(
            "Publishing will make your connector available for use in data pipelines.",
            color="gray.400",
            size="2",
        ),
        spacing="4",
        align="start",
        width="100%",
    )
