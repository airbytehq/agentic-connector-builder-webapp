"""Code tab component."""

import reflex as rx

from ..components.yaml_editor import yaml_editor_component


def code_tab_content(yaml_content: str, on_change, on_reset) -> rx.Component:
    """Code tab content with YAML editor."""
    return yaml_editor_component(
        yaml_content=yaml_content, on_change=on_change, on_reset=on_reset
    )
