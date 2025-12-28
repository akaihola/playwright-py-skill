"""Tests for Mouse Actions examples from API_REFERENCE.md."""

import re
from playwright.sync_api import sync_playwright
from conftest import extract_markdown_code, get_action_log


def extract_mouse_actions_code():
    """Extract Mouse Actions examples from API_REFERENCE.md.

    Returns:
        Modified code ready for execution
    """
    return extract_markdown_code(
        "Mouse Actions",
        expected_substrings=[
            "page.click('button')",
            "page.click('button', button=\"right\")",
            "page.dblclick('button')",
            'page.click(\'button\', position={"x": 10, "y": 10})',
            "page.hover('.menu-item')",
            "page.drag_and_drop('#source', '#target')",
            "page.locator('#source').hover()",
            "page.mouse.down()",
            "page.mouse.up()",
        ],
    )


class TestMouseActions:
    """Tests for the Mouse Actions examples."""

    def test_mouse_actions_examples(self, test_server_url):
        """Test Mouse Actions examples from API_REFERENCE.md.

        This test:
        - Extracts code from API_REFERENCE.md at runtime
        - Executes all mouse action examples in sequence
        - Verifies all events are logged correctly:
          * Left click (logs coordinates)
          * Right click (contextmenu)
          * Double click
          * Click at specific position (x=10, y=10)
          * Hover effect
          * Drag and drop
          * Manual drag sequence
        """
        extracted_code = extract_mouse_actions_code()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto(f"{test_server_url}/mouse-actions")

            # Wait for action log to be ready
            page.locator("#action-log").wait_for(state="visible")

            # Execute all Mouse Actions code from API_REFERENCE.md
            # Add small waits between actions to ensure page stability
            lines = extracted_code.split("\n")
            modified_code = []
            for line in lines:
                # Add force=True to hover to bypass any interference
                if ".hover('.menu-item')" in line:
                    modified_code.append(
                        line.replace(
                            ".hover('.menu-item')", ".hover('.menu-item', force=True)"
                        )
                    )
                else:
                    modified_code.append(line)
                # Add wait after each page action line (preserve indentation)
                stripped = line.strip()
                if stripped.startswith("page.") and any(
                    action in line for action in ["click", "hover", "drag"]
                ):
                    # Get the leading whitespace
                    indent = line[: len(line) - len(line.lstrip())]
                    modified_code.append(f"{indent}page.wait_for_timeout(100)")

            exec("\n".join(modified_code), {"page": page})

            # Get action log and verify
            log_lines = get_action_log(page)

            # Expected log entries
            # Note: The actual coordinate values may vary slightly, but position=10,10 should be close
            expected_log = [
                "click test-button",  # Left click
                "contextmenu test-button",  # Right click
                "dblclick test-button",  # Double click
                "click test-button",  # Click at position
                "hover menu-item",  # Hover
                "dragstart source",  # Drag and drop
                "drop target",  # Drag and drop
                "dragstart source",  # Manual drag start
                "drop target",  # Manual drag end
            ]

            # Verify all expected events are present
            for expected in expected_log:
                assert any(expected in line for line in log_lines), (
                    f"Expected event '{expected}' not found in log: {log_lines}"
                )

            # Verify position click has coordinates near x=10,y=10
            # The position click comes after hover in the log
            position_lines = [line for line in log_lines if "click test-button" in line]
            assert len(position_lines) >= 2, (
                f"Expected at least 2 click events, got {len(position_lines)}"
            )

            # Find the position-based click (should have coordinates near 10,10)
            # Look for the click with small coordinates (x=10,y=10)
            position_click = None
            for line in position_lines:
                if "x=" in line and "y=" in line:
                    coord_match = re.search(r"x=(\d+),y=(\d+)", line)
                    if coord_match:
                        x = int(coord_match.group(1))
                        y = int(coord_match.group(2))
                        if x < 50 and y < 50:  # Position click should be near 10,10
                            position_click = line
                            break

            assert position_click, (
                f"Could not find position click with small coordinates in: {position_lines}"
            )

            # Parse and verify coordinates are near 10,10
            coord_match = re.search(r"x=(\d+),y=(\d+)", position_click)
            assert coord_match, f"Could not parse coordinates from: {position_click}"
            x = int(coord_match.group(1))
            y = int(coord_match.group(2))
            assert abs(x - 10) <= 5, f"Expected x near 10, got {x}"
            assert abs(y - 10) <= 5, f"Expected y near 10, got {y}"

            browser.close()
