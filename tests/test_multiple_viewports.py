"""Tests for Test a Page (Multiple Viewports) example from SKILL.md."""

import re
from pathlib import Path
from playwright.sync_api import sync_playwright


def extract_multiple_viewports_code():
    """Extract Test a Page (Multiple Viewports) example from SKILL.md.

    Returns:
        Modified code ready for execution with test assertions
    """
    skill_path = (
        Path(__file__).parent.parent / "skills" / "playwright-py-skill" / "SKILL.md"
    )

    content = skill_path.read_text()

    pattern = r"### Test a Page \(Multiple Viewports\)\s*```python\s*(.*?)```"
    match = re.search(pattern, content, re.DOTALL)

    assert match, "Test a Page (Multiple Viewports) example not found in SKILL.md"
    extracted_code = match.group(1)

    # Verify we extracted the expected code
    assert "sync_playwright" in extracted_code
    assert "set_viewport_size" in extracted_code
    assert "screenshot" in extracted_code
    assert "page.title()" in extracted_code

    return extracted_code


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

        # Modify the extracted code for testing:
        # 1. Replace headless=False, slow_mo=100 with headless=True for CI
        # 2. Replace 'http://localhost:3001' with test_server_url
        # 3. Add assertions to verify viewport sizes, screenshots, and title
        modified_code = modified_code.replace(
            "browser = p.chromium.launch(headless=False, slow_mo=100)",
            "browser = p.chromium.launch(headless=True)",
        )

        modified_code = modified_code.replace(
            "TARGET_URL = 'http://localhost:3001'  # Auto-detected",
            f"TARGET_URL = '{test_server_url}'  # Auto-detected",
        )

        # Insert variable declarations after the new_page() line
        modified_code = modified_code.replace(
            "    page = browser.new_page()",
            """    page = browser.new_page()
    import os
    desktop_path = '/tmp/desktop.png'
    mobile_path = '/tmp/mobile.png'
    
    # Clean up any existing screenshots
    for path in [desktop_path, mobile_path]:
        if os.path.exists(path):
            os.remove(path)""",
        )

        # Add assertions after desktop screenshot
        modified_code = modified_code.replace(
            "    page.screenshot(path='/tmp/desktop.png', full_page=True)",
            """    page.screenshot(path=desktop_path, full_page=True)
    # Test assertions for desktop
    assert page.viewport_size["width"] == 1920
    assert page.viewport_size["height"] == 1080
    assert os.path.exists(desktop_path)
    desktop_title = page.title()
    assert desktop_title is not None
    assert len(desktop_title) > 0""",
        )

        # Add assertions after mobile screenshot
        modified_code = modified_code.replace(
            "    page.screenshot(path='/tmp/mobile.png', full_page=True)",
            """    page.screenshot(path=mobile_path, full_page=True)
    # Test assertions for mobile
    assert page.viewport_size["width"] == 375
    assert page.viewport_size["height"] == 667
    assert os.path.exists(mobile_path)
    # Verify title still works after viewport change
    mobile_title = page.title()
    assert mobile_title is not None
    assert len(mobile_title) > 0""",
        )

        exec(
            modified_code,
            {"sync_playwright": sync_playwright, "test_server_url": test_server_url},
        )
