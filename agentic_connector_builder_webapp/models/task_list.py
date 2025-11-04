"""Task list models for tracking connector development progress."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TaskStatusEnum(StrEnum):
    """Status of a task in the task list."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"

    def as_emoji(self) -> str:
        """Return an emoji representation of the task status."""
        return {
            TaskStatusEnum.NOT_STARTED: "⚪️",
            TaskStatusEnum.IN_PROGRESS: "🔵",
            TaskStatusEnum.COMPLETED: "✅",
            TaskStatusEnum.BLOCKED: "⛔️",
        }[self]


class TaskTypeEnum(StrEnum):
    """Types of tasks in the task list."""

    CONNECTOR = "connector"
    STREAM = "stream"
    FINALIZATION = "finalization"


class Task(BaseModel):
    """Base task model with common fields."""

    task_type: str = Field(
        description="Type of task (connector, stream, or finalization)"
    )
    id: str = Field(description="Unique identifier for the task")
    task_name: str = Field(description="Short name/title of the task")
    description: str | None = Field(
        default=None,
        description="Optional longer description with additional context/instructions",
    )
    status: TaskStatusEnum = Field(
        default=TaskStatusEnum.NOT_STARTED,
        description="Current status of the task",
    )
    status_detail: str | None = Field(
        default=None,
        description="Details about the task status. Can be set when marking task as completed, blocked, or in progress to provide context.",
    )

    def __str__(self) -> str:
        """Return string representation of the task."""
        result = f"{self.status.as_emoji()} {self.task_name}"
        if self.status_detail:
            result += f": {self.status_detail}"
        elif self.description:
            result += f": {self.description}"

        return result


class ConnectorTask(Task):
    """General connector task for pre-stream work."""

    task_type: TaskTypeEnum = TaskTypeEnum.CONNECTOR


class StreamTask(Task):
    """Stream-specific task with an additional stream name field."""

    task_type: TaskTypeEnum = TaskTypeEnum.STREAM
    stream_name: str = Field(description="Name of the stream this task relates to")

    def __str__(self) -> str:
        """Return string representation with stream name."""
        return f"{self.stream_name}: {self.task_name}"


class FinalizationTask(Task):
    """Finalization task for post-stream work."""

    task_type: TaskTypeEnum = TaskTypeEnum.FINALIZATION


class TaskList(BaseModel):
    """Generic task list for tracking progress."""

    basic_connector_tasks: list[Task] = Field(
        default_factory=list,
        description="List of basic connector tasks",
    )
    stream_tasks: list[Task] = Field(
        default_factory=list,
        description="List of stream tasks",
    )
    finalization_tasks: list[Task] = Field(
        default_factory=list,
        description="List of finalization tasks",
    )

    @property
    def tasks(self) -> list[Task]:
        """Get all tasks combined from all task lists."""
        return self.basic_connector_tasks + self.stream_tasks + self.finalization_tasks

    def get_task_by_id(self, task_id: str) -> Task | None:
        """Get a task by its ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task

        raise ValueError(f"Task with ID '{task_id}' not found.")

    def append_task(self, task: Task) -> Task:
        """Add a new task to the list."""
        if isinstance(task, ConnectorTask):
            self.basic_connector_tasks.append(task)
        elif isinstance(task, StreamTask):
            self.stream_tasks.append(task)
        elif isinstance(task, FinalizationTask):
            self.finalization_tasks.append(task)
        return task

    def insert_task(self, position: int, task: Task) -> Task:
        """Insert a new task at a specific position (0-indexed) within its task type."""
        # Insert into the appropriate list based on task type
        if isinstance(task, ConnectorTask):
            position = max(0, min(position, len(self.basic_connector_tasks)))
            self.basic_connector_tasks.insert(position, task)
        elif isinstance(task, StreamTask):
            position = max(0, min(position, len(self.stream_tasks)))
            self.stream_tasks.insert(position, task)
        elif isinstance(task, FinalizationTask):
            position = max(0, min(position, len(self.finalization_tasks)))
            self.finalization_tasks.insert(position, task)
        return task

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatusEnum,
        status_detail: str | None = None,
    ) -> bool:
        """Update the status of a task. Returns True if successful."""
        task = self.get_task_by_id(task_id)
        if task:
            task.status = status
            task.status_detail = status_detail
            return True

        raise ValueError(f"Task with ID '{task_id}' not found.")

    def remove_task(self, task_id: str) -> bool:
        """Remove a task from the list. Returns True if successful."""
        task = self.get_task_by_id(task_id)
        if task:
            if isinstance(task, ConnectorTask):
                self.basic_connector_tasks.remove(task)
            elif isinstance(task, StreamTask):
                self.stream_tasks.remove(task)
            elif isinstance(task, FinalizationTask):
                self.finalization_tasks.remove(task)
            return True

        raise ValueError(f"Task with ID '{task_id}' not found.")

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of task statuses."""
        total = len(self.tasks)
        not_started = sum(
            1 for t in self.tasks if t.status == TaskStatusEnum.NOT_STARTED
        )
        in_progress = sum(
            1 for t in self.tasks if t.status == TaskStatusEnum.IN_PROGRESS
        )
        completed = sum(1 for t in self.tasks if t.status == TaskStatusEnum.COMPLETED)
        blocked = sum(1 for t in self.tasks if t.status == TaskStatusEnum.BLOCKED)

        return {
            "total": total,
            "not_started": not_started,
            "in_progress": in_progress,
            "completed": completed,
            "blocked": blocked,
        }

    @classmethod
    def new_connector_build_task_list(cls) -> "TaskList":
        """Create a new task list with default connector build tasks."""
        return cls(
            basic_connector_tasks=[
                ConnectorTask(
                    id="collect-info",
                    task_name="Collect information from user",
                    description="Gather requirements, API details, authentication info, and user expectations",
                ),
                ConnectorTask(
                    id="research-api",
                    task_name="Research and analyze source API",
                    description="Study API documentation, endpoints, rate limits, and data structures",
                ),
                ConnectorTask(
                    id="first-stream-tasks",
                    task_name="Enumerate streams and create first stream's tasks",
                    description="Identify all available streams and create detailed tasks for implementing the first stream",
                ),
            ],
            stream_tasks=[],
            finalization_tasks=[
                FinalizationTask(
                    id="readiness-pass-1",
                    task_name="Run connector readiness report",
                    description="Execute readiness check. If issues exist, go back and fix them. Otherwise, create tasks for remaining streams that were enumerated",
                ),
                FinalizationTask(
                    id="readiness-pass-2",
                    task_name="Run connector readiness report",
                    description="Execute final readiness check and create new tasks based on findings",
                ),
            ],
        )
