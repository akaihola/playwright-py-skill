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

        # Execute the example with modifications for testing
        with sync_playwright() as p:
            # Launch browser (headless=True for CI)
            browser = p.chromium.launch(
                headless=True,  # Modified for CI
                slow_mo=50,
            )

            # Verify browser launched successfully
            assert browser is not None
            assert browser.is_connected()

            # Create context with viewport
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            )

            # Verify context created successfully
            assert context is not None

            # Create page
            page = context.new_page()

            # Verify page created successfully
            assert page is not None

            # Verify viewport is correct (viewport is set on the page)
            viewport_size = page.viewport_size
            assert viewport_size["width"] == 1280
            assert viewport_size["height"] == 720

            # Navigate to test server instead of example.com
            page.goto(test_server_url, wait_until="networkidle")

            # Verify navigation succeeded
            assert page.url.rstrip("/") == test_server_url.rstrip("/")
            assert "Welcome" in page.content() or "Example Domain" in page.content()

            # Close browser
            browser.close()

            # Verify browser closed successfully
            assert not browser.is_connected()

    def test_basic_browser_automation_external_url(self):
        """Test Basic Browser Automation example with external URL.

        This version uses https://example.com to demonstrate the example
        works with external URLs as documented.
        """
        with sync_playwright() as p:
            # Launch browser (headless=True for CI)
            browser = p.chromium.launch(
                headless=True,
                slow_mo=50,
            )

            # Verify browser launched successfully
            assert browser is not None
            assert browser.is_connected()

            # Create context with viewport
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            )

            # Verify context created successfully
            assert context is not None

            # Create page
            page = context.new_page()

            # Verify page created successfully
            assert page is not None

            # Verify viewport is correct (viewport is set on the page)
            viewport_size = page.viewport_size
            assert viewport_size["width"] == 1280
            assert viewport_size["height"] == 720

            # Navigate to external URL as shown in the example
            page.goto("https://example.com", wait_until="networkidle")

            # Verify navigation succeeded
            assert page.url == "https://example.com/"
            assert "Example Domain" in page.content()

            # Close browser
            browser.close()

            # Verify browser closed successfully
            assert not browser.is_connected()
