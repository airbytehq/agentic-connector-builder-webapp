"""Tests for manifest editing tools in chat_agent."""

from unittest.mock import Mock

import pytest

from agentic_connector_builder_webapp.chat_agent import (
    SessionDeps,
    get_manifest_text,
    insert_manifest_lines,
    replace_manifest_lines,
)


@pytest.fixture
def sample_yaml_content():
    """Sample YAML content for testing."""
    return """name: test-connector
version: "1.0.0"
description: "A test connector"

source:
  type: api
  url: "https://api.example.com"
destination:
  type: database
"""


@pytest.fixture
def multiline_yaml_content():
    """Create YAML content with more lines for range testing."""
    lines = [f"line {i}" for i in range(1, 21)]
    return "\n".join(lines)


@pytest.fixture
def mock_ctx():
    """Create a mock RunContext with empty YAML content."""
    ctx = Mock()
    ctx.deps = SessionDeps(
        yaml_content="",
        connector_name="test-connector",
        source_api_name="TestAPI",
        documentation_urls="",
        functional_requirements="",
        test_list="",
    )
    return ctx


class TestGetManifestText:
    """Test cases for get_manifest_text tool."""

    def test_basic_read(self, mock_ctx, sample_yaml_content):
        """Test reading manifest without line numbers."""
        mock_ctx.deps.yaml_content = sample_yaml_content
        result = get_manifest_text(mock_ctx)
        assert "name: test-connector" in result
        assert 'version: "1.0.0"' in result
        assert "source:" in result

    def test_with_line_numbers(self, mock_ctx, sample_yaml_content):
        """Test reading manifest with line numbers."""
        mock_ctx.deps.yaml_content = sample_yaml_content
        result = get_manifest_text(mock_ctx, with_line_numbers=True)
        assert "   1 |" in result
        assert "name: test-connector" in result

    def test_line_range(self, mock_ctx, multiline_yaml_content):
        """Test reading a specific line range."""
        mock_ctx.deps.yaml_content = multiline_yaml_content
        result = get_manifest_text(mock_ctx, start_line=5, end_line=10)
        lines = result.split("\n")
        assert len(lines) == 6
        assert "line 5" in lines[0]
        assert "line 10" in lines[5]

    def test_start_line_only(self, mock_ctx, multiline_yaml_content):
        """Test reading from start_line to end of content."""
        mock_ctx.deps.yaml_content = multiline_yaml_content
        result = get_manifest_text(mock_ctx, start_line=15)
        lines = result.split("\n")
        assert "line 15" in lines[0]
        assert "line 20" in lines[-1]

    def test_end_line_only(self, mock_ctx, multiline_yaml_content):
        """Test reading from beginning to end_line."""
        mock_ctx.deps.yaml_content = multiline_yaml_content
        result = get_manifest_text(mock_ctx, end_line=5)
        lines = result.split("\n")
        assert len(lines) == 5
        assert "line 1" in lines[0]
        assert "line 5" in lines[4]

    def test_line_numbers_with_range(self, mock_ctx, multiline_yaml_content):
        """Test line numbers with a specific range."""
        mock_ctx.deps.yaml_content = multiline_yaml_content
        result = get_manifest_text(
            mock_ctx,
            with_line_numbers=True,
            start_line=5,
            end_line=8,
        )
        assert "   5 |" in result
        assert "   8 |" in result
        assert "   4 |" not in result
        assert "   9 |" not in result

    def test_no_content(self, mock_ctx):
        """Test error when no YAML content available."""
        mock_ctx.deps.yaml_content = ""
        result = get_manifest_text(mock_ctx)
        assert "Error: No YAML content available" in result

    def test_invalid_start_line(self, mock_ctx, sample_yaml_content):
        """Test error with invalid start_line."""
        mock_ctx.deps.yaml_content = sample_yaml_content
        result = get_manifest_text(mock_ctx, start_line=100)
        assert "Error: start_line" in result
        assert "out of range" in result

    def test_invalid_end_line(self, mock_ctx, sample_yaml_content):
        """Test error with end_line before start_line."""
        mock_ctx.deps.yaml_content = sample_yaml_content
        result = get_manifest_text(mock_ctx, start_line=5, end_line=3)
        assert "Error: end_line" in result


class TestInsertManifestLines:
    """Test cases for insert_manifest_lines tool."""

    def test_insert_at_beginning(self, mock_ctx, sample_yaml_content):
        """Test inserting lines at the beginning of the content."""
        mock_ctx.deps.yaml_content = sample_yaml_content
        result = insert_manifest_lines(mock_ctx, 1, "# New header comment")

        lines = result.split("\n")
        assert lines[0] == "# New header comment"
        assert lines[1] == "name: test-connector"

    def test_insert_in_middle(self, mock_ctx, multiline_yaml_content):
        """Test inserting lines in the middle of the content."""
        mock_ctx.deps.yaml_content = multiline_yaml_content
        result = insert_manifest_lines(mock_ctx, 10, "inserted line")

        lines = result.split("\n")
        assert "inserted line" in lines[9]
        assert "line 10" in lines[10]

    def test_insert_at_end(self, mock_ctx, multiline_yaml_content):
        """Test inserting lines at the end of the content."""
        mock_ctx.deps.yaml_content = multiline_yaml_content
        result = insert_manifest_lines(mock_ctx, 100, "# End comment")

        assert result.strip().endswith("# End comment")

    def test_insert_multiline(self, mock_ctx, sample_yaml_content):
        """Test inserting multiple lines at once."""
        mock_ctx.deps.yaml_content = sample_yaml_content
        multiline_content = "# Comment 1\n# Comment 2\n# Comment 3"
        result = insert_manifest_lines(mock_ctx, 1, multiline_content)

        lines = result.split("\n")
        assert lines[0] == "# Comment 1"
        assert lines[1] == "# Comment 2"
        assert lines[2] == "# Comment 3"
        assert lines[3] == "name: test-connector"

    def test_insert_invalid_line_number(self, mock_ctx, sample_yaml_content):
        """Test error with invalid line number."""
        mock_ctx.deps.yaml_content = sample_yaml_content
        result = insert_manifest_lines(mock_ctx, 0, "content")
        assert "Error: line_number must be >= 1" in result

    def test_insert_no_content(self, mock_ctx):
        """Test error when no YAML content available."""
        mock_ctx.deps.yaml_content = ""
        result = insert_manifest_lines(mock_ctx, 1, "content")
        assert "Error: No YAML content available" in result


class TestReplaceManifestLines:
    """Test cases for replace_manifest_lines tool."""

    def test_replace_single_line(self, mock_ctx, multiline_yaml_content):
        """Test replacing a single line."""
        mock_ctx.deps.yaml_content = multiline_yaml_content
        result = replace_manifest_lines(mock_ctx, 5, 5, "replaced line 5")

        lines = result.split("\n")
        assert "replaced line 5" in lines[4]
        assert "line 4" in lines[3]
        assert "line 6" in lines[5]

    def test_replace_multiple_lines(self, mock_ctx, multiline_yaml_content):
        """Test replacing multiple consecutive lines."""
        mock_ctx.deps.yaml_content = multiline_yaml_content
        result = replace_manifest_lines(
            mock_ctx,
            5,
            8,
            "replacement line 1\nreplacement line 2",
        )

        lines = result.split("\n")
        assert "replacement line 1" in lines[4]
        assert "replacement line 2" in lines[5]
        assert "line 9" in lines[6]

    def test_replace_at_beginning(self, mock_ctx, sample_yaml_content):
        """Test replacing lines at the beginning of the content."""
        mock_ctx.deps.yaml_content = sample_yaml_content
        result = replace_manifest_lines(mock_ctx, 1, 2, "# New header")

        lines = result.split("\n")
        assert "# New header" in lines[0]
        assert 'description: "A test connector"' in lines[1]

    def test_replace_at_end(self, mock_ctx, multiline_yaml_content):
        """Test replacing lines at the end of the content."""
        mock_ctx.deps.yaml_content = multiline_yaml_content
        result = replace_manifest_lines(mock_ctx, 19, 20, "# End lines replaced")

        assert result.strip().endswith("# End lines replaced")

    def test_replace_with_empty_string(self, mock_ctx, multiline_yaml_content):
        """Test replacing lines with empty content (deletion)."""
        mock_ctx.deps.yaml_content = multiline_yaml_content
        result = replace_manifest_lines(mock_ctx, 10, 15, "")

        lines = result.split("\n")
        assert "line 16" in lines[9]

    def test_replace_invalid_start_line(self, mock_ctx, sample_yaml_content):
        """Test error with invalid start_line."""
        mock_ctx.deps.yaml_content = sample_yaml_content
        result = replace_manifest_lines(mock_ctx, 100, 101, "content")
        assert "Error: start_line" in result
        assert "out of range" in result

    def test_replace_end_before_start(self, mock_ctx, sample_yaml_content):
        """Test error with end_line before start_line."""
        mock_ctx.deps.yaml_content = sample_yaml_content
        result = replace_manifest_lines(mock_ctx, 5, 3, "content")
        assert "Error: end_line" in result
        assert "before start_line" in result

    def test_replace_invalid_end_line(self, mock_ctx, sample_yaml_content):
        """Test error with invalid end_line."""
        mock_ctx.deps.yaml_content = sample_yaml_content
        result = replace_manifest_lines(mock_ctx, 1, 100, "content")
        assert "Error: end_line" in result
        assert "out of range" in result

    def test_replace_no_content(self, mock_ctx):
        """Test error when no YAML content available."""
        mock_ctx.deps.yaml_content = ""
        result = replace_manifest_lines(mock_ctx, 1, 2, "content")
        assert "Error: No YAML content available" in result
