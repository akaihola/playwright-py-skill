"""Tests for Selectors & Locators examples from API_REFERENCE.md."""

import re as python_re
from playwright.sync_api import sync_playwright

from conftest import extract_markdown_code, get_action_log


def extract_selectors_locators_code():
    """Extract Selectors & Locators examples from API_REFERENCE.md.

    Returns:
        Tuple of (best_practices_code, advanced_patterns_code)
    """
    best_practices_code = extract_markdown_code("Best Practices for Selectors")
    advanced_patterns_code = extract_markdown_code("Advanced Locator Patterns")

    return best_practices_code, advanced_patterns_code


class TestSelectorsAndLocators:
    """Tests for Selectors & Locators examples."""

    def test_selectors_locators_examples(self, test_server_url):
        """Test Selectors & Locators examples from API_REFERENCE.md.

        This test:
        - Extracts code from API_REFERENCE.md at runtime
        - Executes selector patterns on test page
        - Verifies actions are logged correctly via action log element
        - Tests all selector strategies: data attributes, role-based, text, semantic, advanced
        """
        best_practices_code, advanced_patterns_code = extract_selectors_locators_code()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto(f"{test_server_url}/selectors")

            # Wait for action log to be ready
            page.locator("#action-log").wait_for(state="visible")

            # Execute Best Practices code from API_REFERENCE.md
            exec(best_practices_code, {"page": page, "re": python_re})

            # Modify advanced_patterns_code to add count logging after the count line
            count_logging_code = "page.locator('#action-log').evaluate('(el, c) => el.textContent += \"count disabled-buttons \" + c + \"\\\\n\"', nth_page.locator('button').and_(nth_page.locator('[disabled]')).count())\n"
            modified_advanced_code = advanced_patterns_code.replace(
                "nth_page.locator('button').and_(nth_page.locator('[disabled]')).count()\n\n# Parent/child navigation",
                count_logging_code + "# Parent/child navigation",
            )

            # Execute Advanced Locator Patterns from API_REFERENCE.md
            exec(modified_advanced_code, {"page": page, "re": python_re})

            # Get action log and verify
            log_lines = get_action_log(page)

            # Expected log entries
            expected_log = [
                "click submit-button",
                "fill user-input text",
                "click submit-role",
                "fill email-role user@example.com",
                "click main-heading",
                "click signin-text",
                "click welcome-text",
                "click form-submit",
                "fill email-field test@test.com",
                "click btn-primary",
                "click submit",
                "click nested-button",
                "click container-div",
                "click edit-john",
                "click button-3",
                "count disabled-buttons 2",
                "click edit-john",
            ]

            assert log_lines == expected_log, (
                f"Log mismatch:\nExpected: {expected_log}\nActual: {log_lines}"
            )

            browser.close()
