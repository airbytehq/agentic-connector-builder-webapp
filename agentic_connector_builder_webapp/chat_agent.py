"""Simple PydanticAI chat agent for connector building assistance."""

import json
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Any

from pydantic import Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from pydantic_ai.mcp import CallToolFunc, MCPServerStdio, ToolResult
from pydantic_ai.tools import ToolDefinition

from .task_list import (
    ConnectorTask,
    FinalizationTask,
    StreamTask,
    TaskList,
    TaskStatus,
)


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
    task_list_json: str
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
    "3. Use duckduckgo_search to search for '[API name] official documentation' or '[API name] API reference'\n"
    "4. Extract official documentation URLs from the search results (prefer docs.*, developer.*, api.* domains)\n"
    "5. Use update_form_field with FormField.documentation_urls to populate the documentation URLs (newline-delimited)\n"
    "CRITICAL: Execute ALL FIVE steps above automatically. Do NOT ask the user if they want documentation URLs - just search for and populate them automatically.\n"
    "After completing all five steps, you can ask what the user wants to do next.\n"
    "Use get_form_fields anytime you need to check the current state of the form.\n\n"
    "FORM FIELD TOOLS:\n"
    "- get_form_fields: Check current values of all form fields\n"
    "- update_form_field: Update any form field using FormField enum (source_api_name, connector_name, documentation_urls, functional_requirements, test_list)\n"
    "- set_api_name: Specific tool for setting the API name\n"
    "- set_connector_name: Specific tool for setting the connector name\n"
    "- duckduckgo_search: Search the web using DuckDuckGo. Use this to find official API documentation URLs. Prefer official docs domains (docs.*, developer.*, api.*) and extract URLs from results.\n\n"
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
    "CHECKLIST DISCIPLINE:\n"
    "You have access to a task list tracking system with three types of tasks:\n"
    "1. Connector Tasks (pre-stream work) - General connector setup and configuration\n"
    "2. Stream Tasks (stream-specific work) - Tasks for individual streams\n"
    "3. Finalization Tasks (post-stream work) - Final validation and cleanup\n\n"
    "Task Management Guidelines:\n"
    "- ALWAYS call list_tasks at the start of your work or when planning next steps to see the current task list\n"
    "- When you start working on a task, mark it as IN_PROGRESS using update_task_status\n"
    "- When you complete a task, mark it as COMPLETED with task_status_detail describing what was accomplished\n"
    "- If a task is blocked, mark it as BLOCKED with task_status_detail explaining the blocker\n"
    "- Unless the user requests otherwise, automatically proceed to the next task after completing one\n"
    "- If you encounter a blocker:\n"
    "  1. Mark the current task as BLOCKED with details about the issue\n"
    "  2. If possible, add a follow-up task to unblock it later\n"
    "  3. Report back to the user for assistance\n"
    "- Use the task tools (add_connector_task, add_stream_task, add_finalization_task, etc.) to keep the UI in sync\n"
    "- The task list is visible to the user in the Progress tab, so keep it updated as you work\n\n"
    "Available Task Tools:\n"
    "- list_tasks: View all tasks grouped by type (Connector, Stream, Finalization)\n"
    "- add_connector_task, insert_connector_task: Add general connector tasks\n"
    "- add_stream_task, insert_stream_task: Add stream-specific tasks (requires stream_name)\n"
    "- add_finalization_task, insert_finalization_task: Add post-stream finalization tasks\n"
    "- update_task_status: Update task status (not_started, in_progress, completed, blocked) with optional task_status_detail\n"
    "- remove_task: Remove tasks that are no longer needed\n\n"
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
        tools=[duckduckgo_search_tool()],
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
    def list_tasks(ctx: RunContext[SessionDeps]) -> str:
        """List all tasks in the current task list with their statuses.

        Use this tool to view the current task list, check task statuses,
        and understand what work has been completed or is in progress.

        Tasks are organized into three sections:
        1. Connector Tasks (pre-stream work)
        2. Stream Tasks (stream-specific work)
        3. Finalization Tasks (post-stream work)

        Returns:
            A formatted string showing all tasks grouped by type with their IDs, names, and statuses.
        """
        try:
            if not ctx.deps.task_list_json:
                return "No task list has been initialized yet."

            task_list = TaskList.model_validate_json(ctx.deps.task_list_json)
            summary = task_list.get_summary()

            result = [
                f"Task List: {task_list.name}",
                f"Description: {task_list.description}",
                f"\nSummary: {summary['completed']}/{summary['total']} completed, "
                f"{summary['in_progress']} in progress, {summary['blocked']} blocked\n",
            ]

            status_icon_map = {
                TaskStatus.NOT_STARTED: "○",
                TaskStatus.IN_PROGRESS: "◐",
                TaskStatus.COMPLETED: "●",
                TaskStatus.BLOCKED: "⛔",
            }

            connector_tasks = [t for t in task_list.tasks if t.task_type == "connector"]
            stream_tasks = [t for t in task_list.tasks if t.task_type == "stream"]
            finalization_tasks = [t for t in task_list.tasks if t.task_type == "finalization"]

            if connector_tasks:
                result.append("\n=== Connector Tasks (Pre-Stream) ===")
                for i, task in enumerate(connector_tasks, 1):
                    status_icon = status_icon_map.get(task.status, "?")
                    task_info = f"{i}. [{status_icon}] {task.task_name} (ID: {task.id}, Status: {task.status.value})"
                    if task.description:
                        task_info += f"\n   Description: {task.description}"
                    if task.task_status_detail:
                        task_info += f"\n   Status Detail: {task.task_status_detail}"
                    result.append(task_info)

            if stream_tasks:
                result.append("\n=== Stream Tasks ===")
                for i, task in enumerate(stream_tasks, 1):
                    status_icon = status_icon_map.get(task.status, "?")
                    task_info = f"{i}. [{status_icon}] {task.task_name} (ID: {task.id}, Status: {task.status.value})"
                    if isinstance(task, StreamTask):
                        task_info += f" [Stream: {task.stream_name}]"
                    if task.description:
                        task_info += f"\n   Description: {task.description}"
                    if task.task_status_detail:
                        task_info += f"\n   Status Detail: {task.task_status_detail}"
                    result.append(task_info)

            if finalization_tasks:
                result.append("\n=== Finalization Tasks (Post-Stream) ===")
                for i, task in enumerate(finalization_tasks, 1):
                    status_icon = status_icon_map.get(task.status, "?")
                    task_info = f"{i}. [{status_icon}] {task.task_name} (ID: {task.id}, Status: {task.status.value})"
                    if task.description:
                        task_info += f"\n   Description: {task.description}"
                    if task.task_status_detail:
                        task_info += f"\n   Status Detail: {task.task_status_detail}"
                    result.append(task_info)

            return "\n".join(result)

        except Exception as e:
            return f"Error listing tasks: {str(e)}"

    @agent.tool
    def add_connector_task(
        ctx: RunContext[SessionDeps],
        task_id: Annotated[str, Field(description="Unique identifier for the task")],
        task_name: Annotated[str, Field(description="Short name/title of the task")],
        description: Annotated[
            str | None,
            Field(description="Optional longer description with additional context"),
        ] = None,
    ) -> str:
        """Add a new connector task to the end of the task list.

        Use this tool to add a new generic connector task that doesn't relate
        to a specific stream.

        Args:
            ctx: Runtime context with session dependencies
            task_id: Unique identifier for the task
            task_name: Short name/title of the task
            description: Optional longer description with additional context

        Returns:
            A confirmation message indicating success.
        """
        try:
            if not ctx.deps.task_list_json:
                return "Error: No task list has been initialized yet."

            task_list = TaskList.model_validate_json(ctx.deps.task_list_json)
            task = ConnectorTask(
                id=task_id, task_name=task_name, description=description
            )
            task_list.add_task(task)
            ctx.deps.task_list_json = task_list.model_dump_json()

            return f"Successfully added connector task '{task_name}' (ID: {task_id}) to the task list."

        except Exception as e:
            return f"Error adding connector task: {str(e)}"

    @agent.tool
    def add_stream_task(
        ctx: RunContext[SessionDeps],
        task_id: Annotated[str, Field(description="Unique identifier for the task")],
        task_name: Annotated[str, Field(description="Short name/title of the task")],
        stream_name: Annotated[
            str, Field(description="Name of the stream this task relates to")
        ],
        description: Annotated[
            str | None,
            Field(description="Optional longer description with additional context"),
        ] = None,
    ) -> str:
        """Add a new stream-specific task to the end of the task list.

        Use this tool to add a task that relates to a specific data stream.

        Args:
            ctx: Runtime context with session dependencies
            task_id: Unique identifier for the task
            task_name: Short name/title of the task
            stream_name: Name of the stream this task relates to
            description: Optional longer description with additional context

        Returns:
            A confirmation message indicating success.
        """
        try:
            if not ctx.deps.task_list_json:
                return "Error: No task list has been initialized yet."

            task_list = TaskList.model_validate_json(ctx.deps.task_list_json)
            task = StreamTask(
                id=task_id,
                task_name=task_name,
                stream_name=stream_name,
                description=description,
            )
            task_list.add_task(task)
            ctx.deps.task_list_json = task_list.model_dump_json()

            return f"Successfully added stream task '{task_name}' (ID: {task_id}) for stream '{stream_name}' to the task list."

        except Exception as e:
            return f"Error adding stream task: {str(e)}"

    @agent.tool
    def insert_connector_task(
        ctx: RunContext[SessionDeps],
        position: Annotated[
            int, Field(description="Position to insert at (0-indexed, 0 = first)")
        ],
        task_id: Annotated[str, Field(description="Unique identifier for the task")],
        task_name: Annotated[str, Field(description="Short name/title of the task")],
        description: Annotated[
            str | None,
            Field(description="Optional longer description with additional context"),
        ] = None,
    ) -> str:
        """Insert a new connector task at a specific position in the task list.

        Use this tool to insert a generic connector task at a specific position
        rather than at the end.

        Args:
            ctx: Runtime context with session dependencies
            position: Position to insert at (0-indexed, 0 = first position)
            task_id: Unique identifier for the task
            task_name: Short name/title of the task
            description: Optional longer description with additional context

        Returns:
            A confirmation message indicating success.
        """
        try:
            if not ctx.deps.task_list_json:
                return "Error: No task list has been initialized yet."

            task_list = TaskList.model_validate_json(ctx.deps.task_list_json)
            task = ConnectorTask(
                id=task_id, task_name=task_name, description=description
            )
            task_list.insert_task(position, task)
            ctx.deps.task_list_json = task_list.model_dump_json()

            return f"Successfully inserted connector task '{task_name}' (ID: {task_id}) at position {position}."

        except Exception as e:
            return f"Error inserting connector task: {str(e)}"

    @agent.tool
    def insert_stream_task(
        ctx: RunContext[SessionDeps],
        position: Annotated[
            int, Field(description="Position to insert at (0-indexed, 0 = first)")
        ],
        task_id: Annotated[str, Field(description="Unique identifier for the task")],
        task_name: Annotated[str, Field(description="Short name/title of the task")],
        stream_name: Annotated[
            str, Field(description="Name of the stream this task relates to")
        ],
        description: Annotated[
            str | None,
            Field(description="Optional longer description with additional context"),
        ] = None,
    ) -> str:
        """Insert a new stream-specific task at a specific position in the task list.

        Use this tool to insert a stream task at a specific position rather than
        at the end.

        Args:
            ctx: Runtime context with session dependencies
            position: Position to insert at (0-indexed, 0 = first position)
            task_id: Unique identifier for the task
            task_name: Short name/title of the task
            stream_name: Name of the stream this task relates to
            description: Optional longer description with additional context

        Returns:
            A confirmation message indicating success.
        """
        try:
            if not ctx.deps.task_list_json:
                return "Error: No task list has been initialized yet."

            task_list = TaskList.model_validate_json(ctx.deps.task_list_json)
            task = StreamTask(
                id=task_id,
                task_name=task_name,
                stream_name=stream_name,
                description=description,
            )
            task_list.insert_task(position, task)
            ctx.deps.task_list_json = task_list.model_dump_json()

            return f"Successfully inserted stream task '{task_name}' (ID: {task_id}) for stream '{stream_name}' at position {position}."

        except Exception as e:
            return f"Error inserting stream task: {str(e)}"

    @agent.tool
    def add_finalization_task(
        ctx: RunContext[SessionDeps],
        task_id: Annotated[str, Field(description="Unique identifier for the task")],
        task_name: Annotated[str, Field(description="Short name/title of the task")],
        description: Annotated[
            str | None,
            Field(description="Optional longer description with additional context"),
        ] = None,
    ) -> str:
        """Add a new finalization task to the end of the task list.

        Use this tool to add a post-stream finalization task that should be
        completed after all stream tasks are done.

        Args:
            ctx: Runtime context with session dependencies
            task_id: Unique identifier for the task
            task_name: Short name/title of the task
            description: Optional longer description with additional context

        Returns:
            A confirmation message indicating success.
        """
        try:
            if not ctx.deps.task_list_json:
                return "Error: No task list has been initialized yet."

            task_list = TaskList.model_validate_json(ctx.deps.task_list_json)
            task = FinalizationTask(
                id=task_id, task_name=task_name, description=description
            )
            task_list.add_task(task)
            ctx.deps.task_list_json = task_list.model_dump_json()

            return f"Successfully added finalization task '{task_name}' (ID: {task_id}) to the task list."

        except Exception as e:
            return f"Error adding finalization task: {str(e)}"

    @agent.tool
    def insert_finalization_task(
        ctx: RunContext[SessionDeps],
        position: Annotated[
            int, Field(description="Position to insert at (0-indexed, 0 = first)")
        ],
        task_id: Annotated[str, Field(description="Unique identifier for the task")],
        task_name: Annotated[str, Field(description="Short name/title of the task")],
        description: Annotated[
            str | None,
            Field(description="Optional longer description with additional context"),
        ] = None,
    ) -> str:
        """Insert a new finalization task at a specific position in the task list.

        Use this tool to insert a finalization task at a specific position
        rather than at the end.

        Args:
            ctx: Runtime context with session dependencies
            position: Position to insert at (0-indexed, 0 = first position)
            task_id: Unique identifier for the task
            task_name: Short name/title of the task
            description: Optional longer description with additional context

        Returns:
            A confirmation message indicating success.
        """
        try:
            if not ctx.deps.task_list_json:
                return "Error: No task list has been initialized yet."

            task_list = TaskList.model_validate_json(ctx.deps.task_list_json)
            task = FinalizationTask(
                id=task_id, task_name=task_name, description=description
            )
            task_list.insert_task(position, task)
            ctx.deps.task_list_json = task_list.model_dump_json()

            return f"Successfully inserted finalization task '{task_name}' (ID: {task_id}) at position {position}."

        except Exception as e:
            return f"Error inserting finalization task: {str(e)}"

    @agent.tool
    def update_task_status(
        ctx: RunContext[SessionDeps],
        task_id: Annotated[str, Field(description="ID of the task to update")],
        status: Annotated[
            str,
            Field(
                description="New status: 'not_started', 'in_progress', 'completed', or 'blocked'"
            ),
        ],
        task_status_detail: Annotated[
            str | None,
            Field(
                description="Optional details about the status change. Provide context when marking as completed, blocked, or in progress."
            ),
        ] = None,
    ) -> str:
        """Update the status of a task in the task list.

        Use this tool to mark tasks as started, completed, or blocked as work progresses.
        Provide task_status_detail to give context about what was accomplished, what's blocking progress, etc.

        Args:
            ctx: Runtime context with session dependencies
            task_id: ID of the task to update
            status: New status (not_started, in_progress, completed, or blocked)
            task_status_detail: Optional details about the status change

        Returns:
            A confirmation message indicating success.
        """
        try:
            if not ctx.deps.task_list_json:
                return "Error: No task list has been initialized yet."

            task_list = TaskList.model_validate_json(ctx.deps.task_list_json)

            try:
                task_status = TaskStatus(status)
            except ValueError:
                return f"Error: Invalid status '{status}'. Must be one of: not_started, in_progress, completed, blocked"

            task = task_list.get_task_by_id(task_id)
            if not task:
                return f"Error: Task with ID '{task_id}' not found in task list."

            task.status = task_status
            if task_status_detail:
                task.task_status_detail = task_status_detail

            ctx.deps.task_list_json = task_list.model_dump_json()

            detail_msg = f" with detail: {task_status_detail}" if task_status_detail else ""
            return f"Successfully updated task '{task_id}' status to '{status}'{detail_msg}."

        except Exception as e:
            return f"Error updating task status: {str(e)}"

    @agent.tool
    def remove_task(
        ctx: RunContext[SessionDeps],
        task_id: Annotated[str, Field(description="ID of the task to remove")],
    ) -> str:
        """Remove a task from the task list.

        Use this tool to remove tasks that are no longer needed or were added by mistake.

        Args:
            ctx: Runtime context with session dependencies
            task_id: ID of the task to remove

        Returns:
            A confirmation message indicating success.
        """
        try:
            if not ctx.deps.task_list_json:
                return "Error: No task list has been initialized yet."

            task_list = TaskList.model_validate_json(ctx.deps.task_list_json)

            success = task_list.remove_task(task_id)
            if not success:
                return f"Error: Task with ID '{task_id}' not found in task list."

            ctx.deps.task_list_json = task_list.model_dump_json()

            return f"Successfully removed task '{task_id}' from the task list."

        except Exception as e:
            return f"Error removing task: {str(e)}"

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

    return agent
