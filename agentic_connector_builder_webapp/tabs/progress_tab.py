"""Progress tab component."""

import reflex as rx

from ..task_list import StreamTask, TaskList, TaskStatus


def get_status_icon(status: TaskStatus) -> str:
    """Get the icon for a task status."""
    return {
        TaskStatus.NOT_STARTED: "○",
        TaskStatus.IN_PROGRESS: "◐",
        TaskStatus.COMPLETED: "●",
        TaskStatus.FAILED: "✗",
    }.get(status, "?")


def get_status_color(status: TaskStatus) -> str:
    """Get the color for a task status."""
    return {
        TaskStatus.NOT_STARTED: "gray.400",
        TaskStatus.IN_PROGRESS: "blue.400",
        TaskStatus.COMPLETED: "green.400",
        TaskStatus.FAILED: "red.400",
    }.get(status, "gray.400")


def render_connector_task(task) -> rx.Component:
    """Render a single connector task."""
    return rx.hstack(
        rx.text(
            get_status_icon(task.status),
            color=get_status_color(task.status),
            font_size="1.2em",
        ),
        rx.vstack(
            rx.text(str(task), font_weight="500"),
            rx.cond(
                task.details,
                rx.text(task.details, color="gray.500", size="2"),
                rx.fragment(),
            ),
            spacing="1",
            align="start",
        ),
        spacing="3",
        align="start",
        width="100%",
    )


def render_stream_tasks_table(stream_tasks: list) -> rx.Component:
    """Render stream tasks in a table format."""
    if not stream_tasks:
        return rx.fragment()

    sorted_tasks = sorted(stream_tasks, key=lambda t: t.stream_name)

    return rx.vstack(
        rx.heading("Stream Tasks", size="5", mb=2),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Status"),
                    rx.table.column_header_cell("Stream"),
                    rx.table.column_header_cell("Task"),
                    rx.table.column_header_cell("Details"),
                )
            ),
            rx.table.body(
                *[
                    rx.table.row(
                        rx.table.cell(
                            rx.text(
                                get_status_icon(task.status),
                                color=get_status_color(task.status),
                                font_size="1.2em",
                            )
                        ),
                        rx.table.cell(rx.text(task.stream_name, font_weight="500")),
                        rx.table.cell(rx.text(task.title)),
                        rx.table.cell(
                            rx.text(task.details or "", color="gray.500", size="2")
                        ),
                    )
                    for task in sorted_tasks
                ]
            ),
            variant="surface",
            width="100%",
        ),
        spacing="2",
        align="start",
        width="100%",
        mb=6,
    )


def progress_tab_content(task_list_json: str = "") -> rx.Component:
    """Render the progress tab with task list."""

    def render_task_list():
        """Render the task list from JSON."""
        if not task_list_json:
            return rx.text(
                "No tasks yet. The task list will appear here once initialized.",
                color="gray.500",
                size="4",
            )

        try:
            task_list = TaskList.model_validate_json(task_list_json)
            summary = task_list.get_summary()

            connector_tasks = [
                t for t in task_list.tasks if not isinstance(t, StreamTask)
            ]
            stream_tasks = [t for t in task_list.tasks if isinstance(t, StreamTask)]

            return rx.vstack(
                rx.heading(task_list.name, size="6", mb=2),
                rx.text(task_list.description, color="gray.500", size="3", mb=4),
                rx.hstack(
                    rx.badge(
                        f"{summary['completed']}/{summary['total']} Completed",
                        color_scheme="green",
                    ),
                    rx.badge(
                        f"{summary['in_progress']} In Progress", color_scheme="blue"
                    ),
                    rx.badge(f"{summary['failed']} Failed", color_scheme="red"),
                    spacing="2",
                    mb=6,
                ),
                rx.cond(
                    len(connector_tasks) > 0,
                    rx.vstack(
                        rx.heading("Connector Tasks", size="5", mb=2),
                        *[render_connector_task(task) for task in connector_tasks],
                        spacing="3",
                        align="start",
                        width="100%",
                        mb=6,
                    ),
                    rx.fragment(),
                ),
                render_stream_tasks_table(stream_tasks),
                spacing="4",
                align="start",
                width="100%",
            )
        except Exception as e:
            return rx.text(
                f"Error loading task list: {str(e)}",
                color="red.400",
                size="4",
            )

    return rx.vstack(
        rx.heading("Progress", size="6", mb=4),
        render_task_list(),
        spacing="4",
        align="start",
        width="100%",
    )
