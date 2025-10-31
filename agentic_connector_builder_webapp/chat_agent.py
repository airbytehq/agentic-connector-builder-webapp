"""Simple PydanticAI chat agent for connector building assistance."""

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Any
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen

from pydantic import Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import CallToolFunc, MCPServerStdio, ToolResult
from pydantic_ai.tools import ToolDefinition


class FormField(str, Enum):
    """Enum representing editable form fields in the requirements form."""

    source_api_name = "source_api_name"
    connector_name = "connector_name"
    documentation_urls = "documentation_urls"
    functional_requirements = "functional_requirements"
    test_list = "test_list"


FORM_FIELD_DESC = "The form field to update. One of: " + ", ".join(
    f.value for f in FormField
)

MANIFEST_TOOLS = {
    "execute_stream_test_read",
    "validate_manifest",
    "execute_record_counts_smoke_test",
    "execute_dynamic_manifest_resolution_test",
}


async def prepare_mcp_tools(
    ctx: RunContext["SessionDeps"],
    tool_defs: list[ToolDefinition],
) -> list[ToolDefinition]:
    """Modify MCP tool schemas to make manifest optional.

    This allows the LLM to call manifest-requiring tools without providing
    the manifest parameter, which will be auto-injected during execution.
    """
    modified_tools = []

    for tool_def in tool_defs:
        if tool_def.name in MANIFEST_TOOLS:
            schema = tool_def.parameters_json_schema.copy()

            if "required" in schema and "manifest" in schema["required"]:
                required = [r for r in schema["required"] if r != "manifest"]
                schema["required"] = required

            if "properties" in schema and "manifest" in schema["properties"]:
                schema["properties"] = {**schema["properties"]}
                schema["properties"]["manifest"] = {
                    **schema["properties"]["manifest"],
                    "description": (
                        "Auto-provided from current YAML editor content. "
                        "You do not need to provide this parameter."
                    ),
                }

            modified_tools.append(
                ToolDefinition(
                    name=tool_def.name,
                    description=tool_def.description,
                    parameters_json_schema=schema,
                    metadata=tool_def.metadata,
                )
            )
        else:
            modified_tools.append(tool_def)

    return modified_tools


async def process_tool_call(
    ctx: RunContext["SessionDeps"],
    call_tool: CallToolFunc,
    name: str,
    tool_args: dict[str, Any],
) -> ToolResult:
    """Inject yaml_content from deps into MCP tool calls that need manifest."""
    if name in MANIFEST_TOOLS and ctx.deps:
        if not tool_args.get("manifest"):
            tool_args = {**tool_args, "manifest": ctx.deps.yaml_content}

    return await call_tool(name, tool_args)


@dataclass
class SessionDeps:
    """Dependencies containing the current webapp session state."""

    yaml_content: str
    connector_name: str
    source_api_name: str
    documentation_urls: str
    functional_requirements: str
    test_list: str
    set_source_api_name: Callable[[str], Any] | None = None
    set_connector_name: Callable[[str], Any] | None = None
    set_documentation_urls: Callable[[str], Any] | None = None
    set_functional_requirements: Callable[[str], Any] | None = None
    set_test_list: Callable[[str], Any] | None = None


mcp_server = MCPServerStdio(
    "uvx",
    args=[
        "airbyte-connector-builder-mcp",
    ],
    timeout=60 * 3,
    process_tool_call=process_tool_call,
)

prepared_mcp_server = mcp_server.prepared(prepare_mcp_tools)

SYSTEM_PROMPT = (
    "You are a helpful assistant for the Agentic Connector Builder. "
    "You help users build data connectors by answering questions about "
    "YAML configuration, connector requirements, data transformations, "
    "and best practices. You have access to tools for validating manifests, "
    "testing streams, generating scaffolds, and more. You can also access "
    "the current state of the user's work including their YAML configuration "
    "and connector metadata. Be concise and helpful.\n\n"
    "WORKFLOW FOR NEW CONNECTORS:\n"
    "When a user tells you what API they want to build a connector for, you MUST complete ALL of these steps in your FIRST response:\n"
    "1. Use set_api_name to set the API name (e.g., 'JSONPlaceholder API')\n"
    "2. Use set_connector_name to set the connector name (e.g., 'source-jsonplaceholder')\n"
    "3. Use search_documentation_urls to find documentation URLs for the API\n"
    "4. Use update_form_field to populate the documentation_urls field with the found URLs\n"
    "CRITICAL: Execute ALL FOUR steps above automatically. Do NOT ask the user if they want documentation URLs - just search for and populate them automatically.\n"
    "After completing all four steps, you can ask what the user wants to do next.\n"
    "Use get_form_fields anytime you need to check the current state of the form.\n\n"
    "FORM FIELD TOOLS:\n"
    "- get_form_fields: Check current values of all form fields\n"
    "- update_form_field: Update any form field using FormField enum (source_api_name, connector_name, documentation_urls, functional_requirements, test_list)\n"
    "- set_api_name: Specific tool for setting the API name\n"
    "- set_connector_name: Specific tool for setting the connector name\n"
    "- search_documentation_urls: Search the web for API documentation URLs\n\n"
    "IMPORTANT: You MUST emit status messages when using tools. These messages help users "
    "understand what you're doing:\n\n"
    "1. Acknowledge the user's request before you start.\n"
    "2. BEFORE calling any tool, emit: '🛠️ Now running [tool name] to [purpose]...'\n"
    "   Example: '🛠️ Now running Validate Connector Manifest to check your configuration...'\n\n"
    "3. AFTER successful tool execution, emit: '✅ Tool completed, [summary]...'\n"
    "   Example: '✅ Tool completed, successfully retrieved development checklist with 15 items.'\n\n"
    "4. AFTER failed tool execution, emit: '❌ Tool failed, [summary]...'\n"
    "   Example: '❌ Tool failed, manifest validation errors: missing required fields.'\n\n"
    "5. When planning next actions, emit: '⚙️ Next, I'll [what you plan to do]...'\n"
    "   Example: '⚙️ Next, I'll validate the updated manifest to ensure all fields are correct.'\n\n"
    "Always include these status messages in your responses - they are required for all tool interactions."
    "\n\n"
    "IMPORTANT: When using tools like validate_manifest, execute_stream_test_read, "
    "execute_record_counts_smoke_test, and execute_dynamic_manifest_resolution_test, "
    "you do NOT need to provide the 'manifest' parameter - it will be automatically "
    "provided from the current YAML editor content. Just provide the other required "
    "parameters like config, stream_name, etc."
    "\n\n"
    "Be concise and helpful."
)


def create_chat_agent() -> Agent:
    """Create a new chat agent instance.

    This function creates a fresh agent instance, which will use the
    OPENAI_API_KEY environment variable at the time of creation.

    Returns:
        A new Agent instance configured for connector building assistance.
    """
    agent = Agent(
        "openai:gpt-4o-mini",
        deps_type=SessionDeps,
        system_prompt=SYSTEM_PROMPT,
        toolsets=[prepared_mcp_server],
    )

    @agent.tool
    def get_current_yaml_content(ctx: RunContext[SessionDeps]) -> str:
        """Get the current YAML configuration content from the editor.

        Use this tool when the user asks about their current YAML configuration,
        what's in their YAML, or to analyze/validate their current work.
        """
        return ctx.deps.yaml_content

    @agent.tool
    def get_connector_metadata(ctx: RunContext[SessionDeps]) -> str:
        """Get the connector metadata including name, source API, requirements, etc.

        Use this tool when the user asks about their connector's configuration,
        requirements, documentation URLs, or test specifications.
        """
        metadata_parts = []
        if ctx.deps.connector_name:
            metadata_parts.append(f"Connector Name: {ctx.deps.connector_name}")
        if ctx.deps.source_api_name:
            metadata_parts.append(f"Source API: {ctx.deps.source_api_name}")
        if ctx.deps.documentation_urls:
            metadata_parts.append(f"Documentation URLs: {ctx.deps.documentation_urls}")
        if ctx.deps.functional_requirements:
            metadata_parts.append(
                f"Functional Requirements: {ctx.deps.functional_requirements}"
            )
        if ctx.deps.test_list:
            metadata_parts.append(f"Test List: {ctx.deps.test_list}")

        return (
            "\n".join(metadata_parts)
            or "No connector metadata has been configured yet."
        )

    @agent.tool
    def get_manifest_text(
        ctx: RunContext[SessionDeps],
        with_line_numbers: Annotated[
            bool, Field(description="Whether to include line numbers in the output")
        ] = False,
        start_line: Annotated[
            int | None,
            Field(description="Optional starting line number (1-indexed, inclusive)"),
        ] = None,
        end_line: Annotated[
            int | None,
            Field(description="Optional ending line number (1-indexed, inclusive)"),
        ] = None,
    ) -> str:
        """Get the raw text content of the current manifest YAML with optional line numbers and range constraints.

        Use this tool to read the current manifest YAML content from the session. You can optionally:
        - Include line numbers in the output for reference
        - Specify a line range to view only part of the content

        This is a read-only operation that does not modify the manifest.

        Args:
            ctx: Runtime context with session dependencies
            with_line_numbers: If True, prepend each line with its line number
            start_line: If provided, only return lines starting from this line (1-indexed)
            end_line: If provided, only return lines up to and including this line (1-indexed)

        Returns:
            The manifest YAML content as a string, optionally with line numbers.
            On error, returns a string starting with "Error:" describing the issue.
        """
        try:
            if not ctx.deps.yaml_content:
                return "Error: No YAML content available in session"

            lines = ctx.deps.yaml_content.splitlines()

            if start_line is not None:
                if start_line < 1 or start_line > len(lines):
                    return f"Error: start_line {start_line} is out of range (content has {len(lines)} lines)"
                lines = lines[start_line - 1 :]

            if end_line is not None:
                effective_start = start_line if start_line is not None else 1
                total_lines = len(ctx.deps.yaml_content.splitlines())
                if end_line < effective_start:
                    return f"Error: end_line {end_line} is before start_line {effective_start}"
                if end_line > len(lines) + (start_line - 1 if start_line else 0):
                    return f"Error: end_line {end_line} is out of range (content has {total_lines} lines)"
                lines_to_keep = end_line - effective_start + 1
                lines = lines[:lines_to_keep]

            if with_line_numbers:
                start_num = start_line if start_line is not None else 1
                numbered_lines = [
                    f"{i + start_num:4d} | {line}" for i, line in enumerate(lines)
                ]
                return "\n".join(numbered_lines)

            return "\n".join(lines)

        except Exception as e:
            return f"Error reading manifest content: {str(e)}"

    @agent.tool
    def insert_manifest_lines(
        ctx: RunContext[SessionDeps],
        line_number: Annotated[
            int,
            Field(
                description="Line number where to insert content (1-indexed). Content is inserted BEFORE this line."
            ),
        ],
        lines: Annotated[
            str, Field(description="Content to insert. Can be multi-line.")
        ],
    ) -> str:
        """Insert new lines into the current manifest YAML at a specific position.

        Use this tool to add content to the manifest YAML. The content will be
        inserted BEFORE the specified line number. For example, to insert at line 5,
        the new content will appear at line 5, and the old line 5 will become line 6+.

        To append to the end, use a line_number greater than the content length.

        This operation modifies the session state and triggers a UI update.

        Args:
            ctx: Runtime context with session dependencies
            line_number: Where to insert (1-indexed). Content inserted before this line.
            lines: The content to insert (can contain multiple lines)

        Returns:
            A confirmation message indicating success.
            On error, returns a string starting with "Error:" describing the issue.
        """
        try:
            if not ctx.deps.yaml_content:
                return "Error: No YAML content available in session"

            file_lines = ctx.deps.yaml_content.splitlines(keepends=False)

            if line_number < 1:
                return f"Error: line_number must be >= 1, got {line_number}"

            new_lines = lines.splitlines(keepends=False)
            num_new_lines = len(new_lines)

            insert_pos = min(line_number - 1, len(file_lines))
            result_lines = file_lines[:insert_pos] + new_lines + file_lines[insert_pos:]

            ctx.deps.yaml_content = "\n".join(result_lines)

            return f"Successfully inserted {num_new_lines} line(s) at line {line_number}. The manifest has been updated and changes are visible in the UI."

        except Exception as e:
            return f"Error inserting lines into manifest: {str(e)}"

    @agent.tool
    def replace_manifest_lines(
        ctx: RunContext[SessionDeps],
        start_line: Annotated[
            int, Field(description="First line to replace (1-indexed, inclusive)")
        ],
        end_line: Annotated[
            int, Field(description="Last line to replace (1-indexed, inclusive)")
        ],
        new_lines: Annotated[
            str, Field(description="Replacement content. Can be multi-line.")
        ],
    ) -> str:
        """Replace a range of lines in the current manifest YAML with new content.

        Use this tool to replace existing lines in the manifest YAML. Both start_line
        and end_line are inclusive. For example, replacing lines 5-7 will replace
        lines 5, 6, and 7 with the new content.

        This operation modifies the session state and triggers a UI update.

        Args:
            ctx: Runtime context with session dependencies
            start_line: First line to replace (1-indexed, inclusive)
            end_line: Last line to replace (1-indexed, inclusive)
            new_lines: The replacement content (can contain multiple lines)

        Returns:
            A confirmation message indicating success.
            On error, returns a string starting with "Error:" describing the issue.
        """
        try:
            if not ctx.deps.yaml_content:
                return "Error: No YAML content available in session"

            file_lines = ctx.deps.yaml_content.splitlines(keepends=False)

            if start_line < 1 or start_line > len(file_lines):
                return f"Error: start_line {start_line} is out of range (content has {len(file_lines)} lines)"
            if end_line < start_line:
                return f"Error: end_line {end_line} is before start_line {start_line}"
            if end_line > len(file_lines):
                return f"Error: end_line {end_line} is out of range (content has {len(file_lines)} lines)"

            replacement_lines = new_lines.splitlines(keepends=False)
            num_replacement_lines = len(replacement_lines)
            num_replaced = end_line - start_line + 1

            result_lines = (
                file_lines[: start_line - 1] + replacement_lines + file_lines[end_line:]
            )

            ctx.deps.yaml_content = "\n".join(result_lines)

            return f"Successfully replaced {num_replaced} line(s) (lines {start_line}-{end_line}) with {num_replacement_lines} new line(s). The manifest has been updated and changes are visible in the UI."

        except Exception as e:
            return f"Error replacing lines in manifest: {str(e)}"

    @agent.tool
    def set_api_name(
        ctx: RunContext[SessionDeps],
        api_name: Annotated[
            str, Field(description="The name of the API (e.g., 'JSONPlaceholder API')")
        ],
    ) -> str:
        """Set the Source API Name in the requirements form.

        Use this tool when the user tells you what API they want to build a connector for.
        This will populate the 'Source API name' field in the Define Requirements tab.

        Args:
            ctx: Runtime context with session dependencies
            api_name: The name of the API

        Returns:
            A confirmation message indicating success.
        """
        try:
            if ctx.deps.set_source_api_name:
                ctx.deps.set_source_api_name(api_name)
                return f"Successfully set the Source API Name to '{api_name}' in the requirements form."
            else:
                return (
                    "Error: Unable to update Source API Name (callback not available)"
                )
        except Exception as e:
            return f"Error setting API name: {str(e)}"

    @agent.tool
    def set_connector_name(
        ctx: RunContext[SessionDeps],
        connector_name: Annotated[
            str,
            Field(
                description="The connector name in the format 'source-{name}' (e.g., 'source-jsonplaceholder')"
            ),
        ],
    ) -> str:
        """Set the Connector Name in the requirements form.

        Use this tool to populate the 'Connector name' field in the Define Requirements tab.
        The connector name should follow the format 'source-{name}' where {name} is derived
        from the API name (e.g., 'JSONPlaceholder API' -> 'source-jsonplaceholder').

        Args:
            ctx: Runtime context with session dependencies
            connector_name: The connector name in source-{name} format

        Returns:
            A confirmation message indicating success.
        """
        try:
            if ctx.deps.set_connector_name:
                ctx.deps.set_connector_name(connector_name)
                return f"Successfully set the Connector Name to '{connector_name}' in the requirements form."
            else:
                return "Error: Unable to update Connector Name (callback not available)"
        except Exception as e:
            return f"Error setting connector name: {str(e)}"

    @agent.tool
    def get_form_fields(ctx: RunContext[SessionDeps]) -> str:
        """Get the current values of all form fields in the requirements form.

        Use this tool to check what values are currently set in the form fields.
        This is useful when you need to know the current state before making updates.

        Args:
            ctx: Runtime context with session dependencies

        Returns:
            A JSON string containing all current form field values.
        """
        form_data = {
            FormField.source_api_name.value: ctx.deps.source_api_name,
            FormField.connector_name.value: ctx.deps.connector_name,
            FormField.documentation_urls.value: ctx.deps.documentation_urls,
            FormField.functional_requirements.value: ctx.deps.functional_requirements,
            FormField.test_list.value: ctx.deps.test_list,
        }
        return json.dumps(form_data, indent=2)

    @agent.tool
    def update_form_field(
        ctx: RunContext[SessionDeps],
        field_name: Annotated[FormField, Field(description=FORM_FIELD_DESC)],
        value: Annotated[str, Field(description="The new value for the field")],
    ) -> str:
        """Update a single form field in the requirements form.

        This is a generic tool that can update any of the whitelisted form fields.
        Use this when you need to update form fields dynamically.

        Args:
            ctx: Runtime context with session dependencies
            field_name: The form field to update
            value: The new value for the field

        Returns:
            A confirmation message indicating success or an error message.
        """
        field_setters: dict[FormField, Callable[[str], Any] | None] = {
            FormField.source_api_name: ctx.deps.set_source_api_name,
            FormField.connector_name: ctx.deps.set_connector_name,
            FormField.documentation_urls: ctx.deps.set_documentation_urls,
            FormField.functional_requirements: ctx.deps.set_functional_requirements,
            FormField.test_list: ctx.deps.set_test_list,
        }

        setter = field_setters.get(field_name)
        if not setter:
            return f"Error: Setter for '{field_name.value}' is not available"

        try:
            setter(value)
            return (
                f"Successfully updated '{field_name.value}' in the requirements form."
            )
        except Exception as e:
            return f"Error updating '{field_name.value}': {str(e)}"

    @agent.tool
    def search_documentation_urls(
        ctx: RunContext[SessionDeps],
        api_name: Annotated[
            str, Field(description="The name of the API to search documentation for")
        ],
    ) -> str:
        """Search for documentation URLs for a given API.

        This tool searches the web for official documentation URLs for the specified API.
        It returns a newline-delimited list of relevant documentation URLs that can be
        used to populate the documentation_urls field.

        Args:
            ctx: Runtime context with session dependencies
            api_name: The name of the API (e.g., "JSONPlaceholder API", "GitHub API")

        Returns:
            A newline-delimited string of documentation URLs, or an error message.
        """
        try:
            search_query = f"{api_name} API documentation"
            encoded_query = quote_plus(search_query)
            search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

            req = Request(
                search_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
            )

            with urlopen(req, timeout=10) as response:
                html_content = response.read().decode("utf-8", errors="ignore")

            url_pattern = re.compile(
                r'<a[^>]+class="result__url"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
            )
            matches = url_pattern.findall(html_content)

            doc_keywords = [
                "docs",
                "documentation",
                "developer",
                "api",
                "reference",
                "guide",
            ]
            found_urls = []
            seen_domains = set()

            for url, text in matches[:20]:
                try:
                    parsed = urlparse(url)
                    domain = parsed.netloc.lower()

                    if domain in seen_domains:
                        continue

                    url_lower = url.lower()
                    text_lower = text.lower()

                    if any(
                        keyword in url_lower or keyword in text_lower
                        for keyword in doc_keywords
                    ):
                        found_urls.append(url)
                        seen_domains.add(domain)

                    if len(found_urls) >= 5:
                        break
                except Exception:
                    continue

            if found_urls:
                return "\n".join(found_urls)
            else:
                return f"No documentation URLs found for '{api_name}'. You may need to search manually or ask the user for documentation links."

        except Exception as e:
            return f"Error searching for documentation URLs: {str(e)}. You may need to ask the user to provide documentation links manually."

    return agent
