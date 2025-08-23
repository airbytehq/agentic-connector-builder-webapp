"""Main Reflex application with YAML editor using reflex-monaco."""

import reflex as rx
from reflex_monaco import monaco
from reflex_monaco.monaco import MonacoEditor


class YamlValidationMonaco(MonacoEditor):
    """Extended Monaco editor with YAML validation capabilities."""
    
    def add_imports(self):
        return {
            "js-yaml": "load as yamlLoad",
        }
    
    def add_hooks(self):
        return [
            """
            // Simple YAML syntax validation using js-yaml
            const validateYamlSyntax = (editor, monaco) => {
                const model = editor.getModel();
                if (!model) return;
                
                const content = model.getValue();
                const markers = [];
                
                try {
                    yamlLoad(content);
                    // YAML is valid, clear any existing markers
                } catch (error) {
                    // YAML syntax error detected
                    const lines = content.split('\\n');
                    let errorLine = 1;
                    
                    // Try to extract line number from error message
                    const lineMatch = error.message.match(/line (\\d+)/);
                    if (lineMatch) {
                        errorLine = parseInt(lineMatch[1]);
                    }
                    
                    // Create error marker
                    markers.push({
                        severity: monaco.MarkerSeverity.Error,
                        startLineNumber: errorLine,
                        startColumn: 1,
                        endLineNumber: errorLine,
                        endColumn: lines[errorLine - 1] ? lines[errorLine - 1].length + 1 : 1,
                        message: 'YAML syntax error: ' + error.message
                    });
                }
                
                monaco.editor.setModelMarkers(model, 'yaml-validation', markers);
            };
            
            // Set up validation on content change
            const setupYamlValidation = () => {
                const editors = monaco.editor.getEditors();
                editors.forEach(editor => {
                    const model = editor.getModel();
                    if (model && model.getLanguageId() === 'yaml') {
                        // Validate immediately
                        validateYamlSyntax(editor, monaco);
                        
                        // Validate on content change
                        model.onDidChangeContent(() => {
                            validateYamlSyntax(editor, monaco);
                        });
                    }
                });
            };
            
            // Wait for monaco to be available
            if (typeof monaco !== 'undefined') {
                setupYamlValidation();
            } else {
                const checkMonaco = setInterval(() => {
                    if (typeof monaco !== 'undefined') {
                        clearInterval(checkMonaco);
                        setupYamlValidation();
                    }
                }, 100);
                
                setTimeout(() => clearInterval(checkMonaco), 10000);
            }
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
