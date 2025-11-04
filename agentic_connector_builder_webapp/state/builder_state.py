"""Builder state for connector configuration."""

import reflex as rx


class BuilderState(rx.State):
    """State for connector builder form fields and YAML manifest."""

    # Form field values
    source_api_name: str = ""
    connector_name: str = ""
    documentation_urls: str = ""
    functional_requirements: str = ""
    test_list: str = ""

    # YAML manifest content
    yaml_content: str = """# Note: This is an empty YAML configuration. You can start building your connector here.
# The LLM will run its scaffold tool to populate this, or else you can manually paste a YAML manifest here.
"""

    def set_source_api_name(self, value: str):
        """Set the source API name."""
        self.source_api_name = value

    def set_connector_name(self, value: str):
        """Set the connector name."""
        self.connector_name = value

    def set_documentation_urls(self, value: str):
        """Set the documentation URLs."""
        self.documentation_urls = value

    def set_functional_requirements(self, value: str):
        """Set the functional requirements."""
        self.functional_requirements = value

    def set_test_list(self, value: str):
        """Set the test list."""
        self.test_list = value

    def update_yaml_content(self, content: str):
        """Update the YAML content when editor changes."""
        self.yaml_content = content

    def reset_yaml_content(self):
        """Reset YAML content to default example."""
        self.yaml_content = """# Example YAML configuration
name: example-connector
version: "1.0.0"
description: "A sample connector configuration"

source:
  type: api
  url: "https://api.example.com"
destination:
  type: database
  connection:
    host: localhost
    port: 5432
    database: example_db

transformations:
  - type: field_mapping
    mappings:
      id: user_id
      name: full_name
      email: email_address
"""

    def get_content_length(self) -> int:
        """Get the content length."""
        return len(self.yaml_content)
