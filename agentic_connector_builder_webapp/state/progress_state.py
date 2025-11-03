"""Progress state for task list management."""

from typing import Any

import reflex as rx

from ..task_list import TaskList, create_default_connector_task_list


class ProgressState(rx.State):
    """State for task list and progress tracking."""

    task_list_json: str = ""

    def get_task_list(self) -> TaskList:
        """Get the task list object from JSON."""
        if not self.task_list_json:
            default_task_list = create_default_connector_task_list()
            self.task_list_json = default_task_list.model_dump_json()
            return default_task_list
        return TaskList.model_validate_json(self.task_list_json)

    def update_task_list(self, task_list: TaskList):
        """Update the task list from a TaskList object."""
        self.task_list_json = task_list.model_dump_json()

    def ensure_task_list(self):
        """Ensure the task list is initialized with default values if empty."""
        if not self.task_list_json:
            default_task_list = create_default_connector_task_list()
            self.task_list_json = default_task_list.model_dump_json()

    @rx.var
    def has_task_list(self) -> bool:
        """Check if a task list has been initialized."""
        return bool(self.task_list_json)

    @rx.var
    def connector_tasks_view(self) -> list[dict[str, Any]]:
        """Get connector tasks as JSON-serializable view data."""
        if not self.task_list_json:
            return []
        try:
            task_list = TaskList.model_validate_json(self.task_list_json)
            result = []
            for task in task_list.tasks:
                if task.task_type != "connector":
                    continue
                status = task.status.value
                icon, color = {
                    "not_started": ("○", "gray.400"),
                    "in_progress": ("◐", "blue.400"),
                    "completed": ("●", "green.400"),
                    "blocked": ("⛔", "red.400"),
                }.get(status, ("?", "gray.400"))
                result.append(
                    {
                        "id": task.id,
                        "title": task.task_name,
                        "details": task.description or "",
                        "status": status,
                        "icon": icon,
                        "color": color,
                    }
                )
            return result
        except Exception:
            return []

    @rx.var
    def stream_tasks_view(self) -> list[dict[str, Any]]:
        """Get stream tasks as JSON-serializable view data, sorted by stream name."""
        if not self.task_list_json:
            return []
        try:
            task_list = TaskList.model_validate_json(self.task_list_json)
            result = []
            for task in task_list.tasks:
                if task.task_type != "stream":
                    continue
                status = task.status.value
                icon, color = {
                    "not_started": ("○", "gray.400"),
                    "in_progress": ("◐", "blue.400"),
                    "completed": ("●", "green.400"),
                    "blocked": ("⛔", "red.400"),
                }.get(status, ("?", "gray.400"))
                result.append(
                    {
                        "id": task.id,
                        "stream_name": task.stream_name,
                        "title": task.task_name,
                        "details": task.description or "",
                        "status": status,
                        "icon": icon,
                        "color": color,
                    }
                )
            result.sort(key=lambda r: (r["stream_name"], r["title"]))
            return result
        except Exception:
            return []

    @rx.var
    def finalization_tasks_view(self) -> list[dict[str, Any]]:
        """Get finalization tasks as JSON-serializable view data."""
        if not self.task_list_json:
            return []
        try:
            task_list = TaskList.model_validate_json(self.task_list_json)
            result = []
            for task in task_list.tasks:
                if task.task_type != "finalization":
                    continue
                status = task.status.value
                icon, color = {
                    "not_started": ("○", "gray.400"),
                    "in_progress": ("◐", "blue.400"),
                    "completed": ("●", "green.400"),
                    "blocked": ("⛔", "red.400"),
                }.get(status, ("?", "gray.400"))
                result.append(
                    {
                        "id": task.id,
                        "title": task.task_name,
                        "details": task.description or "",
                        "status": status,
                        "icon": icon,
                        "color": color,
                    }
                )
            return result
        except Exception:
            return []

    @rx.var
    def task_list_header(self) -> dict[str, Any]:
        """Get task list header information."""
        if not self.task_list_json:
            return {
                "name": "",
                "description": "",
                "summary": {"total": 0, "completed": 0, "in_progress": 0, "blocked": 0},
            }
        try:
            task_list = TaskList.model_validate_json(self.task_list_json)
            return {
                "name": task_list.name,
                "description": task_list.description,
                "summary": task_list.get_summary(),
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
        if not self.task_list_json:
            return ""
        try:
            task_list = TaskList.model_validate_json(self.task_list_json)
            return task_list.name
        except Exception:
            return "Task List"

    @rx.var
    def task_list_description(self) -> str:
        """Get the task list description."""
        if not self.task_list_json:
            return ""
        try:
            task_list = TaskList.model_validate_json(self.task_list_json)
            return task_list.description
        except Exception:
            return "Error parsing task list"

    @rx.var
    def task_total_count(self) -> int:
        """Get total number of tasks."""
        if not self.task_list_json:
            return 0
        try:
            task_list = TaskList.model_validate_json(self.task_list_json)
            return task_list.get_summary()["total"]
        except Exception:
            return 0

    @rx.var
    def task_completed_count(self) -> int:
        """Get number of completed tasks."""
        if not self.task_list_json:
            return 0
        try:
            task_list = TaskList.model_validate_json(self.task_list_json)
            return task_list.get_summary()["completed"]
        except Exception:
            return 0

    @rx.var
    def task_in_progress_count(self) -> int:
        """Get number of in-progress tasks."""
        if not self.task_list_json:
            return 0
        try:
            task_list = TaskList.model_validate_json(self.task_list_json)
            return task_list.get_summary()["in_progress"]
        except Exception:
            return 0

    @rx.var
    def task_blocked_count(self) -> int:
        """Get number of blocked tasks."""
        if not self.task_list_json:
            return 0
        try:
            task_list = TaskList.model_validate_json(self.task_list_json)
            return task_list.get_summary()["blocked"]
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
