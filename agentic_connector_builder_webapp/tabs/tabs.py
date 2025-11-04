import reflex as rx

from ..state import BuilderState, UIState
from .code_tab import code_tab_content
from .progress_tab import progress_tab_content
from .requirements_tab import requirements_tab_content
from .save_publish_tab import save_publish_tab_content


def connector_builder_tabs() -> rx.Component:
    """Create the main tabs component with all modalities."""
    return rx.tabs.root(
        rx.tabs.list(
            rx.tabs.trigger("📋 Define Requirements", value="requirements"),
            rx.tabs.trigger("⚙️ Connector Build Progress", value="progress"),
            rx.tabs.trigger("</> Code Review", value="code"),
            rx.tabs.trigger("💾 Save and Publish", value="save_publish"),
        ),
        rx.tabs.content(
            requirements_tab_content(
                source_api_name=BuilderState.source_api_name,
                connector_name=BuilderState.connector_name,
                documentation_urls=BuilderState.documentation_urls,
                functional_requirements=BuilderState.functional_requirements,
                test_list=BuilderState.test_list,
                on_source_api_name_change=BuilderState.set_source_api_name,
                on_connector_name_change=BuilderState.set_connector_name,
                on_documentation_urls_change=BuilderState.set_documentation_urls,
                on_functional_requirements_change=BuilderState.set_functional_requirements,
                on_test_list_change=BuilderState.set_test_list,
            ),
            value="requirements",
        ),
        rx.tabs.content(
            progress_tab_content(),
            value="progress",
        ),
        rx.tabs.content(
            code_tab_content(
                yaml_content=BuilderState.yaml_content,
                on_change=BuilderState.update_yaml_content,
                on_reset=BuilderState.reset_yaml_content,
            ),
            value="code",
        ),
        rx.tabs.content(
            save_publish_tab_content(),
            value="save_publish",
        ),
        default_value="requirements",
        value=UIState.current_tab,
        on_change=UIState.set_current_tab,
        width="100%",
    )
