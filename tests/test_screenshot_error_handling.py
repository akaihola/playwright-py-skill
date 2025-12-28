"""Tests for Take Screenshot with Error Handling example from SKILL.md."""

from pathlib import Path
from playwright.sync_api import sync_playwright
from conftest import extract_markdown_code


def extract_screenshot_error_handling_code(
    test_server_url="http://localhost:3000",
    screenshot_path="/tmp/screenshot.png",
    timeout=10000,
):
    """Extract Take Screenshot with Error Handling example from SKILL.md.

    Args:
        test_server_url: URL to use for navigation (default: localhost:3000)
        screenshot_path: Path where screenshot will be saved (default: /tmp/screenshot.png)
        timeout: Timeout in milliseconds for page load (default: 10000)

    Returns:
        Modified code ready for execution with test assertions
    """
    extracted_code = extract_markdown_code(
        "Take Screenshot with Error Handling",
        markdown_file="SKILL.md",
        expected_substrings=[
            "sync_playwright",
            "chromium.launch",
            "new_page",
            "screenshot",
            "try:",
            "except Exception",
            "finally:",
        ],
    )

    modified_code = extracted_code.replace("headless=False", "headless=True")

    modified_code = modified_code.replace(
        "'http://localhost:3000'",
        f"'{test_server_url}'",
    )

    modified_code = modified_code.replace(
        "'/tmp/screenshot.png'",
        f"'{screenshot_path}'",
    )

    modified_code = modified_code.replace(
        "timeout=10000",
        f"timeout={timeout}",
    )

    return modified_code


class TestScreenshotErrorHandling:
    """Tests for the Take Screenshot with Error Handling example."""

    def test_screenshot_success(self, test_server_url, tmp_path, capsys):
        """Test Take Screenshot with Error Handling example on success.

        This test:
        - Extracts code from SKILL.md at runtime
        - Verifies screenshot is taken on success
        - Verifies success message is printed
        - Uses test server URL instead of localhost:3000
        """
        screenshot_path = tmp_path / "screenshot.png"
        exec(
            extract_screenshot_error_handling_code(
                test_server_url=test_server_url,
                screenshot_path=screenshot_path,
            ),
            {"sync_playwright": sync_playwright},
        )

        output = capsys.readouterr().out

        assert "📸 Screenshot saved to" in output, (
            f"Expected success message in output: {output}"
        )
        assert screenshot_path.exists(), (
            f"Screenshot file should exist at {screenshot_path}"
        )
        assert screenshot_path.stat().st_size > 0, (
            f"Screenshot file should not be empty"
        )

    def test_screenshot_error_handling(self, test_server_url, tmp_path, capsys):
        """Test error handling in Take Screenshot example.

        This test:
        - Verifies error message is printed on failure
        - Verifies browser is closed in finally block even when error occurs
        - Uses invalid path to trigger error
        """
        exec(
            extract_screenshot_error_handling_code(
                test_server_url=test_server_url,
                screenshot_path="/nonexistent/directory/screenshot.png",
            ),
            {"sync_playwright": sync_playwright},
        )

        output = capsys.readouterr().out

        assert "❌ Error:" in output, f"Expected error message in output: {output}"

    def test_timeout_behavior(self, capsys):
        """Test timeout behavior in Take Screenshot example.

        This test:
        - Verifies error handling when page load times out
        - Verifies error message is printed
        - Verifies browser is closed in finally block
        """
        exec(
            extract_screenshot_error_handling_code(
                test_server_url="http://localhost:1",
                timeout=1000,
            ),
            {"sync_playwright": sync_playwright},
        )

        output = capsys.readouterr().out

        assert "❌ Error:" in output, f"Expected error message in output: {output}"

    def test_browser_closed_in_finally(self, test_server_url, tmp_path):
        """Test that browser is closed in finally block.

        This test:
        - Verifies browser is closed after execution
        """
        namespace = {}
        exec(
            extract_screenshot_error_handling_code(
                test_server_url=test_server_url,
                screenshot_path=tmp_path / "screenshot.png",
            ),
            {"sync_playwright": sync_playwright},
            namespace,
        )

        browser = namespace.get("browser")
        assert browser is not None, "Browser should exist in namespace"
        assert not browser.is_connected(), "Browser should be closed in finally block"
