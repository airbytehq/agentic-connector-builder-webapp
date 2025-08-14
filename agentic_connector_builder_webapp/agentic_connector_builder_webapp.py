"""Main Reflex application with YAML editor using reflex-monaco."""

import reflex as rx
from reflex_monaco import monaco


class MonacoYamlSchemaComponent(rx.Component):
    """Custom component that configures Monaco YAML with Airbyte schema validation."""
    
    library = "react"
    tag = "div"
    
    def add_imports(self) -> dict[str, str]:
        """Add necessary imports for monaco-yaml integration."""
        return {
            "monaco-yaml": "{ configureMonacoYaml }",
            "monaco-editor": "* as monaco",
        }
    
    def add_hooks(self) -> list[str]:
        """Add React hooks for monaco-yaml configuration with enhanced schema validation."""
        airbyte_schema_url = "https://raw.githubusercontent.com/airbytehq/airbyte-python-cdk/bd615ad80b4326174b34f18f3f3bbbdbedb608fb/airbyte_cdk/sources/declarative/generated/declarative_component_schema.json"
        
        return [
            f"""
            useEffect(() => {{
                // Configure monaco-yaml with enhanced Airbyte schema validation
                const configureYamlSchema = async () => {{
                    try {{
                        if (typeof configureMonacoYaml !== 'undefined' && typeof monaco !== 'undefined') {{
                            // Enhanced configuration with comprehensive schema validation options
                            configureMonacoYaml(monaco, {{
                                enableSchemaRequest: true,
                                validate: true,
                                hover: true,
                                completion: true,
                                format: true,
                                isKubernetes: false,
                                // Schema configuration with CORS handling
                                schemas: [
                                    {{
                                        uri: "{airbyte_schema_url}",
                                        fileMatch: ["**/*.yaml", "**/*.yml", "inmemory://model.yaml", "file:///connector.yaml"],
                                        schema: {{
                                            $ref: "{airbyte_schema_url}"
                                        }}
                                    }}
                                ],
                                // Enhanced validation options
                                yamlVersion: "1.2",
                                customTags: [],
                                // Error handling for schema validation failures
                                onSchemaRequestError: (uri, error) => {{
                                    console.error(`Failed to fetch schema from ${{uri}}:`, error);
                                    // Provide user feedback for schema fetch failures
                                    if (error.message.includes('CORS')) {{
                                        console.warn('CORS error detected. Schema validation may be limited.');
                                    }} else if (error.message.includes('404')) {{
                                        console.warn('Schema not found. Using basic YAML validation.');
                                    }} else {{
                                        console.warn('Network error fetching schema. Check connection.');
                                    }}
                                }},
                                // Additional diagnostic options
                                diagnosticsOptions: {{
                                    enableSchemaRequest: true,
                                    hover: true,
                                    completion: true,
                                    validate: true,
                                    format: true
                                }}
                            }});
                            
                            console.log('Monaco YAML configured with enhanced Airbyte schema validation');
                            console.log('Schema URL:', "{airbyte_schema_url}");
                            
                            // Test schema availability
                            fetch("{airbyte_schema_url}", {{ method: 'HEAD' }})
                                .then(response => {{
                                    if (response.ok) {{
                                        console.log('Airbyte schema is accessible');
                                    }} else {{
                                        console.warn('Airbyte schema returned status:', response.status);
                                    }}
                                }})
                                .catch(error => {{
                                    console.warn('Schema accessibility test failed:', error.message);
                                    if (error.message.includes('CORS')) {{
                                        console.info('CORS policy may prevent direct schema access, but monaco-yaml worker should handle it');
                                    }}
                                }});
                        }} else {{
                            console.error('Monaco YAML dependencies not available');
                        }}
                    }} catch (error) {{
                        console.error('Failed to configure monaco-yaml:', error);
                        // Provide detailed error information
                        if (error.message.includes('configureMonacoYaml')) {{
                            console.error('monaco-yaml package may not be properly installed or imported');
                        }} else if (error.message.includes('monaco')) {{
                            console.error('Monaco editor may not be properly initialized');
                        }}
                    }}
                }};
                
                // Configure with multiple retry attempts and delays
                let retryCount = 0;
                const maxRetries = 5;
                const retryDelay = 200;
                
                const configureWithRetry = () => {{
                    if (retryCount < maxRetries) {{
                        configureYamlSchema().catch(() => {{
                            retryCount++;
                            console.log(`Retrying monaco-yaml configuration (attempt ${{retryCount}}/${{maxRetries}})`);
                            setTimeout(configureWithRetry, retryDelay * retryCount);
                        }});
                    }} else {{
                        console.warn('Failed to configure monaco-yaml after maximum retries');
                    }}
                }};
                
                // Initial configuration attempt
                const timer = setTimeout(configureWithRetry, 100);
                return () => clearTimeout(timer);
            }}, []);
            """
        ]
    
    def render(self) -> str:
        """Render the component."""
        return "<div style={{display: 'none'}}></div>"


# Create the schema configuration component
monaco_yaml_schema = MonacoYamlSchemaComponent.create


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
        # Add the schema configuration component (hidden but configures monaco-yaml)
        monaco_yaml_schema(),
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


















