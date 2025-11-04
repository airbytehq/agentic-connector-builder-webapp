"""Main Reflex application with YAML editor using reflex-monaco."""

from pathlib import Path

import reflex as rx
from dotenv import load_dotenv

from .pages.index import index

env_file = Path.cwd() / ".env"
if env_file.exists():
    load_dotenv(env_file)

SIDEBAR_WIDTH_PERCENT = "33.333%"
MAIN_CONTENT_WIDTH_PERCENT = "66.667%"


# Create the Reflex app
app = rx.App(
    theme=rx.theme(
        appearance="dark",
        has_background=True,
        radius="medium",
        accent_color="blue",
    )
)

# Add the main page
app.add_page(index, route="/", title="Agentic Connector Builder")
