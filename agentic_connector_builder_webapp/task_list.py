"""Task list models for tracking connector development progress."""

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Status of a task in the task list."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Task(BaseModel):
    """Base task model with common fields."""

    task_type: str = Field(description="Type of task (connector or stream)")
    id: str = Field(description="Unique identifier for the task")
    title: str = Field(description="Title/description of the task")
    status: TaskStatus = Field(
        default=TaskStatus.NOT_STARTED, description="Current status of the task"
    )
    details: str | None = Field(
        default=None, description="Optional additional details about the task"
    )

    def __str__(self) -> str:
        """Return string representation of the task."""
        return self.title


class ConnectorTask(Task):
    """Generic connector task with just a description."""

    task_type: Literal["connector"] = "connector"


class StreamTask(Task):
    """Stream-specific task with an additional stream name field."""

    task_type: Literal["stream"] = "stream"
    stream_name: str = Field(description="Name of the stream this task relates to")

    def __str__(self) -> str:
        """Return string representation with stream name."""
        return f"{self.stream_name}: {self.title}"


class TaskList(BaseModel):
    """Generic task list for tracking progress."""

    name: str = Field(description="Name of the task list")
    description: str = Field(description="Description of what this task list tracks")
    tasks: list[Task | ConnectorTask | StreamTask] = Field(
        default_factory=list, description="List of tasks"
    )

    def get_task_by_id(self, task_id: str) -> Task | ConnectorTask | StreamTask | None:
        """Get a task by its ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def add_task(self, task: Task | ConnectorTask | StreamTask) -> Task:
        """Add a new task to the list."""
        self.tasks.append(task)
        return task

    def insert_task(
        self, position: int, task: Task | ConnectorTask | StreamTask
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
        failed = sum(1 for t in self.tasks if t.status == TaskStatus.FAILED)

        return {
            "total": total,
            "not_started": not_started,
            "in_progress": in_progress,
            "completed": completed,
            "failed": failed,
        }


def create_default_connector_task_list() -> TaskList:
    """Create the default task list for new connector creation.

    This includes the bare minimum tasks to create and fully test a connector.
    """
    task_list = TaskList(
        name="New Connector Development",
        description="Essential tasks for creating and testing a new connector",
    )

    tasks = [
        ("define_requirements", "Define connector requirements and specifications"),
        ("create_manifest", "Create initial connector manifest YAML"),
        ("configure_streams", "Configure data streams and schemas"),
        ("implement_authentication", "Implement authentication mechanism"),
        ("validate_manifest", "Validate connector manifest"),
        ("test_connection", "Test connection to data source"),
        ("test_streams", "Test stream reading and data extraction"),
        ("verify_data_quality", "Verify data quality and transformations"),
    ]

    for task_id, title in tasks:
        task = ConnectorTask(id=task_id, title=title)
        task_list.add_task(task)

    return task_list
