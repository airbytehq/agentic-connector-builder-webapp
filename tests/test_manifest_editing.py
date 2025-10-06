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
def mock_ctx():
    """Create a mock RunContext for testing."""
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


@pytest.fixture
def sample_manifest(tmp_path):
    """Create a sample manifest file for testing."""
    manifest_path = tmp_path / "manifest.yaml"
    content = """name: test-connector
version: "1.0.0"
description: "A test connector"

source:
  type: api
  url: "https://api.test.com"

destination:
  type: database
"""
    manifest_path.write_text(content)
    return manifest_path


@pytest.fixture
def multiline_manifest(tmp_path):
    """Create a manifest with more lines for range testing."""
    manifest_path = tmp_path / "manifest.yaml"
    lines = [f"line {i}" for i in range(1, 21)]
    manifest_path.write_text("\n".join(lines) + "\n")
    return manifest_path


class TestGetManifestText:
    """Tests for get_manifest_text tool."""

    def test_get_full_content(self, mock_ctx, sample_manifest):
        """Test reading full file content without line numbers."""
        result = get_manifest_text(mock_ctx, str(sample_manifest))
        assert "name: test-connector" in result
        assert "version: " in result
        assert "source:" in result
        assert "Error" not in result

    def test_get_with_line_numbers(self, mock_ctx, sample_manifest):
        """Test reading content with line numbers."""
        result = get_manifest_text(
            mock_ctx, str(sample_manifest), with_line_numbers=True
        )
        assert "   1 | name: test-connector" in result
        assert "   2 | version:" in result
        assert "Error" not in result

    def test_get_line_range(self, mock_ctx, multiline_manifest):
        """Test reading specific line range."""
        result = get_manifest_text(
            mock_ctx, str(multiline_manifest), start_line=5, end_line=10
        )
        lines = result.split("\n")
        assert len(lines) == 6
        assert lines[0] == "line 5"
        assert lines[-1] == "line 10"

    def test_get_line_range_with_numbers(self, mock_ctx, multiline_manifest):
        """Test reading line range with line numbers."""
        result = get_manifest_text(
            mock_ctx,
            str(multiline_manifest),
            with_line_numbers=True,
            start_line=5,
            end_line=10,
        )
        lines = result.split("\n")
        assert len(lines) == 6
        assert "   5 | line 5" in lines[0]
        assert "  10 | line 10" in lines[-1]

    def test_get_from_start_line(self, mock_ctx, multiline_manifest):
        """Test reading from start line to end of file."""
        result = get_manifest_text(mock_ctx, str(multiline_manifest), start_line=15)
        lines = result.split("\n")
        assert len(lines) == 6
        assert lines[0] == "line 15"
        assert lines[-1] == "line 20"

    def test_get_to_end_line(self, mock_ctx, multiline_manifest):
        """Test reading from beginning to end line."""
        result = get_manifest_text(mock_ctx, str(multiline_manifest), end_line=5)
        lines = result.split("\n")
        assert len(lines) == 5
        assert lines[0] == "line 1"
        assert lines[-1] == "line 5"

    def test_file_not_found(self, mock_ctx, tmp_path):
        """Test error when file doesn't exist."""
        result = get_manifest_text(mock_ctx, str(tmp_path / "nonexistent.yaml"))
        assert "Error: File not found" in result

    def test_invalid_start_line(self, mock_ctx, sample_manifest):
        """Test error with start line out of range."""
        result = get_manifest_text(mock_ctx, str(sample_manifest), start_line=100)
        assert "Error: start_line" in result
        assert "out of range" in result

    def test_invalid_end_line(self, mock_ctx, sample_manifest):
        """Test error with end line before start line."""
        result = get_manifest_text(
            mock_ctx, str(sample_manifest), start_line=5, end_line=2
        )
        assert "Error: end_line" in result
        assert "before start_line" in result

    def test_path_is_directory(self, mock_ctx, tmp_path):
        """Test error when path is a directory."""
        result = get_manifest_text(mock_ctx, str(tmp_path))
        assert "Error: Path is not a file" in result


class TestInsertManifestLines:
    """Tests for insert_manifest_lines tool."""

    def test_insert_at_beginning(self, mock_ctx, sample_manifest):
        """Test inserting lines at beginning of file."""
        result = insert_manifest_lines(
            mock_ctx, str(sample_manifest), 1, "# New comment"
        )
        assert "Successfully inserted 1 line(s)" in result

        content = get_manifest_text(mock_ctx, str(sample_manifest))
        lines = content.split("\n")
        assert lines[0] == "# New comment"
        assert lines[1] == "name: test-connector"

    def test_insert_in_middle(self, mock_ctx, sample_manifest):
        """Test inserting lines in middle of file."""
        result = insert_manifest_lines(
            mock_ctx, str(sample_manifest), 3, "# Middle comment"
        )
        assert "Successfully inserted 1 line(s)" in result

        content = get_manifest_text(mock_ctx, str(sample_manifest))
        assert "# Middle comment" in content

    def test_insert_at_end(self, mock_ctx, sample_manifest):
        """Test appending lines at end of file."""
        result = insert_manifest_lines(
            mock_ctx, str(sample_manifest), 999, "# End comment"
        )
        assert "Successfully inserted 1 line(s)" in result

        content = get_manifest_text(mock_ctx, str(sample_manifest))
        lines = content.split("\n")
        assert lines[-1] == "# End comment" or lines[-2] == "# End comment"

    def test_insert_multiple_lines(self, mock_ctx, sample_manifest):
        """Test inserting multiple lines at once."""
        multiline = "# Comment 1\n# Comment 2\n# Comment 3"
        result = insert_manifest_lines(mock_ctx, str(sample_manifest), 2, multiline)
        assert "Successfully inserted 3 line(s)" in result

    def test_insert_file_not_found(self, mock_ctx, tmp_path):
        """Test error when file doesn't exist."""
        result = insert_manifest_lines(
            mock_ctx, str(tmp_path / "nonexistent.yaml"), 1, "content"
        )
        assert "Error: File not found" in result

    def test_insert_invalid_line_number(self, mock_ctx, sample_manifest):
        """Test error with invalid line number."""
        result = insert_manifest_lines(mock_ctx, str(sample_manifest), 0, "content")
        assert "Error: line_number must be >= 1" in result

    def test_insert_path_is_directory(self, mock_ctx, tmp_path):
        """Test error when path is a directory."""
        result = insert_manifest_lines(mock_ctx, str(tmp_path), 1, "content")
        assert "Error: Path is not a file" in result


class TestReplaceManifestLines:
    """Tests for replace_manifest_lines tool."""

    def test_replace_single_line(self, mock_ctx, multiline_manifest):
        """Test replacing a single line."""
        result = replace_manifest_lines(
            mock_ctx, str(multiline_manifest), 5, 5, "replaced line 5"
        )
        assert "Successfully replaced 1 line(s)" in result

        content = get_manifest_text(mock_ctx, str(multiline_manifest))
        lines = content.split("\n")
        assert lines[4] == "replaced line 5"

    def test_replace_multiple_lines(self, mock_ctx, multiline_manifest):
        """Test replacing multiple consecutive lines."""
        replacement = "new line 1\nnew line 2\nnew line 3"
        result = replace_manifest_lines(
            mock_ctx, str(multiline_manifest), 5, 7, replacement
        )
        assert "Successfully replaced 3 line(s)" in result

        content = get_manifest_text(mock_ctx, str(multiline_manifest))
        assert "new line 1" in content
        assert "new line 2" in content
        assert "new line 3" in content

    def test_replace_with_fewer_lines(self, mock_ctx, multiline_manifest):
        """Test replacing multiple lines with fewer lines."""
        result = replace_manifest_lines(
            mock_ctx, str(multiline_manifest), 5, 7, "single replacement"
        )
        assert "Successfully replaced 3 line(s)" in result
        assert "with 1 new line(s)" in result

        content = get_manifest_text(mock_ctx, str(multiline_manifest))
        lines = content.split("\n")
        assert len(lines) == 18

    def test_replace_with_more_lines(self, mock_ctx, multiline_manifest):
        """Test replacing lines with more lines."""
        replacement = "new 1\nnew 2\nnew 3\nnew 4\nnew 5"
        result = replace_manifest_lines(
            mock_ctx, str(multiline_manifest), 5, 7, replacement
        )
        assert "Successfully replaced 3 line(s)" in result
        assert "with 5 new line(s)" in result

    def test_replace_at_beginning(self, mock_ctx, multiline_manifest):
        """Test replacing lines at beginning of file."""
        result = replace_manifest_lines(
            mock_ctx, str(multiline_manifest), 1, 3, "new first line"
        )
        assert "Successfully replaced 3 line(s)" in result

        content = get_manifest_text(mock_ctx, str(multiline_manifest))
        lines = content.split("\n")
        assert lines[0] == "new first line"

    def test_replace_at_end(self, mock_ctx, multiline_manifest):
        """Test replacing lines at end of file."""
        result = replace_manifest_lines(
            mock_ctx, str(multiline_manifest), 18, 20, "new last line"
        )
        assert "Successfully replaced 3 line(s)" in result

        content = get_manifest_text(mock_ctx, str(multiline_manifest))
        lines = content.split("\n")
        assert lines[-1] == "new last line" or lines[-2] == "new last line"

    def test_replace_file_not_found(self, mock_ctx, tmp_path):
        """Test error when file doesn't exist."""
        result = replace_manifest_lines(
            mock_ctx, str(tmp_path / "nonexistent.yaml"), 1, 2, "content"
        )
        assert "Error: File not found" in result

    def test_replace_invalid_start_line(self, mock_ctx, sample_manifest):
        """Test error with start line out of range."""
        result = replace_manifest_lines(
            mock_ctx, str(sample_manifest), 100, 101, "content"
        )
        assert "Error: start_line" in result
        assert "out of range" in result

    def test_replace_invalid_end_line(self, mock_ctx, sample_manifest):
        """Test error with end line before start line."""
        result = replace_manifest_lines(mock_ctx, str(sample_manifest), 5, 2, "content")
        assert "Error: end_line" in result
        assert "before start_line" in result

    def test_replace_end_line_out_of_range(self, mock_ctx, multiline_manifest):
        """Test error with end line out of range."""
        result = replace_manifest_lines(
            mock_ctx, str(multiline_manifest), 5, 100, "content"
        )
        assert "Error: end_line" in result
        assert "out of range" in result

    def test_replace_path_is_directory(self, mock_ctx, tmp_path):
        """Test error when path is a directory."""
        result = replace_manifest_lines(mock_ctx, str(tmp_path), 1, 2, "content")
        assert "Error: Path is not a file" in result
