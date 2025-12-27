#!/usr/bin/env python3
"""Minimal test server for Playwright documentation examples."""

import socket
import threading
import pytest
from textwrap import dedent
from flask import Flask, request, jsonify, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "test-secret-key"


@app.route("/")
def index():
    """Basic page for simple navigation tests."""
    return dedent(
        """\
        <!DOCTYPE html>
        <html><head><title>Home</title></head>
        <body><h1>Welcome</h1><p><a href="/login">Login</a></p><p><a href="/contact">Contact</a></p></body>
        </html>"""
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login form with email/password fields."""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if email == "test@example.com" and password == "password":
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        return dedent(
            """\
            <html><body><h1>Invalid credentials</h1><a href="/login">Try again</a></body></html>"""
        )
    return dedent(
        """\
        <!DOCTYPE html>
        <html><head><title>Login</title></head>
        <body><h1>Login</h1>
        <form method="POST"><label>Email:</label><input name="email" type="email"><br>
        <label>Password:</label><input name="password" type="password"><br>
        <button type="submit">Login</button></form></body></html>"""
    )


@app.route("/dashboard")
def dashboard():
    """Protected page (requires login), contains data table."""
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return dedent(
        """\
        <!DOCTYPE html>
        <html><head><title>Dashboard</title></head>
        <body><h1>Dashboard</h1>
        <table><tr><th>Name</th><th>Email</th></tr>
        <tr><td>John Doe</td><td>john@example.com</td></tr>
        <tr><td>Jane Smith</td><td>jane@example.com</td></tr></table>
        <p><a href="/logout">Logout</a></p></body></html>"""
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/success")
def success():
    """Success page with message div for Test Structure pattern tests."""
    return dedent(
        """\
        <!DOCTYPE html>
        <html><head><title>Success</title></head>
        <body>
        <div class="message">Success!</div>
        <p><a href="/">Home</a></p>
        </body></html>"""
    )


@app.route("/contact", methods=["GET", "POST"])
def contact():
    """Contact form (name/email/message fields)."""
    if request.method == "POST":
        return redirect(url_for("success"))
    return dedent(
        """\
        <!DOCTYPE html>
        <html><head><title>Contact</title></head>
        <body><h1>Contact Us</h1>
        <form method="POST"><label>Name:</label><input name="name" type="text"><br>
        <label>Email:</label><input name="email" type="email"><br>
        <label>Message:</label><textarea name="message"></textarea><br>
        <button type="submit" data-testid="submit-button">Send</button></form></body></html>"""
    )


@app.route("/accessibility")
def accessibility():
    """Page with intentional a11y issues (missing labels, low contrast)."""
    return dedent(
        """\
        <!DOCTYPE html>
        <html><head><title>Accessibility Test</title></head>
        <body><h1>Accessibility Test</h1>
        <form><input type="text" placeholder="Name"><input type="submit" value="Submit"></form>
        <button style="color:#999;background:#888">Low Contrast</button></body></html>"""
    )


@app.route("/geolocation")
def geolocation():
    """Page with geolocation test button."""
    return dedent(
        """\
        <!DOCTYPE html>
        <html><head><title>Geolocation</title></head>
        <body><h1>Geolocation Test</h1>
        <button onclick="navigator.geolocation.getCurrentPosition(p=>alert(p.coords.latitude+','+p.coords.longitude))">Get Location</button></body></html>"""
    )


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
    return dedent(
        """\
        <!DOCTYPE html>
        <html><head><title>Selectors Test</title></head>
        <body>
        <h2>Selectors Test Page</h2>
        <p>Action Log:</p>
        <pre id="action-log" style="background:#f0f0f0;padding:10px;border:1px solid #ccc;"></pre>
        <script>
            window.actionLog = document.getElementById('action-log');
            function log(type, id, value) {
                value = value || '';
                window.actionLog.textContent += type + ' ' + id + (value ? ' ' + value : '') + '\\n';
            }
            function setupEventListeners() {
                var allElements = document.querySelectorAll('button, input, h1, div[id]');
                var wrapperIds = [
                    'nth-element-section'
                ];
                for (var i = 0; i < allElements.length; i++) {
                    var el = allElements[i];
                    if (el.tagName === 'INPUT') {
                        el.addEventListener('input', function(e) {
                            log('fill', this.id, e.target.value);
                        });
                    } else if (wrapperIds.indexOf(el.id) === -1) {
                        el.addEventListener('click', function(e) {
                            e.preventDefault();
                            log('click', this.id);
                        });
                    }
                }
            }
            document.addEventListener('DOMContentLoaded', setupEventListeners);
        </script>
        <hr>
        <h2>Data Attribute Selectors</h2>
        <hr>
        <h2>Data Attribute Selectors</h2>
        <button id="submit-button" data-testid="submit-button">Data Button</button>
        <input id="user-input" data-cy="user-input" type="text" placeholder="User Input">
        <hr>
        <h2>Role-Based Selectors</h2>
        <button id="submit-role" role="button" aria-label="Submit">Submit (Role)</button>
        <input id="email-role" role="textbox" aria-label="Email" type="text" placeholder="Email (Role)">
        <h1 id="main-heading">Main Heading</h1>
        <hr>
        <h2>Text Content Selectors</h2>
        <div id="signin-text" onclick="void(0)">Sign in</div>
        <div id="welcome-text" onclick="void(0)">Welcome Back</div>
        <hr>
        <h2>Semantic HTML Selectors</h2>
        <button id="form-submit" type="submit">Save Changes</button>
        <input id="email-field" name="email" type="text" placeholder="Username (name attr)">
        <hr>
        <h2>Advanced Locator Patterns</h2>
        <table>
            <thead><tr><th>Name</th><th>Status</th><th>Action</th></tr></thead>
            <tbody>
                <tr id="row-john">
                    <td>John Doe</td>
                    <td>Active</td>
                    <td><button id="edit-john" class="edit">Edit</button></td>
                </tr>
                <tr id="row-jane">
                    <td>Jane Smith</td>
                    <td>Pending</td>
                    <td><button id="edit-jane" class="edit">Edit</button></td>
                </tr>
                <tr id="row-bob">
                    <td>Bob Johnson</td>
                    <td>Offline</td>
                    <td><button id="edit-bob" class="edit">Edit</button></td>
                </tr>
            </tbody>
        </table>
        <div id="nth-element-section">
        <h2>Nth Element Test</h2>
        <button id="button-1">Button 1</button>
        <button id="button-2">Button 2</button>
        <button id="button-3">Button 3</button>
        <button id="button-4" disabled>Button 4</button>
        <button id="button-5" disabled>Button 5</button>
        </div>
        <hr>
        <h2>AVOID / LAST RESORT Patterns (Bad Practices)</h2>
        <button id="btn-primary" class="btn-primary">Class Button</button>
        <button id="submit" >ID Button</button>
        <div id="container-div" class="container" style="border:1px solid #ccc;padding:10px;">
            <form>
                <button id="nested-button" onclick="event.preventDefault()">Nested Button</button>
            </form>
        </div>
        </body></html>"""
    )


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
