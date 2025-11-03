"""Chat agent state for managing chat messages and AI agent."""

import os
from typing import cast

import reflex as rx
from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

from ..chat_agent import SessionDeps, create_chat_agent

# HISTORY_MAX_MESSAGES = 20  # Maximum number of messages to include in conversation history


class ChatAgentState(rx.State):
    """State for chat messages and AI agent management."""

    chat_messages: list[dict[str, str]] = [
        {
            "role": "assistant",
            "content": "Welcome! 👋\n\nWhat connector do you want to build today?",
        }
    ]
    chat_input: str = ""
    current_streaming_message: str = ""
    chat_loading: bool = False

    # These attributes are excluded from state serialization to avoid pickling errors
    # with non-serializable objects like SSLContext from the MCP server connection
    _cached_agent: Agent | None = rx.Field(default=None, is_var=False)
    _cached_api_key: str | None = rx.Field(default=None, is_var=False)
    _agent_started: bool = rx.Field(default=False, is_var=False)

    def set_chat_input(self, value: str):
        """Set the chat input value."""
        self.chat_input = value

    def _convert_to_pydantic_history(
        self, messages: list[dict[str, str]]
    ) -> list[ModelMessage]:
        """Convert chat messages to PydanticAI message format.

        Args:
            messages: List of message dicts with 'role' and 'content' keys

        Returns:
            List of ModelMessage objects for PydanticAI
        """
        history = []
        for msg in messages:
            try:
                role = msg.get("role", "")
                content = msg.get("content", "")

                if role == "user":
                    history.append(
                        ModelRequest(parts=[UserPromptPart(content=content)])
                    )
                elif role == "assistant":
                    history.append(ModelResponse(parts=[TextPart(content=content)]))
            except Exception as e:
                print(f"Warning: Failed to convert message to PydanticAI format: {e}")
                continue

        return history

    async def _ensure_agent_started(self, effective_api_key: str):
        """Ensure the agent context is started and MCP server is running.

        This keeps the MCP server process alive for the duration of the session
        instead of starting/stopping it on each message.
        """
        if self._cached_agent is not None and self._cached_api_key != effective_api_key:
            try:
                await self._cached_agent.__aexit__(None, None, None)
            except Exception as e:
                print(
                    f"[_ensure_agent_started] Error during agent cleanup when API key changed: {e}"
                )
            self._cached_agent = None
            self._agent_started = False

        if self._cached_agent is None:
            self._cached_agent = create_chat_agent()
            self._cached_api_key = effective_api_key
            self._agent_started = False

        if not self._agent_started:
            try:
                await self._cached_agent.__aenter__()
                self._agent_started = True
            except Exception as e:
                print(
                    f"[_ensure_agent_started] Error starting agent context for MCP server: {e}"
                )
                self._cached_agent = None
                self._agent_started = False
                raise

    def send_message(self):
        """Trigger the background task to send a message."""
        if not self.chat_input.strip():
            return

        # Import here to avoid circular dependency
        from .builder_state import BuilderState
        from .progress_state import ProgressState
        from .ui_state import UIState

        # Get other states
        ui_state = await self.get_state(UIState)
        builder_state = await self.get_state(BuilderState)
        progress_state = await self.get_state(ProgressState)

        user_message = self.chat_input.strip()
        self.chat_messages.append({"role": "user", "content": user_message})
        self.chat_input = ""
        self.chat_loading = True
        self.current_streaming_message = ""
        yield

        progress_state.get_task_list()

        session_deps = SessionDeps(
            yaml_content=builder_state.yaml_content,
            connector_name=builder_state.connector_name,
            source_api_name=builder_state.source_api_name,
            documentation_urls=builder_state.documentation_urls,
            functional_requirements=builder_state.functional_requirements,
            test_list=builder_state.test_list,
            task_list_json=progress_state.task_list_json,
            set_source_api_name=builder_state.set_source_api_name,
            set_connector_name=builder_state.set_connector_name,
            set_documentation_urls=builder_state.set_documentation_urls,
            set_functional_requirements=builder_state.set_functional_requirements,
            set_test_list=builder_state.set_test_list,
        )

        recent_messages = self.chat_messages[:-1]  # Remove the current user message
        message_history = self._convert_to_pydantic_history(recent_messages)

        effective_api_key = ui_state.get_effective_api_key()
        original_api_key = os.environ.get("OPENAI_API_KEY")

        try:
            if effective_api_key:
                os.environ["OPENAI_API_KEY"] = effective_api_key

            await self._ensure_agent_started(effective_api_key)
            agent: Agent = cast(Agent, self._cached_agent)

            async with agent.run_stream(
                user_prompt=user_message,
                deps=session_deps,
                message_history=message_history,
            ) as response:
                async for text in response.stream_text():
                    # Update state inside context block
                    self.current_streaming_message = text
                    yield

                try:
                    final_output = await response.get_output()
                    if isinstance(final_output, str):
                        self.current_streaming_message = final_output
                except Exception as e:
                    print(f"[send_message] get_output failed: {type(e).__name__}: {e}")

            self.chat_messages.append(
                {"role": "assistant", "content": self.current_streaming_message}
            )
            self.current_streaming_message = ""

            builder_state = await self.get_state(BuilderState)
            if session_deps.yaml_content != builder_state.yaml_content:
                builder_state.yaml_content = session_deps.yaml_content
                yield

            # Update progress state if changed
            progress_state = await self.get_state(ProgressState)
            if session_deps.task_list_json != progress_state.task_list_json:
                progress_state.task_list_json = session_deps.task_list_json
                yield

        except Exception as e:
            self.chat_messages.append(
                {
                    "role": "assistant",
                    "content": f"Sorry, I encountered an error: {str(e)}",
                }
            )
            self.current_streaming_message = ""
        finally:
            if original_api_key is not None:
                os.environ["OPENAI_API_KEY"] = original_api_key
            elif effective_api_key:
                os.environ.pop("OPENAI_API_KEY", None)
            self.chat_loading = False

    def __getstate__(self):
        """Override to exclude backend vars from serialization.

        This prevents the SSLContext and other non-serializable objects
        in the cached agent from being pickled.
        """
        state = super().__getstate__()
        # Remove backend vars (agent cache, etc.) from serialization
        # Check both class-level and instance-level backend vars
        backend_var_names = set(self.backend_vars.keys())
        if hasattr(self, "_backend_vars"):
            backend_var_names.update(self._backend_vars.keys())

        for backend_var_name in backend_var_names:
            state.pop(backend_var_name, None)

        # Also explicitly remove the agent-related attributes
        state.pop("_cached_agent", None)
        state.pop("_cached_api_key", None)
        state.pop("_agent_started", None)
        state.pop("_backend_vars", None)

        return state

    def __setstate__(self, state):
        """Override to reinitialize backend vars after deserialization."""
        super().__setstate__(state)
        # Reinitialize the agent cache attributes
        self._cached_agent = None
        self._cached_api_key = None
        self._agent_started = False
