"""Requirements tab component."""

from collections.abc import Callable

import reflex as rx


def requirements_tab_content(
    source_api_name: str,
    connector_name: str,
    documentation_urls: str,
    functional_requirements: str,
    test_list: str,
    on_source_api_name_change: Callable[[str], None],
    on_connector_name_change: Callable[[str], None],
    on_documentation_urls_change: Callable[[str], None],
    on_functional_requirements_change: Callable[[str], None],
    on_test_list_change: Callable[[str], None],
) -> rx.Component:
    """Requirements tab content with form inputs.

    Args:
        source_api_name: Current value of the source API name field
        connector_name: Current value of the connector name field
        documentation_urls: Current value of the documentation URLs field
        functional_requirements: Current value of the functional requirements field
        test_list: Current value of the test list field
        on_source_api_name_change: Callback for source API name changes
        on_connector_name_change: Callback for connector name changes
        on_documentation_urls_change: Callback for documentation URLs changes
        on_functional_requirements_change: Callback for functional requirements changes
        on_test_list_change: Callback for test list changes
    """
    fields_disabled = source_api_name.strip() == ""

    return rx.vstack(
        rx.heading("Requirements", size="6", mb=4),
        rx.text(
            "Define your connector requirements and specifications.",
            color="gray.500",
            size="4",
            mb=6,
        ),
        rx.vstack(
            rx.text("Source API name", weight="bold", size="3"),
            rx.input(
                placeholder="e.g., GitHub API, Stripe API, Salesforce API",
                value=source_api_name,
                on_change=on_source_api_name_change,
                width="100%",
                size="3",
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        rx.vstack(
            rx.text("Connector name", weight="bold", size="3"),
            rx.input(
                placeholder="e.g., source-github, source-stripe",
                value=connector_name,
                on_change=on_connector_name_change,
                disabled=fields_disabled,
                width="100%",
                size="3",
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        rx.vstack(
            rx.text("Documentation URLs (Optional)", weight="bold", size="3"),
            rx.text(
                "Enter each URL on a new line",
                color="gray.400",
                size="2",
            ),
            rx.text_area(
                placeholder="https://docs.example.com/api\nhttps://developer.example.com/reference",
                value=documentation_urls,
                on_change=on_documentation_urls_change,
                disabled=fields_disabled,
                width="100%",
                height="100px",
                resize="vertical",
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        rx.vstack(
            rx.text(
                "Additional functional requirements (Optional)", weight="bold", size="3"
            ),
            rx.text_area(
                placeholder="Describe any specific requirements, rate limits, authentication needs, etc.",
                value=functional_requirements,
                on_change=on_functional_requirements_change,
                disabled=fields_disabled,
                width="100%",
                height="120px",
                resize="vertical",
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        rx.vstack(
            rx.text("List of tests (Optional)", weight="bold", size="3"),
            rx.text(
                "Write each test as an assertion, one per line",
                color="gray.400",
                size="2",
            ),
            rx.text_area(
                placeholder=(
                    "All streams should have at least 50 records.\n"
                    "The 'transactions' stream should have at least a thousand records."
                ),
                value=test_list,
                on_change=on_test_list_change,
                disabled=fields_disabled,
                width="100%",
                height="120px",
                resize="vertical",
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        spacing="6",
        align="start",
        width="100%",
    )
