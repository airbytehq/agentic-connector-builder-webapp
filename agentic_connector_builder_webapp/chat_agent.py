"""Simple PydanticAI chat agent for connector building assistance."""

from pydantic_ai import Agent

chat_agent = Agent(
    'openai:gpt-4o-mini',
    system_prompt=(
        "You are a helpful assistant for the Agentic Connector Builder. "
        "You help users build data connectors by answering questions about "
        "YAML configuration, connector requirements, data transformations, "
        "and best practices. Be concise and helpful."
    ),
)
