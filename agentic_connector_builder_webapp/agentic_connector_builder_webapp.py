"""Main Reflex application with YAML editor using reflex-monaco."""

import reflex as rx
from reflex_monaco import monaco


def configure_monaco_yaml_head() -> rx.Component:
    """Add head scripts to configure monaco-yaml with Airbyte schema validation."""
    return rx.fragment(
        rx.script(src="https://unpkg.com/monaco-yaml@5.2.2/index.js"),
        rx.script("""
            // Configure Monaco Environment for workers
            window.MonacoEnvironment = {
                getWorker: function(workerId, label) {
                    switch (label) {
                        case 'editorWorkerService':
                            return new Worker('/monaco-editor/esm/vs/editor/editor.worker.js');
                        case 'yaml':
                            return new Worker('/monaco-yaml/yaml.worker.js');
                        default:
                            throw new Error('Unknown worker ' + label);
                    }
                }
            };
            
            // Configure monaco-yaml when available
            window.addEventListener('load', function() {
                if (typeof window.configureMonacoYaml !== 'undefined') {
                    try {
                        window.configureMonacoYaml(window.monaco, {
                            enableSchemaRequest: true,
                            validate: true,
                            hover: true,
                            completion: true,
                            schemas: [{
                                uri: 'https://raw.githubusercontent.com/airbytehq/airbyte-python-cdk/bd615ad80b4326174b34f18f3f3bbbdbedb608fb/airbyte_cdk/sources/declarative/generated/declarative_component_schema.json',
                                fileMatch: ['**/*.yaml', '**/*.yml']
                            }]
                        });
                        console.log('Monaco YAML configured with Airbyte schema validation');
                    } catch (error) {
                        console.warn('Failed to configure monaco-yaml:', error);
                    }
                }
            });
        """)
    )


class YamlEditorState(rx.State):
    """State management for the YAML editor."""
    
    yaml_content: str = """# yaml-language-server: $schema=https://raw.githubusercontent.com/airbytehq/airbyte-python-cdk/bd615ad80b4326174b34f18f3f3bbbdbedb608fb/airbyte_cdk/sources/declarative/generated/declarative_component_schema.json
# Airbyte Declarative Connector Configuration
version: "0.51.42"
type: DeclarativeSource
check:
  type: CheckStream
  stream_names:
    - users

definitions:
  base_requester:
    type: HttpRequester
    url_base: "https://api.example.com"
    
  retriever:
    type: SimpleRetriever
    requester:
      $ref: "#/definitions/base_requester"
    record_selector:
      type: RecordSelector
      extractor:
        type: DpathExtractor
        field_path: ["data"]

streams:
  - type: DeclarativeStream
    name: users
    primary_key: ["id"]
    retriever:
      $ref: "#/definitions/retriever"
      requester:
        $ref: "#/definitions/base_requester"
        path: "/users"
    schema_loader:
      type: InlineSchemaLoader
      schema:
        type: object
        properties:
          id:
            type: integer
          name:
            type: string
          email:
            type: string
            format: email
"""

    def update_yaml_content(self, content: str):
        """Update the YAML content when editor changes."""
        self.yaml_content = content

    def reset_yaml_content(self):
        """Reset YAML content to default Airbyte connector example."""
        self.yaml_content = """# yaml-language-server: $schema=https://raw.githubusercontent.com/airbytehq/airbyte-python-cdk/bd615ad80b4326174b34f18f3f3bbbdbedb608fb/airbyte_cdk/sources/declarative/generated/declarative_component_schema.json
# Airbyte Declarative Connector Configuration
version: "0.51.42"
type: DeclarativeSource
check:
  type: CheckStream
  stream_names:
    - users

definitions:
  base_requester:
    type: HttpRequester
    url_base: "https://api.example.com"
    
  retriever:
    type: SimpleRetriever
    requester:
      $ref: "#/definitions/base_requester"
    record_selector:
      type: RecordSelector
      extractor:
        type: DpathExtractor
        field_path: ["data"]

streams:
  - type: DeclarativeStream
    name: users
    primary_key: ["id"]
    retriever:
      $ref: "#/definitions/retriever"
      requester:
        $ref: "#/definitions/base_requester"
        path: "/users"
    schema_loader:
      type: InlineSchemaLoader
      schema:
        type: object
        properties:
          id:
            type: integer
          name:
            type: string
          email:
            type: string
            format: email
"""


def yaml_editor_component() -> rx.Component:
    """Create the Monaco YAML editor component with Airbyte schema validation."""
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
                # Basic editor options
                "minimap": {"enabled": False},
                "fontSize": 14,
                "lineNumbers": "on",
                "roundedSelection": False,
                "scrollBeyondLastLine": False,
                "automaticLayout": True,
                "tabSize": 2,
                "insertSpaces": True,
                "wordWrap": "on",
                
                # Enhanced schema validation and intellisense options
                "quickSuggestions": {
                    "other": True,
                    "comments": False,
                    "strings": True
                },
                "suggest": {
                    "insertMode": "replace",
                    "filterGraceful": True,
                    "showKeywords": True,
                    "showSnippets": True,
                    "showClasses": True,
                    "showFunctions": True,
                    "showConstructors": True,
                    "showFields": True,
                    "showVariables": True,
                    "showInterfaces": True,
                    "showModules": True,
                    "showProperties": True,
                    "showEvents": True,
                    "showOperators": True,
                    "showUnits": True,
                    "showValues": True,
                    "showConstants": True,
                    "showEnums": True,
                    "showEnumMembers": True,
                    "showColors": True,
                    "showFiles": True,
                    "showReferences": True,
                    "showFolders": True,
                    "showTypeParameters": True,
                    "showIssues": True,
                    "showUsers": True
                },
                
                # Hover and validation options
                "hover": {
                    "enabled": True,
                    "delay": 300,
                    "sticky": True
                },
                
                # Error and warning display
                "glyphMargin": True,
                "folding": True,
                "foldingStrategy": "indentation",
                "showFoldingControls": "always",
                
                # Language-specific options for YAML
                "bracketPairColorization": {"enabled": True},
                "guides": {
                    "bracketPairs": True,
                    "bracketPairsHorizontal": True,
                    "highlightActiveBracketPair": True,
                    "indentation": True,
                    "highlightActiveIndentation": True
                },
                
                # Validation and diagnostics
                "semanticHighlighting": {"enabled": True},
                "occurrencesHighlight": True,
                "selectionHighlight": True,
                "codeLens": True,
                "colorDecorators": True,
                
                # Performance and responsiveness
                "smoothScrolling": True,
                "cursorSmoothCaretAnimation": True,
                "renderLineHighlight": "gutter",
                "renderWhitespace": "boundary",
                
                # Accessibility and usability
                "accessibilitySupport": "auto",
                "ariaLabel": "YAML Connector Configuration Editor with Airbyte Schema Validation"
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
























