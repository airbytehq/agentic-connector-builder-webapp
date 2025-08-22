"""Main Reflex application with YAML editor using reflex-monaco."""

import reflex as rx
import yaml
from reflex_monaco import monaco
from reflex_monaco.monaco import MonacoEditor


class YamlValidationMonaco(MonacoEditor):
    """Monaco Editor with YAML syntax validation using monaco-yaml."""
    
    def add_imports(self):
        """Add required imports for YAML validation."""
        return {
            "monaco-yaml": "configureMonacoYaml",
            "js-yaml": "load",
            "react": ["useEffect", "useCallback"],
            "@monaco-editor/react": "useMonaco",
        }
    
    def add_hooks(self):
        """Add YAML validation hooks following airbyte-platform pattern."""
        return [
            """
            const monaco = useMonaco();
            
            useEffect(() => {
                if (monaco) {
                    // Configure monaco-yaml for YAML validation
                    configureMonacoYaml(monaco, {
                        enableSchemaRequest: false,
                        hover: true,
                        completion: true,
                        validate: true,
                        format: true,
                    });
                }
            }, [monaco]);
            """,
            """
            const validateYamlSyntax = useCallback((editor, yamlValue) => {
                if (!monaco || !editor || !yamlValue) return;
                
                const model = editor.getModel();
                if (!model) return;
                
                const errOwner = "yaml";
                
                try {
                    load(yamlValue);
                    // Clear error markers on valid YAML
                    monaco.editor.setModelMarkers(model, errOwner, []);
                } catch (err) {
                    // Set error markers for invalid YAML
                    const mark = err.mark;
                    if (mark) {
                        monaco.editor.setModelMarkers(model, errOwner, [{
                            startLineNumber: mark.line + 1,
                            startColumn: mark.column + 1,
                            endLineNumber: mark.line + 1,
                            endColumn: mark.column + 2,
                            message: err.message,
                            severity: monaco.MarkerSeverity.Error,
                        }]);
                    }
                }
            }, [monaco]);
            
            // Trigger validation when editor content changes
            useEffect(() => {
                if (monaco && validateYamlSyntax) {
                    const editor = monaco.editor.getEditors()[0];
                    if (editor) {
                        const model = editor.getModel();
                        if (model) {
                            validateYamlSyntax(editor, model.getValue());
                            
                            // Listen for content changes
                            const disposable = model.onDidChangeContent(() => {
                                validateYamlSyntax(editor, model.getValue());
                            });
                            
                            return () => disposable.dispose();
                        }
                    }
                }
            }, [monaco, validateYamlSyntax]);
            """
        ]


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

    def get_content_length(self) -> int:
        """Get the content length."""
        return len(self.yaml_content)

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
                "Content length will be calculated dynamically",
                color="gray.600",
                size="2",
            ),
            width="100%",
            mb=2,
        ),
        YamlValidationMonaco.create(
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
