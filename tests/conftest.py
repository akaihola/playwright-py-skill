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


@app.route("/contact", methods=["GET", "POST"])
def contact():
    """Contact form (name/email/message fields)."""
    if request.method == "POST":
        return dedent(
            """\
            <html><body><h1>Thank you!</h1><p>Your message has been sent.</p><a href="/">Home</a></body></html>"""
        )
    return dedent(
        """\
        <!DOCTYPE html>
        <html><head><title>Contact</title></head>
        <body><h1>Contact Us</h1>
        <form method="POST"><label>Name:</label><input name="name" type="text"><br>
        <label>Email:</label><input name="email" type="email"><br>
        <label>Message:</label><textarea name="message"></textarea><br>
        <button type="submit">Send</button></form></body></html>"""
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
