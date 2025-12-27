"""Tests for Selectors & Locators examples from API_REFERENCE.md."""

import re
from pathlib import Path
from playwright.sync_api import sync_playwright


def extract_selectors_locators_code():
    """Extract Selectors & Locators examples from API_REFERENCE.md.

    Returns:
        Tuple of (best_practices_code, advanced_patterns_code)
    """
    api_ref_path = (
        Path(__file__).parent.parent
        / "skills"
        / "playwright-py-skill"
        / "API_REFERENCE.md"
    )

    content = api_ref_path.read_text()

    # Extract Best Practices for Selectors section
    best_pattern = r"### Best Practices for Selectors\s*```python\s*(.*?)```"
    best_match = re.search(best_pattern, content, re.DOTALL)

    assert best_match, (
        "Best Practices for Selectors example not found in API_REFERENCE.md"
    )
    best_practices_code = best_match.group(1)

    # Extract Advanced Locator Patterns section
    advanced_pattern = r"### Advanced Locator Patterns\s*```python\s*(.*?)```"
    advanced_match = re.search(advanced_pattern, content, re.DOTALL)

    assert advanced_match, (
        "Advanced Locator Patterns example not found in API_REFERENCE.md"
    )
    advanced_patterns_code = advanced_match.group(1)

    return best_practices_code, advanced_patterns_code


class TestSelectorsAndLocators:
    """Tests for the Selectors & Locators examples."""

    def test_selectors_locators_examples(self, test_server_url):
        """Test Selectors & Locators examples from API_REFERENCE.md.

        This test:
        - Extracts code from API_REFERENCE.md at runtime
        - Executes selector patterns on test page
        - Verifies actions are logged correctly via action log element
        - Tests all selector strategies: data attributes, role-based, text, semantic, advanced
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto(f"{test_server_url}/selectors")

            # Wait for action log to be ready
            page.locator("#action-log").wait_for(state="visible")

            # Execute selectors from API_REFERENCE.md examples

            # Data attribute selectors (PREFERRED)
            page.locator('[data-testid="submit-button"]').click()
            page.locator('[data-cy="user-input"]').fill("text")

            # Role-based selectors (GOOD)
            page.get_by_role("button", name="Submit Button").click()
            page.get_by_role("textbox", name="Email Address").fill("user@example.com")
            page.get_by_role("heading", name="Main Heading").click()

            # Text content selectors (GOOD)
            page.get_by_text("Sign in").click()
            page.get_by_text("Welcome Back").click()

            # Semantic HTML selectors (OK)
            page.locator('button[type="submit"]').click()
            page.locator('input[name="email"]').fill("test@test.com")

            # AVOID examples (included to show they work but are bad practices)
            page.locator(".btn-primary").click()
            page.locator("#submit").click()
            page.locator("div.container > form > button").click()

            # Advanced Locator Patterns
            # Filter and chain locators
            page.locator("tr").filter(has_text="John Doe").locator("button").click()

            # Nth element (clicks 3rd button)
            page.locator("button").nth(2).click()

            # Combining conditions with count
            count = page.locator("button").and_(page.locator("[disabled]")).count()
            page.locator("#action-log").evaluate(
                f"(el) => el.textContent += 'count disabled-buttons {count}\\n'"
            )

            # Parent/child navigation
            cell = page.locator("td").filter(has_text="Jane Smith")
            row = cell.locator("..")
            row.locator(".edit").click()

            # Get the action log and verify
            log_content = page.locator("#action-log").text_content()
            log_lines = [
                line.strip() for line in log_content.strip().split("\n") if line.strip()
            ]

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
                "click form-submit",
                "count disabled-buttons 2",
                "click edit-jane",
            ]

            assert log_lines == expected_log, (
                f"Log mismatch:\nExpected: {expected_log}\nActual: {log_lines}"
            )

            browser.close()
