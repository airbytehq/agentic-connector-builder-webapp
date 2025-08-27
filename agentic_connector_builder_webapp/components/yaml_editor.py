"""YAML editor component using reflex-monaco."""

import reflex as rx
from reflex_monaco import monaco


def yaml_editor_component(yaml_content: str, on_change, on_reset) -> rx.Component:
    """Create the Monaco YAML editor component."""
    return rx.vstack(
        rx.heading("YAML Connector Configuration Editor", size="6", mb=4),
        rx.hstack(
            rx.button(
                "Reset to Example",
                on_click=on_reset,
                color_scheme="blue",
                size="2",
            ),
            rx.spacer(),
            rx.text(
                "Content length will be calculated dynamically",
                color="gray.600",
                size="2",
            ),
            width="100%",
            mb=2,
        ),
        monaco(
            value=yaml_content,
            language="yaml",
            theme="vs-dark",
            height="500px",
            width="100%",
            on_change=on_change,
            options={
                "minimap": {"enabled": False},
                "fontSize": 14,
                "lineNumbers": "on",
                "roundedSelection": False,
                "scrollBeyondLastLine": False,
                "automaticLayout": True,
                "tabSize": 2,
                "insertSpaces": True,
                "wordWrap": "on",
            },
        ),
        width="100%",
        height="100%",
        spacing="4",
    )
