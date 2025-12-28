"""Tests for Test Structure pattern from API_REFERENCE.md."""

from playwright.sync_api import sync_playwright, Page, expect
from conftest import extract_markdown_code


def extract_test_structure_code():
    """Extract Test Structure example from API_REFERENCE.md.

    Returns:
        Modified code ready for execution with test assertions
    """
    return extract_markdown_code(
        "Test Structure",
        expected_substrings=[
            "Page",
            "expect",
            'data-testid="submit-button"',
            "to_have_url",
            "to_have_text",
        ],
    )


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
