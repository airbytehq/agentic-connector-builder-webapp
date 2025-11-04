"""Chat agent state for managing chat messages and AI agent."""

import os
from typing import Any, cast

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
from ..models.task_list import TaskList
from .builder_state import BuilderState
from .ui_state import UIState

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
    agent_running: bool = False
    agent_paused: bool = False
    task_list: TaskList | None = None

    # These attributes are excluded from state serialization to avoid pickling errors
    # with non-serializable objects like SSLContext from the MCP server connection
    _cached_agent: Agent | None = rx.Field(default=None, is_var=False)
    _cached_api_key: str | None = rx.Field(default=None, is_var=False)
    _agent_started: bool = rx.Field(default=False, is_var=False)

    @rx.var
    def has_started(self) -> bool:
        """Check if the agent has started."""
        return self._agent_started

    @rx.var
    def connector_tasks_view(self) -> list[dict[str, Any]]:
        """Get connector tasks as JSON-serializable view data."""
        if self.task_list is None:
            return []
        try:
            result = []
            for task in self.task_list.basic_connector_tasks:
                status = task.status.value
                icon, color = {
                    "not_started": ("○", "gray.400"),
                    "in_progress": ("◐", "blue.400"),
                    "completed": ("●", "green.400"),
                    "blocked": ("⛔", "red.400"),
                }.get(status, ("?", "gray.400"))
                result.append({
                    "id": task.id,
                    "title": task.task_name,
                    "details": task.description or "",
                    "status": status,
                    "icon": icon,
                    "color": color,
                })
            return result
        except Exception:
            return []

    @rx.var
    def stream_tasks_view(self) -> list[dict[str, Any]]:
        """Get stream tasks as JSON-serializable view data, sorted by stream name."""
        if self.task_list is None:
            return []
        try:
            result = []
            for task in self.task_list.stream_tasks:
                status = task.status.value
                icon, color = {
                    "not_started": ("○", "gray.400"),
                    "in_progress": ("◐", "blue.400"),
                    "completed": ("✅", "green.400"),
                    "blocked": ("⛔", "red.400"),
                }.get(status, ("?", "gray.400"))
                result.append({
                    "id": task.id,
                    "stream_name": task.stream_name,
                    "title": task.task_name,
                    "details": task.description or "",
                    "status": status,
                    "icon": icon,
                    "color": color,
                })
            result.sort(key=lambda r: (r["stream_name"], r["title"]))
            return result
        except Exception:
            return []

    @rx.var
    def finalization_tasks_view(self) -> list[dict[str, Any]]:
        """Get finalization tasks as JSON-serializable view data."""
        if self.task_list is None:
            return []
        try:
            result = []
            for task in self.task_list.finalization_tasks:
                status = task.status.value
                icon, color = {
                    "not_started": ("○", "gray.400"),
                    "in_progress": ("◐", "blue.400"),
                    "completed": ("✅", "green.400"),
                    "blocked": ("⛔", "red.400"),
                }.get(status, ("?", "gray.400"))
                result.append({
                    "id": task.id,
                    "title": task.task_name,
                    "details": task.description or "",
                    "status": status,
                    "icon": icon,
                    "color": color,
                })
            return result
        except Exception:
            return []

    @rx.var
    def task_list_header(self) -> dict[str, Any]:
        """Get task list header information."""
        if self.task_list is None:
            return {
                "name": "",
                "description": "",
                "summary": {"total": 0, "completed": 0, "in_progress": 0, "blocked": 0},
            }
        try:
            return {
                "name": self.task_list.name,
                "description": self.task_list.description,
                "summary": self.task_list.get_summary(),
            }
        except Exception:
            return {
                "name": "Task List",
                "description": "Error parsing task list",
                "summary": {"total": 0, "completed": 0, "in_progress": 0, "blocked": 0},
            }

    @rx.var
    def has_connector_tasks(self) -> bool:
        """Check if there are any connector tasks."""
        return len(self.connector_tasks_view) > 0

    @rx.var
    def has_stream_tasks(self) -> bool:
        """Check if there are any stream tasks."""
        return len(self.stream_tasks_view) > 0

    @rx.var
    def has_finalization_tasks(self) -> bool:
        """Check if there are any finalization tasks."""
        return len(self.finalization_tasks_view) > 0

    @rx.var
    def task_list_name(self) -> str:
        """Get the task list name."""
        if self.task_list is None:
            return ""
        try:
            return self.task_list.name
        except Exception:
            return "Task List"

    @rx.var
    def task_total_count(self) -> int:
        """Get total number of tasks."""
        if self.task_list is None:
            return 0
        try:
            return self.task_list.get_summary()["total"]
        except Exception:
            return 0

    @rx.var
    def task_completed_count(self) -> int:
        """Get number of completed tasks."""
        if self.task_list is None:
            return 0
        try:
            return self.task_list.get_summary()["completed"]
        except Exception:
            return 0

    @rx.var
    def task_in_progress_count(self) -> int:
        """Get number of in-progress tasks."""
        if self.task_list is None:
            return 0
        try:
            return self.task_list.get_summary()["in_progress"]
        except Exception:
            return 0

    @rx.var
    def task_blocked_count(self) -> int:
        """Get number of blocked tasks."""
        if self.task_list is None:
            return 0
        try:
            return self.task_list.get_summary()["blocked"]
        except Exception:
            return 0

    @rx.var
    def completed_of_total_text(self) -> str:
        """Get formatted completed/total text."""
        return f"{self.task_completed_count}/{self.task_total_count} Completed"

    @rx.var
    def in_progress_text(self) -> str:
        """Get formatted in-progress text."""
        return f"{self.task_in_progress_count} In Progress"

    @rx.var
    def blocked_text(self) -> str:
        """Get formatted blocked text."""
        return f"{self.task_blocked_count} Blocked"

    def _convert_to_pydantic_history(
        self, messages: list[dict[str, str]]
    ) -> list[ModelMessage]:
        """Convert chat messages to PydanticAI message format.

        Args:
            messages: List of message dicts with 'role' and 'content' keys

        Returns:
            List of ModelMessage objects for PydanticAI
        """
        history: list[ModelRequest | ModelResponse] = []
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

    @rx.event
    async def start_demo(self):
        """Start a demo session with predefined messages."""
        self.chat_input = "I want to build a connector for the JSONPlaceholder API."

        # Kick off background task to run the agent workflow
        yield ChatAgentState.send_message

    @rx.event
    async def send_message(self):
        """Trigger the background task to send a message."""
        user_message = self.chat_input.strip() or "`Continue`"
        self.chat_input = ""
        yield
        self.chat_messages.append({"role": "user", "content": user_message})
        self.agent_running = True
        self.agent_paused = False
        self.current_streaming_message = ""

        # Kick off background task to run the agent workflow
        yield ChatAgentState.run_agent_workflow

    @rx.event
    def pause_agent(self) -> None:
        """Pause the current streaming message."""
        self.agent_paused = True

    @rx.event(background=True)
    async def run_agent_workflow(self):
        """Start the agent workflow to process the user's message."""
        async with self:
            ui_state = await self.get_state(UIState)
            builder_state = await self.get_state(BuilderState)

        session_deps = SessionDeps(
            chat_state=self,
            yaml_content=builder_state.yaml_content,
            connector_name=builder_state.connector_name,
            source_api_name=builder_state.source_api_name,
            documentation_urls=builder_state.documentation_urls,
            functional_requirements=builder_state.functional_requirements,
            test_list=builder_state.test_list,
            task_list=(
                TaskList.new_connector_build_task_list()
                if self.task_list is None
                else self.task_list
            ),
        )

        message_history: list[ModelRequest | ModelResponse] = (
            self._convert_to_pydantic_history(self.chat_messages)
        )

        # Split out the latest user message from history
        user_message = cast(ModelRequest, message_history[-1]).parts[0].content
        message_history = message_history[:-1]  # Exclude latest user message

        effective_api_key = ui_state.get_effective_api_key()
        original_api_key = os.environ.get("OPENAI_API_KEY")

        try:
            if effective_api_key:
                os.environ["OPENAI_API_KEY"] = effective_api_key

            async with self:
                await self._ensure_agent_started(effective_api_key)
            agent: Agent = cast(Agent, self._cached_agent)

            async with agent.run_stream(
                user_prompt=user_message,
                deps=session_deps,
                message_history=message_history,
            ) as response:
                async for text in response.stream_text():
                    # Update state inside context block
                    async with self:
                        if self.agent_paused:
                            self.agent_paused = True
                            break

                        self.current_streaming_message = text
                        yield

                try:
                    final_output = await response.get_output()
                    if isinstance(final_output, str):
                        self.current_streaming_message = final_output
                except Exception as e:
                    print(f"[send_message] get_output failed: {type(e).__name__}: {e}")

            async with self:
                self.chat_messages.append({
                    "role": "assistant",
                    "content": self.current_streaming_message,
                })
                self.current_streaming_message = ""

                builder_state: BuilderState = await self.get_state(BuilderState)
                if session_deps.yaml_content != builder_state.yaml_content:
                    builder_state.yaml_content = session_deps.yaml_content
                    yield

                # Update task list if changed
                if session_deps.task_list != self.task_list:
                    self.task_list = session_deps.task_list
                    yield

                if session_deps.connector_name != builder_state.connector_name:
                    builder_state.connector_name = session_deps.connector_name
                    yield

                if session_deps.source_api_name != builder_state.source_api_name:
                    builder_state.source_api_name = session_deps.source_api_name
                    yield

                if (
                    session_deps.functional_requirements
                    != builder_state.functional_requirements
                ):
                    builder_state.functional_requirements = (
                        session_deps.functional_requirements
                    )
                    yield

                if session_deps.documentation_urls != builder_state.documentation_urls:
                    builder_state.documentation_urls = session_deps.documentation_urls
                    yield

        except Exception as e:
            async with self:
                self.chat_messages.append({
                    "role": "assistant",
                    "content": f"Sorry, I encountered an error: {str(e)}",
                })
                self.current_streaming_message = ""
        finally:
            if original_api_key is not None:
                os.environ["OPENAI_API_KEY"] = original_api_key
            elif effective_api_key:
                os.environ.pop("OPENAI_API_KEY", None)
            async with self:
                self.agent_running = False

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
