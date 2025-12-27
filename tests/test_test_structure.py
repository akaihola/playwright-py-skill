"""Tests for Test Structure pattern from API_REFERENCE.md."""

import re
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, expect


def extract_test_structure_code():
    """Extract Test Structure example from API_REFERENCE.md.

    Returns:
        Modified code ready for execution with test assertions
    """
    api_ref_path = (
        Path(__file__).parent.parent
        / "skills"
        / "playwright-py-skill"
        / "API_REFERENCE.md"
    )

    content = api_ref_path.read_text()

    pattern = r"### Test Structure\s*```python\s*(.*?)```"
    match = re.search(pattern, content, re.DOTALL)

    assert match, "Test Structure example not found in API_REFERENCE.md"
    extracted_code = match.group(1)

    # Verify we extracted the expected code
    assert "Page" in extracted_code
    assert "expect" in extracted_code
    assert 'data-testid="submit-button"' in extracted_code
    assert "to_have_url" in extracted_code
    assert "to_have_text" in extracted_code

    return extracted_code


class TestTestStructure:
    """Tests for the Test Structure pattern (arrange-act-assert)."""

    def test_test_structure_pattern(self, test_server_url):
        """Test Test Structure example from API_REFERENCE.md.

        This test:
        - Extracts code from API_REFERENCE.md at runtime
        - Modifies the extracted code to use test server
        - Evaluates the modified code
        - Verifies arrange-act-assert pattern works correctly
        - Verifies URL changes to /success
        - Verifies success message appears
        """
        extracted_code = extract_test_structure_code()

        # Modify the extracted code to use test server URL
        modified_code = extracted_code.replace(
            'page.goto("/")',
            f'page.goto("{test_server_url}/contact")',
        )

        # Update URL assertion to use full URL
        modified_code = modified_code.replace(
            'expect(page).to_have_url("/success")',
            f'expect(page).to_have_url("{test_server_url}/success")',
        )

        # Execute the modified code to define the test function
        ns = {"sync_playwright": sync_playwright, "Page": Page, "expect": expect}
        exec(modified_code, ns)
        test_feature_name = ns["test_feature_name"]

        # Execute the test function with a page fixture
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            try:
                test_feature_name(page)
            finally:
                browser.close()
