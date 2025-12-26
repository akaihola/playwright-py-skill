"""Tests for Basic Browser Automation example from API_REFERENCE.md."""

import os
import re
import pytest
from playwright.sync_api import sync_playwright


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
        # Get the path to API_REFERENCE.md
        api_ref_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "skills",
            "playwright-py-skill",
            "API_REFERENCE.md",
        )

        # Read API_REFERENCE.md to extract the Basic Browser Automation example
        with open(api_ref_path, "r") as f:
            content = f.read()

        # Extract the Basic Browser Automation code block
        # Looking for the section between "### Basic Browser Automation" and the next section
        pattern = r"### Basic Browser Automation\s*```python\s*(.*?)```"
        match = re.search(pattern, content, re.DOTALL)

        assert match, "Basic Browser Automation example not found in API_REFERENCE.md"
        extracted_code = match.group(1)

        # Verify we extracted the expected code
        assert "sync_playwright" in extracted_code
        assert "chromium.launch" in extracted_code
        assert "new_context" in extracted_code
        assert "new_page" in extracted_code
        assert "goto" in extracted_code

        # Modify the extracted code for testing:
        # 1. Replace headless=False with headless=True for CI
        # 2. Replace https://example.com with test_server_url
        # 3. Replace "# Your automation here" with assertions
        modified_code = (
            extracted_code.replace(
                "headless=False,  # Set to True for headless mode", "headless=True,"
            )
            .replace(
                'page.goto("https://example.com", wait_until="networkidle")',
                f'page.goto("{test_server_url}", wait_until="networkidle")',
            )
            .replace(
                "# Your automation here",
                f"""# Test assertions
    assert browser is not None
    assert browser.is_connected()
    assert context is not None
    assert page is not None
    viewport_size = page.viewport_size
    assert viewport_size["width"] == 1280
    assert viewport_size["height"] == 720
    assert page.url.rstrip("/") == "{test_server_url.rstrip("/")}"
    assert "Welcome" in page.content() or "Example Domain" in page.content()""",
            )
        )

        # Execute the modified code
        exec(
            modified_code,
            {"sync_playwright": sync_playwright, "test_server_url": test_server_url},
        )

    def test_basic_browser_automation_external_url(self):
        """Test Basic Browser Automation example with external URL.

        This version uses https://example.com to demonstrate the example
        works with external URLs as documented.
        """
        # Get the path to API_REFERENCE.md
        api_ref_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "skills",
            "playwright-py-skill",
            "API_REFERENCE.md",
        )

        # Read API_REFERENCE.md to extract the Basic Browser Automation example
        with open(api_ref_path, "r") as f:
            content = f.read()

        # Extract the Basic Browser Automation code block
        pattern = r"### Basic Browser Automation\s*```python\s*(.*?)```"
        match = re.search(pattern, content, re.DOTALL)

        assert match, "Basic Browser Automation example not found in API_REFERENCE.md"
        extracted_code = match.group(1)

        # Modify the extracted code for testing:
        # 1. Replace headless=False with headless=True for CI
        # 2. Replace "# Your automation here" with assertions
        modified_code = extracted_code.replace(
            "headless=False,  # Set to True for headless mode", "headless=True,"
        ).replace(
            "# Your automation here",
            """# Test assertions
    assert browser is not None
    assert browser.is_connected()
    assert context is not None
    assert page is not None
    viewport_size = page.viewport_size
    assert viewport_size["width"] == 1280
    assert viewport_size["height"] == 720
    assert page.url == "https://example.com/"
    assert "Example Domain" in page.content()""",
        )

        # Execute the modified code
        exec(modified_code, {"sync_playwright": sync_playwright})
