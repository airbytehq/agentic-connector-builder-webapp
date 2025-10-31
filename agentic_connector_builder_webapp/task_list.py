"""Task list models for tracking connector development progress."""

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Status of a task in the task list."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


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
    status: TaskStatus = Field(
        default=TaskStatus.NOT_STARTED, description="Current status of the task"
    )
    task_status_detail: str | None = Field(
        default=None,
        description="Details about the task status. Can be set when marking task as completed, blocked, or in progress to provide context.",
    )

    def model_post_init(self, __context: Any) -> None:
        """Handle backward compatibility for old field names."""
        pass

    def __str__(self) -> str:
        """Return string representation of the task."""
        return self.task_name


class ConnectorTask(Task):
    """General connector task for pre-stream work."""

    task_type: Literal["connector"] = "connector"


class StreamTask(Task):
    """Stream-specific task with an additional stream name field."""

    task_type: Literal["stream"] = "stream"
    stream_name: str = Field(description="Name of the stream this task relates to")

    def __str__(self) -> str:
        """Return string representation with stream name."""
        return f"{self.stream_name}: {self.task_name}"


class FinalizationTask(Task):
    """Finalization task for post-stream work."""

    task_type: Literal["finalization"] = "finalization"


class TaskList(BaseModel):
    """Generic task list for tracking progress."""

    name: str = Field(description="Name of the task list")
    description: str = Field(description="Description of what this task list tracks")
    tasks: list[Task | ConnectorTask | StreamTask | FinalizationTask] = Field(
        default_factory=list, description="List of tasks"
    )

    def get_task_by_id(
        self, task_id: str
    ) -> Task | ConnectorTask | StreamTask | FinalizationTask | None:
        """Get a task by its ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def add_task(
        self, task: Task | ConnectorTask | StreamTask | FinalizationTask
    ) -> Task:
        """Add a new task to the list."""
        self.tasks.append(task)
        return task

    def insert_task(
        self, position: int, task: Task | ConnectorTask | StreamTask | FinalizationTask
    ) -> Task:
        """Insert a new task at a specific position (0-indexed)."""
        position = max(0, min(position, len(self.tasks)))
        self.tasks.insert(position, task)
        return task

    def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """Update the status of a task. Returns True if successful."""
        task = self.get_task_by_id(task_id)
        if task:
            task.status = status
            return True
        return False

    def remove_task(self, task_id: str) -> bool:
        """Remove a task from the list. Returns True if successful."""
        task = self.get_task_by_id(task_id)
        if task:
            self.tasks.remove(task)
            return True
        return False

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of task statuses."""
        total = len(self.tasks)
        not_started = sum(1 for t in self.tasks if t.status == TaskStatus.NOT_STARTED)
        in_progress = sum(1 for t in self.tasks if t.status == TaskStatus.IN_PROGRESS)
        completed = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        blocked = sum(1 for t in self.tasks if t.status == TaskStatus.BLOCKED)

        return {
            "total": total,
            "not_started": not_started,
            "in_progress": in_progress,
            "completed": completed,
            "blocked": blocked,
        }


def create_default_connector_task_list() -> TaskList:
    """Create the default BuildNewConnector task list.

    This workflow guides the user through the essential steps of building a new connector.
    """
    task_list = TaskList(
        name="Build New Connector",
        description="Workflow for building and testing a new connector from scratch",
    )

    connector_tasks = [
        (
            "collect-info",
            "Collect information from user",
            "Gather requirements, API details, authentication info, and user expectations",
        ),
        (
            "research-api",
            "Research and analyze source API",
            "Study API documentation, endpoints, rate limits, and data structures",
        ),
        (
            "first-stream-tasks",
            "Enumerate streams and create first stream's tasks",
            "Identify all available streams and create detailed tasks for implementing the first stream",
        ),
    ]

    for task_id, task_name, description in connector_tasks:
        task = ConnectorTask(id=task_id, task_name=task_name, description=description)
        task_list.add_task(task)

    finalization_tasks = [
        (
            "readiness-pass-1",
            "Run connector readiness report",
            "Execute readiness check. If issues exist, go back and fix them. Otherwise, create tasks for remaining streams that were enumerated",
        ),
        (
            "readiness-pass-2",
            "Run connector readiness report",
            "Execute final readiness check and create new tasks based on findings",
        ),
    ]

    for task_id, task_name, description in finalization_tasks:
        task = FinalizationTask(
            id=task_id, task_name=task_name, description=description
        )
        task_list.add_task(task)

    return task_list
