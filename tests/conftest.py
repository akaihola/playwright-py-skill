#!/usr/bin/env python3
"""Minimal test server for Playwright documentation examples."""

import socket
import threading
import pytest
from flask import Flask, request, jsonify, redirect, url_for, session, render_template

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
