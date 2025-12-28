"""Tests for Basic Browser Automation example from API_REFERENCE.md."""

from playwright.sync_api import sync_playwright
from conftest import extract_markdown_code, set_indent


def extract_basic_browser_automation_code(test_server_url=None):
    """Extract Basic Browser Automation example from API_REFERENCE.md.

    Args:
        test_server_url: Optional URL to replace example.com with

    Returns:
        Modified code ready for execution with test assertions
    """
    extracted_code = extract_markdown_code(
        "Basic Browser Automation",
        expected_substrings=[
            "sync_playwright",
            "chromium.launch",
            "new_context",
            "new_page",
            "goto",
        ],
    )

    # Modify the extracted code for testing:
    # 1. Replace headless=False with headless=True for CI
    # 2. Replace https://example.com with test_server_url if provided
    # 3. Replace "# Your automation here" with assertions
    modified_code = extracted_code.replace(
        "headless=False,  # Set to True for headless mode", "headless=True,"
    )

    if test_server_url:
        modified_code = modified_code.replace(
            'page.goto("https://example.com", wait_until="networkidle")',
            f'page.goto("{test_server_url}", wait_until="networkidle")',
        )

    return modified_code


class TestBasicBrowserAutomation:
    """Tests for the Basic Browser Automation example."""

    def test_basic_browser_automation(self, test_server_url):
        """Test Basic Browser Automation example from API_REFERENCE.md.

        This test:
        - Extracts code from API_REFERENCE.md at runtime
        - Modifies and evaluates the extracted code
        - Verifies browser launches without errors
        - Verifies context is created with correct viewport
        - Verifies page navigates successfully
        - Runs with headless=True (for CI)
        - Uses test server instead of external URL
        """
        modified_code = extract_basic_browser_automation_code(test_server_url)

        modified_code = modified_code.replace(
            "# Your automation here",
            set_indent(
                f"""
                # Test assertions
                assert browser is not None
                assert browser.is_connected()
                assert context is not None
                assert page is not None
                viewport_size = page.viewport_size
                assert viewport_size["width"] == 1280
                assert viewport_size["height"] == 720
                assert page.url.rstrip("/") == "{test_server_url.rstrip("/")}"
                assert "Welcome" in page.content() or "Example Domain" in page.content()
                """
            ),
        )

        exec(
            modified_code,
            {"sync_playwright": sync_playwright, "test_server_url": test_server_url},
        )

    def test_basic_browser_automation_external_url(self):
        """Test Basic Browser Automation example with external URL.

        This version uses https://example.com to demonstrate the example
        works with external URLs as documented.
        """
        modified_code = extract_basic_browser_automation_code()

        modified_code = modified_code.replace(
            "# Your automation here",
            set_indent(
                """
                # Test assertions
                assert browser is not None
                assert browser.is_connected()
                assert context is not None
                assert page is not None
                viewport_size = page.viewport_size
                assert viewport_size["width"] == 1280
                assert viewport_size["height"] == 720
                assert page.url == "https://example.com/"
                assert "Example Domain" in page.content()
                """
            ),
        )

        exec(modified_code, {"sync_playwright": sync_playwright})
