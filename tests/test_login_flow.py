"""Test the Login Flow example from SKILL.md."""

from playwright.sync_api import Page
from conftest import extract_markdown_code, get_action_log


def test_login_flow_example(test_server_url: str, page: Page) -> None:
    """Test that the 'Test Login Flow' example from SKILL.md works correctly.

    Verifies:
    - Navigation to /login page
    - Email field filled with test@example.com
    - Password field filled with password
    - Submit button clicked
    - Redirect to /dashboard
    - Dashboard content visible
    """
    code = extract_markdown_code(
        section_name="Test Login Flow", markdown_file="SKILL.md"
    )

    modified_code = code.replace("headless=False", "headless=True")
    modified_code = modified_code.replace(
        "TARGET_URL = 'http://localhost:3001'", f"TARGET_URL = '{test_server_url}'"
    )
    modified_code = modified_code.replace("'password123'", "'password'")

    lines = modified_code.split("\n")
    exec_code_lines = []
    in_with_block = False
    for line in lines:
        stripped_line = line.strip()

        if not stripped_line or stripped_line.startswith("#"):
            continue

        if "from playwright.sync_api import sync_playwright" in stripped_line:
            continue
        if "with sync_playwright" in stripped_line:
            in_with_block = True
            continue
        if "browser = p.chromium.launch" in stripped_line:
            continue
        if "page = browser.new_page()" in stripped_line:
            continue
        if "browser.close()" in stripped_line:
            in_with_block = False
            continue

        if "page.click" in stripped_line and "submit" in stripped_line:
            exec_code_lines.append("action_log = get_action_log(page)")
            exec_code_lines.append(stripped_line)
            continue

        if in_with_block:
            exec_code_lines.append(stripped_line)
        else:
            exec_code_lines.append(line)

    exec_globals = {"page": page, "get_action_log": get_action_log}
    exec("\n".join(exec_code_lines), exec_globals)

    action_log = exec_globals["action_log"]
    assert action_log == [
        "load login-page",
        "fill email test@example.com",
        "change email test@example.com",
        "fill password password",
    ]

    assert page.url == f"{test_server_url}/dashboard"
    assert "Dashboard" in page.title()
