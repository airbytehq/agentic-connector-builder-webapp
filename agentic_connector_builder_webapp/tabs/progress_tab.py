"""Progress tab component."""

import reflex as rx

from ..state import ChatAgentState


def progress_tab_content() -> rx.Component:
    """Render the progress tab with task list."""

    return rx.vstack(
        rx.heading("Progress", size="6", mb=4),
        rx.vstack(
            rx.heading(ChatAgentState.task_list_name, size="6", mb=2),
            rx.text(
                "Connector Builder Task List",
                color="gray.500",
                size="3",
                mb=4,
            ),
            rx.hstack(
                rx.badge(
                    ChatAgentState.completed_of_total_text,
                    color_scheme="green",
                ),
                rx.badge(
                    ChatAgentState.in_progress_text,
                    color_scheme="blue",
                ),
                rx.badge(
                    ChatAgentState.blocked_text,
                    color_scheme="red",
                ),
                spacing="2",
                mb=6,
            ),
            rx.vstack(
                rx.heading("Connector Tasks", size="5", mb=2),
                rx.foreach(
                    ChatAgentState.connector_tasks_view,
                    lambda task: rx.hstack(
                        rx.text(
                            task["icon"],
                            color=task["color"],
                            font_size="1.2em",
                        ),
                        rx.vstack(
                            rx.text(task["title"], font_weight="500"),
                            rx.cond(
                                task["details"],
                                rx.text(task["details"], color="gray.500", size="2"),
                                rx.fragment(),
                            ),
                            spacing="1",
                            align="start",
                        ),
                        spacing="3",
                        align="start",
                        width="100%",
                    ),
                ),
                spacing="3",
                align="start",
                width="100%",
                mb=6,
            ),
            rx.vstack(
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
                        rx.foreach(
                            ChatAgentState.stream_tasks_view,
                            lambda task: rx.table.row(
                                rx.table.cell(
                                    rx.text(
                                        task["icon"],
                                        color=task["color"],
                                        font_size="1.2em",
                                    )
                                ),
                                rx.table.cell(
                                    rx.text(task["stream_name"], font_weight="500")
                                ),
                                rx.table.cell(rx.text(task["title"])),
                                rx.table.cell(
                                    rx.text(
                                        task["details"],
                                        color="gray.500",
                                        size="2",
                                    )
                                ),
                            ),
                        )
                    ),
                    variant="surface",
                    width="100%",
                ),
                spacing="2",
                align="start",
                width="100%",
                mb=6,
            ),
            rx.vstack(
                rx.heading("Finalization Tasks", size="5", mb=2),
                rx.foreach(
                    ChatAgentState.finalization_tasks_view,
                    lambda task: rx.hstack(
                        rx.text(
                            task["icon"],
                            color=task["color"],
                            font_size="1.2em",
                        ),
                        rx.vstack(
                            rx.text(task["title"], font_weight="500"),
                            rx.cond(
                                task["details"],
                                rx.text(task["details"], color="gray.500", size="2"),
                                rx.fragment(),
                            ),
                            spacing="1",
                            align="start",
                        ),
                        spacing="3",
                        align="start",
                        width="100%",
                    ),
                ),
                spacing="3",
                align="start",
                width="100%",
                mb=6,
            ),
            rx.fragment(),
        ),
        rx.text(
            "No tasks yet. The task list will appear here once initialized.",
            color="gray.500",
            size="4",
        ),
    )
