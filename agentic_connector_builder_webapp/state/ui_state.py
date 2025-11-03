"""UI state for connector builder."""

import os

import reflex as rx


class UIState(rx.State):
    """State for UI-related concerns like tabs and modals."""

    current_tab: str = "requirements"
    settings_modal_open: bool = False
    openai_api_key_input: str = ""

    def set_current_tab(self, tab: str) -> None:
        """Set the current active tab."""
        self.current_tab = tab

    def open_settings_modal(self) -> None:
        """Open the settings modal."""
        self.settings_modal_open = True

    def close_settings_modal(self) -> None:
        """Close the settings modal."""
        self.settings_modal_open = False

    def set_openai_api_key_input(self, value: str) -> None:
        """Set the OpenAI API key input value."""
        self.openai_api_key_input = value

    def save_settings(self) -> None:
        """Save settings (currently just closes modal as state is already updated)."""
        self.settings_modal_open = False

    def get_effective_api_key(self) -> str:
        """Get the effective OpenAI API key (UI input takes precedence over env var)."""
        if self.openai_api_key_input:
            return self.openai_api_key_input
        return os.environ.get("OPENAI_API_KEY", "")

    @rx.var
    def has_api_key(self) -> bool:
        """Check if an API key is configured (either from env var or UI input)."""
        return bool(self.get_effective_api_key())

    @rx.var
    def has_env_api_key(self) -> bool:
        """Check if an API key is available from environment variables (not UI input)."""
        return bool(os.environ.get("OPENAI_API_KEY", ""))
