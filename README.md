# Agentic Connector Builder WebApp

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/airbytehq/agentic-connector-builder-webapp?quickstart=1)

A full-stack agentic connector builder webapp with YAML editing capabilities. This application provides an intuitive interface for building and configuring data connectors using a modern web-based YAML editor.

## Features

- **YAML Editor**: Monaco-based editor with syntax highlighting and validation
- **Reflex Framework**: Modern Python web framework for full-stack development
- **Testing Suite**: Comprehensive unit and end-to-end testing with pytest and Playwright
- **Development Tools**: Modern Python tooling with uv package manager

## Quick Start

### Run with uvx (No Installation Required)

Run the webapp directly from GitHub using `uvx`:

```bash
uvx --from git+https://github.com/airbytehq/agentic-connector-builder-webapp agentic-connector-builder-webapp
```

This will automatically fetch and run the latest version from the `main` branch. The app will start at `http://localhost:3000`.

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager

### Local Development

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Run the application:**
   ```bash
   uv run reflex run
   ```

3. **Open your browser:**
   Navigate to `http://localhost:3000` to access the YAML editor interface.

## Development

For detailed development setup, testing instructions, and contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Project Structure

```
├── src/agentic_connector_builder_webapp/  # Main application code
├── tests/                                 # Unit tests
├── tests/e2e/                            # End-to-end tests
├── pyproject.toml                        # Project configuration
└── playwright.config.py                 # E2E test configuration
```

## License

[Internal, incubating repo.] A fledgling attempt to build a new connector builder webapp: full stack and agentic, secure by default for multi-tenant use cases, and decoupled from Airbyte Platform infra.
