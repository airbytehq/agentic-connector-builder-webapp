"""Simple PydanticAI chat agent for connector building assistance."""

from dataclasses import dataclass

from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerStdio


@dataclass
class SessionDeps:
    """Dependencies containing the current webapp session state."""

    yaml_content: str
    connector_name: str
    source_api_name: str
    documentation_urls: str
    functional_requirements: str
    test_list: str


mcp_server = MCPServerStdio(
    "uvx",
    args=[
        "airbyte-connector-builder-mcp",
    ],
    timeout=60 * 3,
)

chat_agent = Agent(
    "openai:gpt-4o-mini",
    deps_type=SessionDeps,
    system_prompt=(
        "You are a helpful assistant for the Agentic Connector Builder. "
        "You help users build data connectors by answering questions about "
        "YAML configuration, connector requirements, data transformations, "
        "and best practices. You have access to tools for validating manifests, "
        "testing streams, generating scaffolds, and more. You can also access "
        "the current state of the user's work including their YAML configuration "
        "and connector metadata. Be concise and helpful."
    ),
    toolsets=[mcp_server],
)


@chat_agent.tool
def get_current_yaml_content(ctx: RunContext[SessionDeps]) -> str:
    """Get the current YAML configuration content from the editor.

    Use this tool when the user asks about their current YAML configuration,
    what's in their YAML, or to analyze/validate their current work.
    """
    return ctx.deps.yaml_content


@chat_agent.tool
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
        if metadata_parts
        else "No connector metadata has been configured yet."
    )
