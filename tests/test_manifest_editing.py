"""Tests for manifest editing tools in chat_agent."""

from unittest.mock import Mock

import pytest

from agentic_connector_builder_webapp.chat_agent import (
    SessionDeps,
    get_manifest_text,
    insert_manifest_lines,
    replace_manifest_lines,
)

SAMPLE_YAML = """name: test-connector
version: "1.0.0"
description: "A test connector"

source:
  type: api
  url: "https://api.example.com"
destination:
  type: database
"""

MULTILINE_YAML = "\n".join([f"line {i}" for i in range(1, 21)])


def create_mock_ctx(yaml_content=""):
    """Create a mock RunContext with specified YAML content."""
    ctx = Mock()
    ctx.deps = SessionDeps(
        yaml_content=yaml_content,
        connector_name="test-connector",
        source_api_name="TestAPI",
        documentation_urls="",
        functional_requirements="",
        test_list="",
    )
    return ctx


@pytest.mark.parametrize(
    "yaml_content,with_line_numbers,start_line,end_line,expected_in_result,expected_not_in_result,expected_line_count",
    [
        pytest.param(
            SAMPLE_YAML,
            False,
            None,
            None,
            ["name: test-connector", 'version: "1.0.0"', "source:"],
            [],
            None,
            id="basic_read",
        ),
        pytest.param(
            SAMPLE_YAML,
            True,
            None,
            None,
            ["   1 |", "name: test-connector"],
            [],
            None,
            id="with_line_numbers",
        ),
        pytest.param(
            MULTILINE_YAML,
            False,
            5,
            10,
            ["line 5", "line 10"],
            [],
            6,
            id="line_range",
        ),
        pytest.param(
            MULTILINE_YAML,
            False,
            15,
            None,
            ["line 15", "line 20"],
            [],
            None,
            id="start_line_only",
        ),
        pytest.param(
            MULTILINE_YAML,
            False,
            None,
            5,
            ["line 1", "line 5"],
            [],
            5,
            id="end_line_only",
        ),
        pytest.param(
            MULTILINE_YAML,
            True,
            5,
            8,
            ["   5 |", "   8 |"],
            ["   4 |", "   9 |"],
            None,
            id="line_numbers_with_range",
        ),
        pytest.param(
            "",
            False,
            None,
            None,
            ["Error: No YAML content available"],
            [],
            None,
            id="no_content",
        ),
        pytest.param(
            SAMPLE_YAML,
            False,
            100,
            None,
            ["Error: start_line", "out of range"],
            [],
            None,
            id="invalid_start_line",
        ),
        pytest.param(
            SAMPLE_YAML,
            False,
            5,
            3,
            ["Error: end_line"],
            [],
            None,
            id="invalid_end_line",
        ),
    ],
)
def test_get_manifest_text(
    yaml_content,
    with_line_numbers,
    start_line,
    end_line,
    expected_in_result,
    expected_not_in_result,
    expected_line_count,
):
    """Test get_manifest_text with various parameters and edge cases."""
    ctx = create_mock_ctx(yaml_content)
    result = get_manifest_text(ctx, with_line_numbers, start_line, end_line)

    for expected in expected_in_result:
        assert expected in result

    for not_expected in expected_not_in_result:
        assert not_expected not in result

    if expected_line_count is not None:
        assert len(result.split("\n")) == expected_line_count


@pytest.mark.parametrize(
    "yaml_content,line_number,lines_to_insert,expected_in_result,expected_at_line,should_modify",
    [
        pytest.param(
            SAMPLE_YAML,
            1,
            "# New header comment",
            ["Successfully inserted", "1 line(s)"],
            {0: "# New header comment", 1: "name: test-connector"},
            True,
            id="insert_at_beginning",
        ),
        pytest.param(
            MULTILINE_YAML,
            10,
            "inserted line",
            ["Successfully inserted"],
            {9: "inserted line", 10: "line 10"},
            True,
            id="insert_in_middle",
        ),
        pytest.param(
            MULTILINE_YAML,
            100,
            "# End comment",
            ["Successfully inserted"],
            {},
            True,
            id="insert_at_end",
        ),
        pytest.param(
            SAMPLE_YAML,
            1,
            "# Comment 1\n# Comment 2\n# Comment 3",
            ["Successfully inserted", "3 line(s)"],
            {
                0: "# Comment 1",
                1: "# Comment 2",
                2: "# Comment 3",
                3: "name: test-connector",
            },
            True,
            id="insert_multiline",
        ),
        pytest.param(
            SAMPLE_YAML,
            0,
            "content",
            ["Error: line_number must be >= 1"],
            {},
            False,
            id="invalid_line_number",
        ),
        pytest.param(
            "",
            1,
            "content",
            ["Error: No YAML content available"],
            {},
            False,
            id="no_content",
        ),
    ],
)
def test_insert_manifest_lines(
    yaml_content,
    line_number,
    lines_to_insert,
    expected_in_result,
    expected_at_line,
    should_modify,
):
    """Test insert_manifest_lines with various parameters and edge cases."""
    ctx = create_mock_ctx(yaml_content)
    original_content = yaml_content
    result = insert_manifest_lines(ctx, line_number, lines_to_insert)

    for expected in expected_in_result:
        assert expected in result

    if should_modify:
        assert ctx.deps.yaml_content != original_content
        lines = ctx.deps.yaml_content.split("\n")
        for line_idx, expected_text in expected_at_line.items():
            assert expected_text in lines[line_idx]
    else:
        assert ctx.deps.yaml_content == original_content


@pytest.mark.parametrize(
    "yaml_content,start_line,end_line,new_lines,expected_in_result,expected_at_line,should_modify",
    [
        pytest.param(
            MULTILINE_YAML,
            5,
            5,
            "replaced line 5",
            ["Successfully replaced", "1 line(s)"],
            {3: "line 4", 4: "replaced line 5", 5: "line 6"},
            True,
            id="replace_single_line",
        ),
        pytest.param(
            MULTILINE_YAML,
            5,
            8,
            "replacement line 1\nreplacement line 2",
            ["Successfully replaced", "4 line(s)", "2 new line(s)"],
            {4: "replacement line 1", 5: "replacement line 2", 6: "line 9"},
            True,
            id="replace_multiple_lines",
        ),
        pytest.param(
            SAMPLE_YAML,
            1,
            2,
            "# New header",
            ["Successfully replaced"],
            {0: "# New header", 1: 'description: "A test connector"'},
            True,
            id="replace_at_beginning",
        ),
        pytest.param(
            MULTILINE_YAML,
            19,
            20,
            "# End lines replaced",
            ["Successfully replaced"],
            {},
            True,
            id="replace_at_end",
        ),
        pytest.param(
            MULTILINE_YAML,
            10,
            15,
            "",
            ["Successfully replaced"],
            {9: "line 16"},
            True,
            id="replace_with_empty_string",
        ),
        pytest.param(
            SAMPLE_YAML,
            100,
            101,
            "content",
            ["Error: start_line", "out of range"],
            {},
            False,
            id="invalid_start_line",
        ),
        pytest.param(
            SAMPLE_YAML,
            5,
            3,
            "content",
            ["Error: end_line", "before start_line"],
            {},
            False,
            id="end_before_start",
        ),
        pytest.param(
            SAMPLE_YAML,
            1,
            100,
            "content",
            ["Error: end_line", "out of range"],
            {},
            False,
            id="invalid_end_line",
        ),
        pytest.param(
            "",
            1,
            2,
            "content",
            ["Error: No YAML content available"],
            {},
            False,
            id="no_content",
        ),
    ],
)
def test_replace_manifest_lines(
    yaml_content,
    start_line,
    end_line,
    new_lines,
    expected_in_result,
    expected_at_line,
    should_modify,
):
    """Test replace_manifest_lines with various parameters and edge cases."""
    ctx = create_mock_ctx(yaml_content)
    original_content = yaml_content
    result = replace_manifest_lines(ctx, start_line, end_line, new_lines)

    for expected in expected_in_result:
        assert expected in result

    if should_modify:
        assert ctx.deps.yaml_content != original_content
        lines = ctx.deps.yaml_content.split("\n")
        for line_idx, expected_text in expected_at_line.items():
            assert expected_text in lines[line_idx]
    else:
        assert ctx.deps.yaml_content == original_content
