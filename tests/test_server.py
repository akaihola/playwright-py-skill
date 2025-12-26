"""Test the test server fixture."""

import pytest


def test_index_page(test_server_url):
    """Test that the index page loads."""
    import requests

    response = requests.get(f"{test_server_url}/")
    assert response.status_code == 200
    assert "Welcome" in response.text


def test_login_page(test_server_url):
    """Test that the login page loads."""
    import requests

    response = requests.get(f"{test_server_url}/login")
    assert response.status_code == 200
    assert "Login" in response.text


def test_contact_page(test_server_url):
    """Test that the contact page loads."""
    import requests

    response = requests.get(f"{test_server_url}/contact")
    assert response.status_code == 200
    assert "Contact Us" in response.text


def test_api_users(test_server_url):
    """Test that the API returns user data."""
    import requests

    response = requests.get(f"{test_server_url}/api/users")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["name"] == "John Doe"


def test_headers_endpoint(test_server_url):
    """Test that the headers endpoint returns JSON."""
    import requests

    response = requests.get(f"{test_server_url}/headers")
    assert response.status_code == 200
    headers = response.json()
    assert "Host" in headers


def test_login_redirect(test_server_url):
    """Test that login redirects to dashboard on success."""
    import requests

    with requests.Session() as session:
        response = session.post(
            f"{test_server_url}/login",
            data={"email": "test@example.com", "password": "password"},
        )
        assert response.status_code == 200
        assert "Dashboard" in response.text


def test_dashboard_requires_login(test_server_url):
    """Test that dashboard requires login."""
    import requests

    response = requests.get(f"{test_server_url}/dashboard")
    assert response.url.endswith("/login")


def test_accessibility_page(test_server_url):
    """Test that the accessibility page loads with intentional issues."""
    import requests

    response = requests.get(f"{test_server_url}/accessibility")
    assert response.status_code == 200
    assert "Accessibility Test" in response.text


def test_geolocation_page(test_server_url):
    """Test that the geolocation page loads."""
    import requests

    response = requests.get(f"{test_server_url}/geolocation")
    assert response.status_code == 200
    assert "Geolocation Test" in response.text
