# Contributing to Agentic Connector Builder WebApp

Thank you for your interest in contributing to the Agentic Connector Builder WebApp! This guide will help you get started with development and testing.

## Development Tools

This project uses modern Python development tools for an efficient development experience:

- **[uv](https://docs.astral.sh/uv/)** - Fast Python package manager and project manager
- **[Reflex](https://reflex.dev/)** - Full-stack Python web framework
- **[pytest](https://pytest.org/)** - Python testing framework for unit tests
- **[Playwright](https://playwright.dev/python/)** - End-to-end testing framework

## Prerequisites

### Required
- **Python 3.13+** - The project requires Python 3.13 or higher
- **uv** - Package manager for dependency management

### Installing uv

If you don't have uv installed, install it using one of these methods:

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Using pip
pip install uv
```

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd agentic-connector-builder-webapp
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```
   This will create a virtual environment and install all dependencies including dev dependencies.

3. **Install Playwright browsers (for e2e tests):**
   ```bash
   uv run playwright install
   ```

## Running the Application

### Development Server
```bash
uv run reflex run
```
The application will be available at `http://localhost:3000`

### Production Mode
```bash
uv run reflex run --env prod
```

## Testing

### Unit Tests
Run unit tests using pytest:
```bash
# Run all unit tests
uv run pytest tests/

# Run with coverage
uv run pytest tests/ --cov=src/agentic_connector_builder_webapp

# Run specific test file
uv run pytest tests/test_app.py

# Run with verbose output
uv run pytest tests/ -v
```

### End-to-End Tests
Run e2e tests using Playwright:
```bash
# Run all e2e tests
uv run pytest tests/e2e/

# Run e2e tests with headed browser (for debugging)
uv run pytest tests/e2e/ --headed

# Run specific e2e test
uv run pytest tests/e2e/test_yaml_editor.py

# Run e2e tests with specific browser
uv run pytest tests/e2e/ --browser chromium
```

### Running All Tests
```bash
# Run both unit and e2e tests
uv run pytest

# Run tests in parallel (faster)
uv run pytest -n auto
```

## Project Structure

```
agentic-connector-builder-webapp/
├── src/
│   └── agentic_connector_builder_webapp/
│       ├── __init__.py
│       └── app.py                    # Main Reflex application
├── tests/
│   ├── __init__.py
│   ├── conftest.py                   # pytest configuration
│   ├── test_app.py                   # Unit tests
│   └── e2e/
│       ├── __init__.py
│       ├── conftest.py               # Playwright configuration
│       └── test_yaml_editor.py       # E2E tests
├── pyproject.toml                    # Project configuration
├── playwright.config.py             # Playwright configuration
├── README.md
└── CONTRIBUTING.md
```

## Development Workflow

1. **Make your changes** in the appropriate files
2. **Run unit tests** to ensure your changes don't break existing functionality
3. **Run e2e tests** to verify the application works end-to-end
4. **Test the application manually** by running the dev server
5. **Commit your changes** with a descriptive commit message

## Code Style

- Follow Python PEP 8 style guidelines
- Use type hints where appropriate
- Write descriptive docstrings for functions and classes
- Keep functions focused and modular

## Testing Guidelines

### Unit Tests
- Test individual components and functions in isolation
- Use fixtures for common test data
- Mock external dependencies
- Aim for high test coverage

### E2E Tests
- Test complete user workflows
- Focus on critical user paths
- Test across different browsers when needed
- Use page object patterns for complex interactions

## Troubleshooting

### Common Issues

**Dependencies not installing:**
```bash
# Clear uv cache and reinstall
uv cache clean
uv sync --reinstall
```

**Playwright browsers not found:**
```bash
# Reinstall Playwright browsers
uv run playwright install --force
```

**Reflex app not starting:**
```bash
# Check if port 3000 is available
lsof -i :3000

# Run on different port
uv run reflex run --port 3001
```

**Tests failing:**
```bash
# Run tests with more verbose output
uv run pytest -v -s

# Run specific failing test
uv run pytest tests/test_specific.py::test_function -v
```

## Getting Help

- Check the [Reflex documentation](https://reflex.dev/docs/)
- Review [Playwright Python documentation](https://playwright.dev/python/)
- Look at existing tests for examples
- Open an issue for bugs or feature requests

## Development Tips

- Use `uv run reflex run --env dev` for development with hot reloading
- Run tests frequently during development
- Use browser dev tools for debugging frontend issues
- Check Playwright traces for e2e test debugging: `uv run pytest tests/e2e/ --tracing on`
