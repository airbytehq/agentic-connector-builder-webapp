"""Main Reflex application with YAML editor using reflex-monaco."""

import reflex as rx
from reflex_monaco import monaco


class MonacoYamlEditor(rx.Component):
    """Custom Monaco YAML editor with schema validation support."""
    
    library = "@monaco-editor/react@4.7.0"
    tag = "MonacoEditor"
    is_default = True
    
    # Basic Monaco editor properties
    value: rx.Var[str]
    language: rx.Var[str] = "yaml"
    theme: rx.Var[str] = "vs-dark"
    height: rx.Var[str] = "500px"
    width: rx.Var[str] = "100%"
    
    # Event handlers
    on_change: rx.EventHandler[rx.event.passthrough_event_spec(str)]
    on_validate: rx.EventHandler[rx.event.passthrough_event_spec(str)]
    
    # Monaco editor options
    options: rx.Var[dict] = {}
    
    def add_imports(self) -> dict[str, str]:
        """Add necessary imports for monaco-yaml integration."""
        return {
            "monaco-yaml": "configureMonacoYaml",
            "monaco-editor": "* as monaco",
        }
    
    def add_hooks(self) -> list[str]:
        """Add React hooks for monaco-yaml configuration."""
        airbyte_schema_url = "https://raw.githubusercontent.com/airbytehq/airbyte-python-cdk/bd615ad80b4326174b34f18f3f3bbbdbedb608fb/airbyte_cdk/sources/declarative/generated/declarative_component_schema.json"
        
        return [
            f"""
            React.useEffect(() => {{
                // Configure monaco-yaml with Airbyte schema validation
                if (typeof configureMonacoYaml !== 'undefined' && typeof monaco !== 'undefined') {{
                    try {{
                        configureMonacoYaml(monaco, {{
                            enableSchemaRequest: true,
                            validate: true,
                            hover: true,
                            completion: true,
                            schemas: [
                                {{
                                    uri: "{airbyte_schema_url}",
                                    fileMatch: ["**/*.yaml", "**/*.yml", "inmemory://model.yaml"],
                                }}
                            ],
                        }});
                        console.log('Monaco YAML configured with Airbyte schema validation');
                    }} catch (error) {{
                        console.warn('Failed to configure monaco-yaml:', error);
                    }}
                }}
            }}, []);
            """
        ]


# Create the custom Monaco YAML editor component
monaco_yaml_editor = MonacoYamlEditor.create


class YamlEditorState(rx.State):
    """State management for the YAML editor."""
    
    yaml_content: str = """# Example YAML configuration
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


def yaml_editor_component() -> rx.Component:
    """Create the Monaco YAML editor component."""
    return rx.vstack(
        rx.heading("YAML Connector Configuration Editor", size="6", mb=4),
        rx.hstack(
            rx.button(
                "Reset to Example",
                on_click=YamlEditorState.reset_yaml_content,
                color_scheme="blue",
                size="2",
            ),
            rx.spacer(),
            rx.text(
                f"Content length: {YamlEditorState.yaml_content.length()} characters",
                color="gray.600",
                size="2",
            ),
            width="100%",
            mb=2,
        ),
        monaco(
            value=YamlEditorState.yaml_content,
            language="yaml",
            theme="vs-dark",
            height="500px",
            width="100%",
            on_change=YamlEditorState.update_yaml_content,
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


def index() -> rx.Component:
    """Main page with YAML editor."""
    return rx.container(
        rx.vstack(
            rx.heading(
                "Agentic Connector Builder",
                size="9",
                text_align="center",
                mb=6,
            ),
            rx.text(
                "Build and configure data connectors using YAML",
                text_align="center",
                color="gray.600",
                mb=8,
            ),
            yaml_editor_component(),
            spacing="6",
            width="100%",
            max_width="1200px",
            mx="auto",
            py=8,
        ),
        width="100%",
        height="100vh",
    )


# Create the Reflex app
app = rx.App(
    theme=rx.theme(
        appearance="dark",
        has_background=True,
        radius="medium",
        accent_color="blue",
    )
)

# Add the main page
app.add_page(index, route="/", title="Agentic Connector Builder")









