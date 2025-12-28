"""Tests for Test a Page (Multiple Viewports) example from SKILL.md."""

from pathlib import Path
from textwrap import dedent
from playwright.sync_api import sync_playwright
from conftest import extract_markdown_code


def extract_multiple_viewports_code():
    """Extract Test a Page (Multiple Viewports) example from SKILL.md.

    Returns:
        Modified code ready for execution with test assertions
    """
    return extract_markdown_code(
        "Test a Page (Multiple Viewports)",
        markdown_file="SKILL.md",
        expected_substrings=[
            "sync_playwright",
            "set_viewport_size",
            "screenshot",
            "page.title()",
        ],
    )


class TestMultipleViewports:
    """Tests for the Test a Page (Multiple Viewports) example."""

    def test_multiple_viewports(self, test_server_url):
        """Test Test a Page (Multiple Viewports) example from SKILL.md.

        This test:
        - Extracts code from SKILL.md at runtime
        - Modifies and evaluates the extracted code
        - Verifies desktop viewport (1920x1080)
        - Verifies mobile viewport (375x667)
        - Verifies screenshots are taken at each viewport
        - Verifies page title is retrieved
        - Runs with headless=True (for CI)
        - Uses test server instead of external URL
        """
        modified_code = extract_multiple_viewports_code()
        lines = modified_code.split("\n")
        modified = False

        for i, line in enumerate(lines):
            if not line.strip():
                continue

            # Replace headless=False, slow_mo=100 with headless=True for CI
            if "headless=False, slow_mo=100" in line:
                lines[i] = line.replace("headless=False, slow_mo=100", "headless=True")
                modified = True

            # Replace 'http://localhost:3001' with test_server_url
            elif "http://localhost:3001" in line:
                lines[i] = line.replace("http://localhost:3001", test_server_url)
                modified = True

            # Insert variable declarations after page = browser.new_page()
            elif "page = browser.new_page()" in line:
                lines[i] = "    " + dedent(
                    """\
                    page = browser.new_page()
                    desktop_path = Path('/tmp/desktop.png')
                    mobile_path = Path('/tmp/mobile.png')

                    # Clean up any existing screenshots
                    for path in [desktop_path, mobile_path]:
                        if path.exists():
                            path.unlink()"""
                ).replace("\n", "\n    ")
                modified = True

            # Add assertions after desktop screenshot
            elif "page.screenshot(path='/tmp/desktop.png', full_page=True)" in line:
                lines[i] = "    " + dedent(
                    """\
                    page.screenshot(path=desktop_path, full_page=True)
                    # Test assertions for desktop
                    assert page.viewport_size["width"] == 1920
                    assert page.viewport_size["height"] == 1080
                    assert desktop_path.exists()
                    desktop_title = page.title()
                    assert desktop_title is not None
                    assert len(desktop_title) > 0"""
                ).replace("\n", "\n    ")
                modified = True

            # Add assertions after mobile screenshot
            elif "page.screenshot(path='/tmp/mobile.png', full_page=True)" in line:
                lines[i] = "    " + dedent(
                    """\
                    page.screenshot(path=mobile_path, full_page=True)
                    # Test assertions for mobile
                    assert page.viewport_size["width"] == 375
                    assert page.viewport_size["height"] == 667
                    assert mobile_path.exists()
                    # Verify title still works after viewport change
                    mobile_title = page.title()
                    assert mobile_title is not None
                    assert len(mobile_title) > 0"""
                ).replace("\n", "\n    ")
                modified = True

        # Fail if no replacements were made (example code changed unexpectedly)
        assert modified, "No matching lines found - example code may have changed"

        modified_code = "\n".join(lines)
        exec(
            modified_code,
            {
                "sync_playwright": sync_playwright,
                "test_server_url": test_server_url,
                "Path": Path,
            },
        )
