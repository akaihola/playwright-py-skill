#!/usr/bin/env python3
"""Minimal test server for Playwright documentation examples."""

import re
import socket
import threading
from pathlib import Path

import pytest
from flask import Flask, request, jsonify, redirect, url_for, session, render_template
from playwright.sync_api import sync_playwright


class DummyBrowser:
    """Dummy browser class for exec() namespace."""

    def close(self):
        pass


def extract_markdown_code(
    section_name, markdown_file="API_REFERENCE.md", expected_substrings=None
):
    """Extract code block from a markdown file's section.

    Args:
        section_name: Name of the section header (e.g., "Basic Browser Automation")
        markdown_file: Name of the markdown file in skills/playwright-py-skill/
        expected_substrings: Optional list of strings that must be present in extracted code

    Returns:
        Extracted code block as string
    """
    skill_path = (
        Path(__file__).parent.parent / "skills" / "playwright-py-skill" / markdown_file
    )

    content = skill_path.read_text()

    pattern = rf"### {re.escape(section_name)}\s*```python\s*(.*?)```"
    match = re.search(pattern, content, re.DOTALL)

    assert match, f"{section_name} example not found in {markdown_file}"
    extracted_code = match.group(1)

    if expected_substrings:
        for expected in expected_substrings:
            assert expected in extracted_code, (
                f"Expected '{expected}' not found in {section_name} code"
            )

    return extracted_code


def get_action_log(page):
    """Extract and parse action log content from the page.

    Args:
        page: Playwright Page object

    Returns:
        List of non-empty, stripped log lines from #action-log element
    """
    log_content = page.locator("#action-log").text_content()
    return [line.strip() for line in log_content.strip().split("\n") if line.strip()]


def extract_json_from_page(page):
    """Extract JSON from page content, handling Flask-wrapped <pre> tags.

    Args:
        page: Playwright Page object

    Returns:
        Parsed JSON data from the page content
    """
    import json

    page_content = page.content()
    json_match = re.search(r"<pre>(.*?)</pre>", page_content, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(1))
    else:
        return json.loads(page_content)


app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "test-secret-key"


@app.route("/")
def index():
    """Basic page for simple navigation tests."""
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login form with email/password fields."""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if email == "test@example.com" and password == "password":
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        return render_template("login_error.html")
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    """Protected page (requires login), contains data table."""
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("dashboard.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/success")
def success():
    """Success page with message div for Test Structure pattern tests."""
    return render_template("success.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    """Contact form (name/email/message fields)."""
    if request.method == "POST":
        return redirect(url_for("success"))
    return render_template("contact.html")


@app.route("/accessibility")
def accessibility():
    """Page with intentional a11y issues (missing labels, low contrast)."""
    return render_template("accessibility.html")


@app.route("/geolocation")
def geolocation():
    """Page with geolocation test button."""
    return render_template("geolocation.html")


@app.route("/api/users")
def api_users():
    """Mock API endpoint returning JSON user data."""
    return jsonify(
        [
            {"id": 1, "name": "John Doe", "email": "john@example.com"},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com"},
            {"id": 3, "name": "Bob Johnson", "email": "bob@example.com"},
        ]
    )


@app.route("/headers")
def headers():
    """Returns JSON of request headers."""
    return jsonify(dict(request.headers))


@app.route("/selectors")
def selectors():
    """Test page with elements for selector/locator examples."""
    return render_template("selectors.html")


@app.route("/mouse-actions")
def mouse_actions():
    """Test page with interactive mouse action elements."""
    return render_template("mouse-actions.html")


@app.route("/keyboard-actions")
def keyboard_actions():
    """Test page with interactive keyboard action elements."""
    return render_template("keyboard-actions.html")


@pytest.fixture(scope="session")
def test_server_url():
    """Start Flask server on available port and return URL."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()

    def run_server():
        app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()

    import time

    time.sleep(0.5)

    yield f"http://127.0.0.1:{port}"


@pytest.fixture
def page():
    """Fixture providing a Playwright page object with automatic cleanup."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            yield page
        finally:
            browser.close()
