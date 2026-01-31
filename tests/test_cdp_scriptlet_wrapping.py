"""Tests for CDP scriptlet wrapping in run_cdp_scriptlet()."""

import ast
import sys
import tempfile
from pathlib import Path
from textwrap import dedent, indent
from unittest.mock import MagicMock, Mock, patch

import pytest

# Import the function under test by adding the skill dir to sys.path
skill_dir = Path(__file__).parent.parent / "skills" / "playwright-py-skill"
if str(skill_dir) not in sys.path:
    sys.path.insert(0, str(skill_dir))

from run import run_cdp_scriptlet


class TestRunCdpScriptletWrapping:
    """Test suite for CDP scriptlet wrapping and code execution."""

    @pytest.fixture
    def mock_execute_code(self, monkeypatch):
        """Mock execute_code_as_module to avoid actual execution."""
        mock = Mock()
        monkeypatch.setattr("run.execute_code_as_module", mock)
        return mock

    @pytest.mark.parametrize(
        "user_code,expected_indentation",
        [
            pytest.param(
                "print('hello')",
                4,
                id="simple_single_line",
            ),
            pytest.param(
                dedent(
                    """\
                import time
                time.sleep(1)
                print('done')
                """
                ),
                4,
                id="multiline_no_leading_newline",
            ),
            pytest.param(
                dedent(
                    """\

                import time
                time.sleep(1)
                print('done')
                """
                ),
                4,
                id="multiline_with_leading_newline",
            ),
            pytest.param(
                """
x = 1
y = 2
result = x + y
print(result)
                """,
                4,
                id="multiline_with_leading_and_trailing_whitespace",
            ),
        ],
    )
    def test_scriptlet_wrapping_produces_valid_syntax(
        self, mock_execute_code, user_code, expected_indentation
    ):
        """Test that wrapped code is syntactically valid regardless of leading/trailing whitespace.

        This test:
        - Extracts the wrapped code from the mock call
        - Parses it as valid Python AST
        - Verifies that the user code lines are properly indented
        """
        port = 9222
        run_cdp_scriptlet(user_code, port)

        # Get the wrapped code that was passed to execute_code_as_module
        assert mock_execute_code.called, "execute_code_as_module should be called"
        wrapped_code = mock_execute_code.call_args[0][0]

        # Verify it's valid Python syntax
        try:
            ast.parse(wrapped_code)
        except SyntaxError as e:
            pytest.fail(
                f"Wrapped code has syntax error at line {e.lineno}: {e.msg}\n"
                f"Wrapped code:\n{wrapped_code}"
            )

        # Verify the structure includes expected imports and try/finally
        assert "from playwright.sync_api import sync_playwright" in wrapped_code
        assert "try:" in wrapped_code
        assert "finally:" in wrapped_code
        assert "p.stop()" in wrapped_code
        assert f"localhost:{port}" in wrapped_code

    def test_scriptlet_wrapping_with_leading_newline(self, mock_execute_code):
        """Test that leading newlines in user code don't cause IndentationError.

        Regression test for Error 1: IndentationError when using --cdp with
        multiline inline code starting with \\n.
        """
        user_code = """
print("Title:", page.title())
print("URL:", page.url)
        """
        port = 9222

        run_cdp_scriptlet(user_code, port)

        wrapped_code = mock_execute_code.call_args[0][0]

        # Parse to verify valid syntax
        try:
            ast.parse(wrapped_code)
        except SyntaxError as e:
            pytest.fail(f"Wrapped code with leading newline failed: {e.msg}")

        # Verify user code lines are properly indented (4 spaces for try block)
        lines = wrapped_code.split("\n")
        user_code_lines = [
            l for l in lines if "print(" in l and "Title" in l or "URL" in l
        ]
        for line in user_code_lines:
            if line.strip():  # Ignore blank lines
                # Should be indented by 4 spaces (try block level)
                assert line.startswith("    "), (
                    f"User code should be indented by 4 spaces for try block, "
                    f"got: {repr(line)}"
                )

    def test_scriptlet_wrapping_preserves_user_code_logic(self, mock_execute_code):
        """Test that user code logic is preserved in the wrapped version.

        The wrapped code should include the exact user code (after stripping
        leading/trailing whitespace) indented correctly.
        """
        user_code = dedent(
            """\
        x = 42
        y = x * 2
        assert y == 84, f"Expected 84, got {y}"
        print(f"Success: {y}")
        """
        )

        run_cdp_scriptlet(user_code, 9222)

        wrapped_code = mock_execute_code.call_args[0][0]

        # User code should be present and properly formatted
        assert "x = 42" in wrapped_code
        assert "y = x * 2" in wrapped_code
        assert "assert y == 84" in wrapped_code
        assert 'print(f"Success: {y}")' in wrapped_code

    def test_scriptlet_wrapping_indentation_consistency(self, mock_execute_code):
        """Test that all user code lines have consistent base indentation.

        Top-level lines of the user code should be indented by exactly 4 spaces
        (the try block level). Nested lines (inside functions, loops, etc.)
        will have additional indentation.
        """
        user_code = dedent(
            """\
        def helper():
            return "value"

        result = helper()
        print(result)
        """
        )

        run_cdp_scriptlet(user_code, 9222)

        wrapped_code = mock_execute_code.call_args[0][0]
        lines = wrapped_code.split("\n")

        # Find the try block and check subsequent lines until finally
        try_index = None
        finally_index = None
        for i, line in enumerate(lines):
            if line.strip() == "try:":
                try_index = i
            elif line.strip() == "finally:":
                finally_index = i

        assert try_index is not None, "try: block not found in wrapped code"
        assert finally_index is not None, "finally: block not found in wrapped code"

        # Check that top-level code (def, result, print) has at least 4 spaces
        # and that the user code structure is preserved
        found_def = False
        found_result = False
        found_print = False

        for i in range(try_index + 1, finally_index):
            line = lines[i]
            if line.strip().startswith("def helper"):
                found_def = True
                assert line.startswith(
                    "    "
                ), f"Top-level def should be indented by 4 spaces, got: {repr(line)}"
            elif line.strip().startswith("result = helper"):
                found_result = True
                assert line.startswith(
                    "    "
                ), f"Top-level assignment should be indented by 4 spaces, got: {repr(line)}"
            elif line.strip().startswith("print(result"):
                found_print = True
                assert line.startswith(
                    "    "
                ), f"Top-level print should be indented by 4 spaces, got: {repr(line)}"

        assert found_def, "def helper() not found in wrapped code"
        assert found_result, "result = helper() not found in wrapped code"
        assert found_print, "print(result) not found in wrapped code"

    @pytest.mark.parametrize(
        "user_code",
        [
            "x = 1",
            "  x = 1",  # Pre-indented
            "\nx = 1",  # Leading newline
            "x = 1\n",  # Trailing newline
            "\n\nx = 1\n\n",  # Multiple leading/trailing newlines
        ],
    )
    def test_scriptlet_wrapping_handles_whitespace_variants(
        self, mock_execute_code, user_code
    ):
        """Test that various whitespace patterns don't break the wrapping.

        Parameterized test with different whitespace patterns to ensure
        robustness against user code formatting variations.
        """
        run_cdp_scriptlet(user_code, 9222)

        wrapped_code = mock_execute_code.call_args[0][0]

        # Should always produce valid syntax
        try:
            ast.parse(wrapped_code)
        except SyntaxError as e:
            pytest.fail(f"Failed to parse with input {repr(user_code)}: {e.msg}")

    def test_scriptlet_wrapping_port_in_connection_string(self, mock_execute_code):
        """Test that the specified port is used in the CDP connection string."""
        user_code = "print('test')"

        # Test with default port
        run_cdp_scriptlet(user_code, 9222)
        wrapped_code = mock_execute_code.call_args[0][0]
        assert "localhost:9222" in wrapped_code

        # Test with custom port
        mock_execute_code.reset_mock()
        run_cdp_scriptlet(user_code, 12345)
        wrapped_code = mock_execute_code.call_args[0][0]
        assert "localhost:12345" in wrapped_code

    def test_scriptlet_wrapping_calls_execute_code_as_module(self, mock_execute_code):
        """Test that execute_code_as_module is called with the wrapped code."""
        user_code = "x = 1"

        run_cdp_scriptlet(user_code, 9222)

        # Should be called exactly once with the wrapped code
        mock_execute_code.assert_called_once()
        args, kwargs = mock_execute_code.call_args
        assert len(args) == 1, "Should be called with exactly one positional argument"
        assert isinstance(args[0], str), "Argument should be a string"
        assert len(args[0]) > len(user_code), "Wrapped code should be longer than input"

    def test_scriptlet_wrapping_with_playwright_api_calls(self, mock_execute_code):
        """Test that user code with Playwright API calls is properly wrapped."""
        user_code = dedent(
            """\
        # Handle cookie banner if present
        try:
            btn = page.locator("button").filter(has_text="Accept")
            btn.click()
        except:
            pass

        page.goto("https://example.com")
        title = page.title()
        print(f"Title: {title}")
        """
        )

        run_cdp_scriptlet(user_code, 9222)

        wrapped_code = mock_execute_code.call_args[0][0]

        # Verify code structure
        assert "from playwright.sync_api import sync_playwright" in wrapped_code
        assert "page.locator" in wrapped_code
        assert "page.goto" in wrapped_code
        assert "page.title()" in wrapped_code

        # Verify it's valid syntax
        try:
            ast.parse(wrapped_code)
        except SyntaxError as e:
            pytest.fail(f"Playwright API code failed to parse: {e.msg}")

    def test_scriptlet_wrapping_finally_block_always_present(self, mock_execute_code):
        """Test that finally block with p.stop() is always present."""
        user_code = "raise Exception('test error')"

        run_cdp_scriptlet(user_code, 9222)

        wrapped_code = mock_execute_code.call_args[0][0]

        # Should have try/finally structure to ensure cleanup
        assert "try:" in wrapped_code
        assert "finally:" in wrapped_code
        assert "p.stop()" in wrapped_code

        # The finally block should be at the correct indentation (0 spaces)
        lines = wrapped_code.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("finally:"):
                # finally should be at column 0
                assert (
                    line == "finally:"
                ), f"finally: should be at column 0, got: {repr(line)}"
                # p.stop() should be indented by 4 spaces
                assert i + 1 < len(lines), "There should be code after finally:"
                next_line = lines[i + 1]
                assert (
                    "p.stop()" in next_line or next_line.strip() == ""
                ), f"Expected p.stop() after finally, got: {repr(next_line)}"
