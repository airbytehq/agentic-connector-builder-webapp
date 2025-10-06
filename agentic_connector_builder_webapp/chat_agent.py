"""Simple PydanticAI chat agent for connector building assistance."""

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

mcp_server = MCPServerStdio(
    "uvx",
    args=[
        "airbyte-connector-builder-mcp",
    ],
    timeout=60 * 3,
)

chat_agent = Agent(
    "openai:gpt-4o-mini",
    system_prompt=(
        "You are a helpful assistant for the Agentic Connector Builder. "
        "You help users build data connectors by answering questions about "
        "YAML configuration, connector requirements, data transformations, "
        "and best practices. You have access to tools for validating manifests, "
        "testing streams, generating scaffolds, and more. Be concise and helpful."
    ),
    toolsets=[mcp_server],
)
