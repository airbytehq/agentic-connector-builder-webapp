"""Requirements tab component."""

import reflex as rx


def requirements_tab_content(
    source_api_name: str,
    connector_name: str,
    documentation_urls: str,
    functional_requirements: str,
    test_list: str,
    on_source_api_name_change,
    on_connector_name_change,
    on_documentation_urls_change,
    on_functional_requirements_change,
    on_test_list_change,
) -> rx.Component:
    """Requirements tab content with form inputs."""
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
                placeholder="assert response.status_code == 200\nassert 'data' in response.json()\nassert len(response.json()['data']) > 0",
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
