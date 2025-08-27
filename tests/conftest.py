"""Pytest configuration and fixtures for agentic-connector-builder-webapp tests."""

import sys
from pathlib import Path

import pytest

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def sample_yaml_content():
    """Fixture providing sample YAML content for testing."""
    return """# Test YAML configuration
name: test-connector
version: "1.0.0"
description: "A test connector configuration"

source:
  type: api
  url: "https://api.test.com"
destination:
  type: database
  connection:
    host: localhost
    port: 5432
    database: test_db

transformations:
  - type: field_mapping
    mappings:
      id: user_id
      name: full_name
"""


@pytest.fixture
def empty_yaml_content():
    """Fixture providing empty YAML content for testing."""
    return ""


@pytest.fixture
def invalid_yaml_content():
    """Fixture providing invalid YAML content for testing."""
    return """# Invalid YAML - missing quotes and improper indentation
name: test-connector
version: 1.0.0
description: A test connector
  invalid_indentation: true
source:
type: api
"""


@pytest.fixture
def yaml_editor_state():
    """Fixture providing a ConnectorBuilderState instance for testing."""
    from agentic_connector_builder_webapp.agentic_connector_builder_webapp import (
        ConnectorBuilderState,
    )

    return ConnectorBuilderState()


# Configure pytest settings
def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
