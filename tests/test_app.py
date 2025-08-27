"""Unit tests for the main Reflex application components."""

import pytest

from agentic_connector_builder_webapp.agentic_connector_builder_webapp import (
    ConnectorBuilderState,
    index,
)
from agentic_connector_builder_webapp.components.yaml_editor import (
    yaml_editor_component,
)
from agentic_connector_builder_webapp.tabs.requirements_tab import (
    requirements_tab_content,
)


class TestConnectorBuilderState:
    """Test cases for ConnectorBuilderState class."""

    @pytest.mark.unit
    def test_initial_yaml_content(self, yaml_editor_state):
        """Test that ConnectorBuilderState has initial YAML content."""
        assert yaml_editor_state.yaml_content is not None
        assert len(yaml_editor_state.yaml_content) > 0
        assert "name: example-connector" in yaml_editor_state.yaml_content
        assert 'version: "1.0.0"' in yaml_editor_state.yaml_content

    @pytest.mark.unit
    def test_update_yaml_content(self, yaml_editor_state, sample_yaml_content):
        """Test updating YAML content."""
        original_content = yaml_editor_state.yaml_content
        yaml_editor_state.update_yaml_content(sample_yaml_content)

        assert yaml_editor_state.yaml_content == sample_yaml_content
        assert yaml_editor_state.yaml_content != original_content

    @pytest.mark.unit
    def test_update_yaml_content_with_empty_string(
        self, yaml_editor_state, empty_yaml_content
    ):
        """Test updating YAML content with empty string."""
        yaml_editor_state.update_yaml_content(empty_yaml_content)
        assert yaml_editor_state.yaml_content == ""

    @pytest.mark.unit
    def test_reset_yaml_content(self, yaml_editor_state, sample_yaml_content):
        """Test resetting YAML content to default."""
        # First change the content
        yaml_editor_state.update_yaml_content(sample_yaml_content)
        assert yaml_editor_state.yaml_content == sample_yaml_content

        # Then reset it
        yaml_editor_state.reset_yaml_content()
        assert "name: example-connector" in yaml_editor_state.yaml_content
        assert 'version: "1.0.0"' in yaml_editor_state.yaml_content
        assert yaml_editor_state.yaml_content != sample_yaml_content

    @pytest.mark.unit
    def test_yaml_content_persistence(self, yaml_editor_state):
        """Test that YAML content persists across multiple operations."""
        test_content = "test: value\nother: data"

        yaml_editor_state.update_yaml_content(test_content)
        assert yaml_editor_state.yaml_content == test_content

        # Content should persist
        assert yaml_editor_state.yaml_content == test_content

    @pytest.mark.unit
    def test_yaml_content_type(self, yaml_editor_state):
        """Test that YAML content is always a string."""
        assert isinstance(yaml_editor_state.yaml_content, str)

        yaml_editor_state.update_yaml_content("new content")
        assert isinstance(yaml_editor_state.yaml_content, str)


class TestYamlEditorComponent:
    """Test cases for yaml_editor_component function."""

    @pytest.mark.unit
    def test_yaml_editor_component_returns_component(self):
        """Test that yaml_editor_component returns a Reflex component."""
        component = yaml_editor_component(
            yaml_content="test: content",
            on_change=ConnectorBuilderState.update_yaml_content,
            on_reset=ConnectorBuilderState.reset_yaml_content,
        )
        assert component is not None
        # Component should be a Reflex component (has certain attributes)
        assert hasattr(component, "children") or hasattr(component, "tag")

    @pytest.mark.unit
    def test_yaml_editor_component_structure(self):
        """Test the basic structure of the YAML editor component."""
        component = yaml_editor_component(
            yaml_content="test: content",
            on_change=ConnectorBuilderState.update_yaml_content,
            on_reset=ConnectorBuilderState.reset_yaml_content,
        )
        # The component should be properly structured
        assert component is not None

    @pytest.mark.unit
    def test_requirements_tab_content_returns_component(self):
        """Test that requirements_tab_content returns a Reflex component."""
        component = requirements_tab_content(
            source_api_name="Test API",
            connector_name="test-connector",
            documentation_urls="https://example.com",
            functional_requirements="Test requirements",
            test_list="assert True",
            on_source_api_name_change=ConnectorBuilderState.set_source_api_name,
            on_connector_name_change=ConnectorBuilderState.set_connector_name,
            on_documentation_urls_change=ConnectorBuilderState.set_documentation_urls,
            on_functional_requirements_change=ConnectorBuilderState.set_functional_requirements,
            on_test_list_change=ConnectorBuilderState.set_test_list,
        )
        assert component is not None
        assert hasattr(component, "children") or hasattr(component, "tag")


class TestIndexPage:
    """Test cases for the main index page."""

    @pytest.mark.unit
    def test_index_returns_component(self):
        """Test that index function returns a Reflex component."""
        component = index()
        assert component is not None
        # Component should be a Reflex component
        assert hasattr(component, "children") or hasattr(component, "tag")

    @pytest.mark.unit
    def test_index_page_structure(self):
        """Test the basic structure of the index page."""
        component = index()
        # The component should be properly structured
        assert component is not None


class TestAppConfiguration:
    """Test cases for app configuration and setup."""

    @pytest.mark.unit
    def test_app_import(self):
        """Test that the app can be imported successfully."""
        from agentic_connector_builder_webapp.agentic_connector_builder_webapp import (
            app,
        )

        assert app is not None

    @pytest.mark.unit
    def test_app_has_pages(self):
        """Test that the app has pages configured."""
        from agentic_connector_builder_webapp.agentic_connector_builder_webapp import (
            app,
        )

        # App should have pages configured
        assert hasattr(app, "pages") or hasattr(app, "_pages")


class TestYamlContentValidation:
    """Test cases for YAML content validation and handling."""

    @pytest.mark.unit
    def test_yaml_content_with_special_characters(self, yaml_editor_state):
        """Test YAML content handling with special characters."""
        special_content = """name: "test-with-special-chars"
description: "Content with special chars: @#$%^&*()"
config:
  url: "https://api.example.com/v1"
  key: "special-key-123!"
"""
        yaml_editor_state.update_yaml_content(special_content)
        assert yaml_editor_state.yaml_content == special_content

    @pytest.mark.unit
    def test_yaml_content_with_unicode(self, yaml_editor_state):
        """Test YAML content handling with Unicode characters."""
        unicode_content = """name: "test-unicode"
description: "Content with Unicode: 你好世界 🌍"
config:
  message: "Hello 世界"
"""
        yaml_editor_state.update_yaml_content(unicode_content)
        assert yaml_editor_state.yaml_content == unicode_content

    @pytest.mark.unit
    def test_large_yaml_content(self, yaml_editor_state):
        """Test handling of large YAML content."""
        large_content = "\n".join([f"item_{i}: value_{i}" for i in range(1000)])
        yaml_editor_state.update_yaml_content(large_content)
        assert yaml_editor_state.yaml_content == large_content
        assert len(yaml_editor_state.yaml_content.split("\n")) == 1000


class TestStateManagement:
    """Test cases for state management functionality."""

    @pytest.mark.unit
    def test_multiple_state_instances(self):
        """Test that multiple state instances work independently."""
        state1 = ConnectorBuilderState()
        state2 = ConnectorBuilderState()

        test_content1 = "content1: value1"
        test_content2 = "content2: value2"

        state1.update_yaml_content(test_content1)
        state2.update_yaml_content(test_content2)

        assert state1.yaml_content == test_content1
        assert state2.yaml_content == test_content2
        assert state1.yaml_content != state2.yaml_content

    @pytest.mark.unit
    def test_state_method_chaining(self, yaml_editor_state):
        """Test that state methods can be called in sequence."""
        test_content = "test: content"

        yaml_editor_state.update_yaml_content(test_content)
        assert yaml_editor_state.yaml_content == test_content

        yaml_editor_state.reset_yaml_content()
        assert "example-connector" in yaml_editor_state.yaml_content

        yaml_editor_state.update_yaml_content("")
        assert yaml_editor_state.yaml_content == ""
