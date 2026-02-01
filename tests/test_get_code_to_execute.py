"""Tests for get_code_to_execute() inline vs file-path detection."""

import sys
from pathlib import Path
from textwrap import dedent

import pytest

skill_dir = Path(__file__).parent.parent / "skills" / "playwright-py-skill"
if str(skill_dir) not in sys.path:
    sys.path.insert(0, str(skill_dir))

from run import get_code_to_execute


class TestInlineCodeDetection:
    """Ensure multiline inline code is not misidentified as a file path."""

    def test_multiline_inline_code_with_slash(self):
        """Inline code containing '/' should not be treated as a file path."""
        code = dedent(
            """\
            import time
            # navigate to /forecast
            print(page.title())"""
        )
        result = get_code_to_execute([code])
        assert result == code

    def test_multiline_inline_code_with_dotpy(self):
        """Inline code containing '.py' should not be treated as a file path."""
        code = dedent(
            """\
            # like script.py does
            print("hello")"""
        )
        result = get_code_to_execute([code])
        assert result == code

    def test_long_inline_code_without_newlines(self):
        """Long single-line inline code (>255 chars) should be treated as code."""
        code = "x = 1; " * 50  # >255 chars
        result = get_code_to_execute([code])
        assert result == code

    def test_short_file_path_not_found(self, tmp_path):
        """A short path-like string that doesn't exist should error."""
        with pytest.raises(SystemExit):
            get_code_to_execute(["/tmp/nonexistent_script.py"])

    def test_existing_file_is_read(self, tmp_path):
        """An existing .py file path should be read."""
        f = tmp_path / "test_script.py"
        f.write_text("print('hello')\n")
        result = get_code_to_execute([str(f)])
        assert result == "print('hello')\n"

    def test_simple_inline_code(self):
        """Simple inline code without path-like chars works."""
        result = get_code_to_execute(["print('hello')"])
        assert result == "print('hello')"


class TestStdinDash:
    """Ensure '-' argument reads code from stdin."""

    def test_dash_reads_from_stdin(self, monkeypatch):
        """'--cdp -' should read code from stdin."""
        from io import StringIO

        monkeypatch.setattr("sys.stdin", StringIO('print("hello")\n'))
        result = get_code_to_execute(["-"])
        assert result == 'print("hello")\n'

    def test_dash_reads_multiline_from_stdin(self, monkeypatch):
        """'--cdp -' should read multiline code from stdin (heredoc use case)."""
        from io import StringIO

        code = 'import time\npage.click("button")\nprint(f"Title: {page.title()}")\n'
        monkeypatch.setattr("sys.stdin", StringIO(code))
        result = get_code_to_execute(["-"])
        assert result == code

    def test_dash_takes_precedence_over_file(self, tmp_path, monkeypatch):
        """'-' should read stdin even if a file named '-' somehow exists."""
        from io import StringIO

        monkeypatch.setattr("sys.stdin", StringIO("from_stdin\n"))
        result = get_code_to_execute(["-"])
        assert result == "from_stdin\n"
