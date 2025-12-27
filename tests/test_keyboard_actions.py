"""Tests for Keyboard Actions examples from API_REFERENCE.md."""

import re
from pathlib import Path
from playwright.sync_api import sync_playwright


def extract_keyboard_actions_code():
    """Extract Keyboard Actions examples from API_REFERENCE.md.

    Returns:
        Modified code ready for execution
    """
    api_ref_path = (
        Path(__file__).parent.parent
        / "skills"
        / "playwright-py-skill"
        / "API_REFERENCE.md"
    )

    content = api_ref_path.read_text()

    pattern = r"### Keyboard Actions\s*```python\s*(.*?)```"
    match = re.search(pattern, content, re.DOTALL)

    assert match, "Keyboard Actions example not found in API_REFERENCE.md"
    extracted_code = match.group(1)

    # Verify we extracted the expected code
    assert "page.keyboard.type('Hello World', delay=100)" in extracted_code
    assert "page.keyboard.press('Control+A')" in extracted_code
    assert "page.keyboard.press('Control+C')" in extracted_code
    assert "page.keyboard.press('Control+V')" in extracted_code
    assert "page.keyboard.press('Enter')" in extracted_code
    assert "page.keyboard.press('Tab')" in extracted_code
    assert "page.keyboard.press('Escape')" in extracted_code
    assert "page.keyboard.press('ArrowDown')" in extracted_code

    return extracted_code


class TestKeyboardActions:
    """Tests for the Keyboard Actions examples."""

    def test_keyboard_actions_examples(self, test_server_url):
        """Test Keyboard Actions examples from API_REFERENCE.md.

        This test:
        - Extracts code from API_REFERENCE.md at runtime
        - Executes all keyboard action examples in sequence
        - Verifies all events are logged correctly:
          * Type with delay (logs each character typed)
          * Control+A selects all text
          * Control+C/V copy-paste works
          * Special keys work correctly (Enter, Tab, Escape, ArrowDown)
        """
        extracted_code = extract_keyboard_actions_code()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto(f"{test_server_url}/keyboard-actions")

            # Wait for action log to be ready
            page.locator("#action-log").wait_for(state="visible")

            # Modify and execute all Keyboard Actions code from API_REFERENCE.md
            # We need to focus elements and add waits between actions
            lines = extracted_code.split("\n")
            modified_code = []
            for line in lines:
                # Add focus before type and press operations
                if "page.keyboard.type('Hello World', delay=100)" in line:
                    modified_code.append("page.locator('#type-input').focus()")
                    modified_code.append(line)
                elif "page.keyboard.press('Control+A')" in line:
                    modified_code.append("page.locator('#combo-input').focus()")
                    modified_code.append(line)
                elif "page.keyboard.press('Control+C')" in line:
                    modified_code.append(line)
                elif "page.keyboard.press('Control+V')" in line:
                    modified_code.append(line)
                elif "page.keyboard.press('Enter')" in line:
                    modified_code.append("page.locator('#special-input').focus()")
                    modified_code.append(line)
                elif "page.keyboard.press('Tab')" in line:
                    modified_code.append(line)
                elif "page.keyboard.press('Escape')" in line:
                    modified_code.append(line)
                elif "page.keyboard.press('ArrowDown')" in line:
                    modified_code.append(line)
                else:
                    modified_code.append(line)
                # Add wait after each keyboard action line (preserve indentation)
                stripped = line.strip()
                if stripped.startswith("page.keyboard."):
                    # Get the leading whitespace
                    indent = line[: len(line) - len(line.lstrip())]
                    modified_code.append(f"{indent}page.wait_for_timeout(200)")

            exec("\n".join(modified_code), {"page": page})

            # Get action log and verify
            log_content = page.locator("#action-log").text_content()
            log_lines = [
                line.strip() for line in log_content.strip().split("\n") if line.strip()
            ]

            # Expected log entries
            # Type with delay should log each character as it's typed
            # Control+A should log the full text being selected
            # Control+C/V should not log anything (copy/paste operations)
            # Special keys should each log their key name
            expected_log = [
                "type H",
                "type He",
                "type Hel",
                "type Hell",
                "type Hello",
                "type Hello ",
                "type Hello W",
                "type Hello Wo",
                "type Hello Wor",
                "type Hello Worl",
                "type Hello World",
                "keydown Ctrl+A",
                "select Initial text",
                "keydown Ctrl+C",
                "keydown Ctrl+V",
                "keydown Enter",
                "keydown Tab",
                "keydown Escape",
                "keydown ArrowDown",
            ]

            # Verify all expected events are present
            for expected in expected_log:
                assert any(expected in line for line in log_lines), (
                    f"Expected event '{expected}' not found in log: {log_lines}"
                )

            browser.close()
