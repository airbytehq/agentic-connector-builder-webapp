"""Simple PydanticAI chat agent for connector building assistance."""

import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, Any

import reflex as rx
from pydantic import Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from pydantic_ai.mcp import CallToolFunc, MCPServerStdio, ToolResult
from pydantic_ai.tools import ToolDefinition

from ._guidance import SYSTEM_PROMPT
from .models.task_list import (
    ConnectorTask,
    FinalizationTask,
    StreamTask,
    TaskList,
    TaskStatusEnum,
    TaskTypeEnum,
)


class FormFieldEnum(StrEnum):
    """Enum representing editable form fields in the requirements form."""

    source_api_name = "source_api_name"
    connector_name = "connector_name"
    documentation_urls = "documentation_urls"
    functional_requirements = "functional_requirements"
    test_list = "test_list"


FORM_FIELD_DESC = "The form field to update. One of: " + ", ".join(
    f.value for f in FormFieldEnum
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

    chat_state: rx.State
    yaml_content: str
    connector_name: str
    source_api_name: str
    documentation_urls: str
    functional_requirements: str
    test_list: str
    task_list: TaskList


mcp_server = MCPServerStdio(
    "uvx",
    args=[
        "airbyte-connector-builder-mcp",
    ],
    timeout=60 * 3,
    process_tool_call=process_tool_call,
)

prepared_mcp_server = mcp_server.prepared(prepare_mcp_tools)


def create_chat_agent() -> Agent:
    """Create a new chat agent instance.

    This function creates a fresh agent instance, which will use the
    OPENAI_API_KEY environment variable at the time of creation.

    Returns:
        A new Agent instance configured for connector building assistance.
    """
    agent: Agent[SessionDeps, str] = Agent(
        model="openai:gpt-4o-mini",
        deps_type=SessionDeps,
        instructions=SYSTEM_PROMPT,
        # system_prompt=SYSTEM_PROMPT,  # Doesn't work. Must pass via `instructions` param
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

        Returns:
            A confirmation message indicating success.
        """
        ctx.deps.source_api_name = api_name  # Deferred state update to session deps
        return f"Successfully set the Source API Name to '{api_name}' in the requirements form."

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

        Returns:
            A confirmation message indicating success.
        """
        # Deferred state update to session deps
        ctx.deps.connector_name = connector_name

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
        return ctx.deps.task_list

    @agent.tool
    async def add_connector_task(
        ctx: RunContext[SessionDeps],
        task_type: Annotated[
            TaskTypeEnum,
            Field(
                description="Type of the task.",
            ),
        ],
        task_id: Annotated[
            str,
            Field(
                description="Unique identifier for the task",
            ),
        ],
        task_name: Annotated[
            str,
            Field(
                description="Short name/title of the task",
            ),
        ],
        description: Annotated[
            str | None,
            Field(description="Optional longer description with additional context"),
        ] = None,
        stream_name: Annotated[
            str | None,
            Field(
                description="Name of the stream this task relates to (required if task_type is 'stream')",
            ),
        ] = None,
    ) -> str:
        """Add a new connector task to the end of the task list.

        Use this tool to add a new generic connector task that doesn't relate
        to a specific stream.

        Returns:
            A confirmation message indicating success.
        """
        if not ctx.deps.task_list:
            raise ValueError("No task list has been initialized yet.")

        task_list = ctx.deps.task_list
        if task_type == TaskTypeEnum.FINALIZATION:
            task_list.append_task(
                FinalizationTask(
                    id=task_id,
                    task_name=task_name,
                    description=description,
                )
            )
        elif task_type == TaskTypeEnum.CONNECTOR:
            task_list.append_task(
                ConnectorTask(
                    id=task_id,
                    task_name=task_name,
                    description=description,
                )
            )
        elif task_type == TaskTypeEnum.STREAM:
            if not stream_name:
                raise ValueError("stream_name is required when task_type is 'stream'.")
            task_list.append_task(
                StreamTask(
                    id=task_id,
                    task_name=task_name,
                    stream_name=stream_name,
                    description=description,
                )
            )
        else:
            raise ValueError(f"Invalid task_type: {task_type}")

        async with ctx.deps.chat_state as state:
            state.task_list = task_list  # Trigger state update

        return f"Successfully added connector task '{task_name}' (ID: {task_id}) to the task list."

    @agent.tool
    async def update_task_status(
        ctx: RunContext[SessionDeps],
        task_id: Annotated[str, Field(description="ID of the task to update")],
        status: Annotated[
            str,
            Field(
                description="New status: 'not_started', 'in_progress', 'completed', or 'blocked'"
            ),
        ],
        status_detail: Annotated[
            str | None,
            Field(
                description="Optional details about the status change. Provide context when marking as completed, blocked, or in progress."
            ),
        ] = None,
    ) -> str:
        """Update the status of a task in the task list.

        Use this tool to mark tasks as started, completed, or blocked as work progresses.
        Provide status_detail to give context about what was accomplished, what's blocking progress, etc.

        Returns:
            A confirmation message indicating success.
        """
        try:
            if ctx.deps.task_list is not None:
                ctx.deps.task_list.update_task_status(
                    task_id=task_id,
                    status=TaskStatusEnum(status),
                    status_detail=status_detail,
                )
                # Trigger state update through the chat_state
                async with ctx.deps.chat_state:
                    ctx.deps.chat_state.task_list = ctx.deps.task_list
            return f"Successfully updated task '{task_id}' status to '{status}'."

        except Exception as e:
            return f"Error updating task status: {str(e)}"

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
        form_data: dict[str, str] = {
            FormFieldEnum.source_api_name.value: ctx.deps.source_api_name,
            FormFieldEnum.connector_name.value: ctx.deps.connector_name,
            FormFieldEnum.documentation_urls.value: ctx.deps.documentation_urls,
            FormFieldEnum.functional_requirements.value: ctx.deps.functional_requirements,
            FormFieldEnum.test_list.value: ctx.deps.test_list,
        }
        return json.dumps(form_data, indent=2)

    @agent.tool
    async def update_form_field(
        ctx: RunContext[SessionDeps],
        field_name: Annotated[FormFieldEnum, Field(description=FORM_FIELD_DESC)],
        value: Annotated[str, Field(description="The new value for the field")],
    ) -> str:
        """Update a single form field in the requirements form.

        This is a generic tool that can update any of the whitelisted form fields.
        Use this when you need to update form fields dynamically.

        Returns:
            A confirmation message indicating success or an error message.
        """
        match field_name:
            case FormFieldEnum.source_api_name:
                ctx.deps.source_api_name = value
            case FormFieldEnum.connector_name:
                ctx.deps.connector_name = value
            case FormFieldEnum.documentation_urls:
                ctx.deps.documentation_urls = value
            case FormFieldEnum.functional_requirements:
                ctx.deps.functional_requirements = value
            case FormFieldEnum.test_list:
                ctx.deps.test_list = value

    return agent
