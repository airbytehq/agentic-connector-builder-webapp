"""Main Reflex application with YAML editor using reflex-monaco."""

import reflex as rx
import yaml
from reflex_monaco import monaco
from reflex_monaco.monaco import MonacoEditor


class YamlValidationMonaco(MonacoEditor):
    """Monaco Editor with Python-based YAML syntax validation."""
    
    validation_errors: rx.Var[list]
    
    def add_imports(self):
        """Add minimal imports for Monaco YAML language support."""
        return {
            "monaco-yaml": "configureMonacoYaml",
            "react": ["useEffect"],
            "@monaco-editor/react": "useMonaco",
        }
    
    def add_hooks(self):
        """Add minimal Monaco configuration hooks."""
        return [
            """
            const monaco = useMonaco();
            
            useEffect(() => {
                if (monaco) {
                    // Configure monaco-yaml for basic YAML language support
                    configureMonacoYaml(monaco, {
                        enableSchemaRequest: false,
                        hover: true,
                        completion: true,
                        validate: true,
                        format: true,
                    });
                    
                    // Apply validation errors from Python state
                    const editor = monaco.editor.getEditors()[0];
                    if (editor && props.validation_errors) {
                        const model = editor.getModel();
                        if (model) {
                            monaco.editor.setModelMarkers(model, "yaml", props.validation_errors);
                        }
                    }
                }
            }, [monaco, props.validation_errors]);
            """
        ]


class YamlEditorState(rx.State):
    """State management for the YAML editor with Python-based validation."""

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
    
    validation_errors: list = []

    def get_content_length(self) -> int:
        """Get the content length."""
        return len(self.yaml_content)

    def validate_yaml_syntax(self, content: str) -> list:
        """Validate YAML syntax using Python and return Monaco-compatible error markers."""
        try:
            yaml.safe_load(content)
            return []  # No errors
        except yaml.YAMLError as e:
            line = getattr(e, 'problem_mark', None)
            if line:
                return [{
                    "startLineNumber": line.line + 1,
                    "startColumn": line.column + 1,
                    "endLineNumber": line.line + 1,
                    "endColumn": line.column + 2,
                    "message": str(e),
                    "severity": 8,  # Monaco MarkerSeverity.Error
                }]
            else:
                return [{
                    "startLineNumber": 1,
                    "startColumn": 1,
                    "endLineNumber": 1,
                    "endColumn": 2,
                    "message": str(e),
                    "severity": 8,
                }]

    def update_yaml_content(self, content: str):
        """Update the YAML content and validate syntax."""
        self.yaml_content = content
        self.validation_errors = self.validate_yaml_syntax(content)

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
        self.validation_errors = []


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
                "Content length will be calculated dynamically",
                color="gray.600",
                size="2",
            ),
            width="100%",
            mb=2,
        ),
        YamlValidationMonaco.create(
            value=YamlEditorState.yaml_content,
            validation_errors=YamlEditorState.validation_errors,
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
