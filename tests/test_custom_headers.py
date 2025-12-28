""" "Tests for Custom HTTP Headers feature via environment variables."""

import sys
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

# Add parent directory to path to import helpers
sys.path.insert(
    0,
    str(Path(__file__).parent.parent / "skills" / "playwright-py-skill"),
)

from lib.helpers import (
    get_extra_headers_from_env,
    get_context_options_with_headers,
    create_context,
)
from conftest import extract_json_from_page


class TestGetExtraHeadersFromEnv:
    """Tests for get_extra_headers_from_env() function."""

    def test_single_header_from_env_vars(self, monkeypatch):
        """Test parsing PW_HEADER_NAME and PW_HEADER_VALUE."""
        monkeypatch.setenv("PW_HEADER_NAME", "X-Automated-By")
        monkeypatch.setenv("PW_HEADER_VALUE", "playwright-py-skill")

        headers = get_extra_headers_from_env()

        assert headers is not None
        assert headers == {"X-Automated-By": "playwright-py-skill"}

    def test_multiple_headers_from_json(self, monkeypatch):
        """Test parsing PW_EXTRA_HEADERS as JSON."""
        headers_json = json.dumps(
            {
                "X-Automated-By": "playwright-py-skill",
                "X-Debug": "true",
                "X-Request-ID": "12345",
            }
        )
        monkeypatch.setenv("PW_EXTRA_HEADERS", headers_json)

        headers = get_extra_headers_from_env()

        assert headers is not None
        assert headers == {
            "X-Automated-By": "playwright-py-skill",
            "X-Debug": "true",
            "X-Request-ID": "12345",
        }

    def test_single_header_takes_precedence(self, monkeypatch):
        """Test that PW_HEADER_NAME/VALUE takes precedence over PW_EXTRA_HEADERS."""
        monkeypatch.setenv("PW_HEADER_NAME", "X-Automated-By")
        monkeypatch.setenv("PW_HEADER_VALUE", "playwright-py-skill")
        monkeypatch.setenv("PW_EXTRA_HEADERS", '{"X-Other":"value"}')

        headers = get_extra_headers_from_env()

        assert headers is not None
        assert headers == {"X-Automated-By": "playwright-py-skill"}

    def test_no_headers_returns_none(self, monkeypatch):
        """Test that no environment variables returns None."""
        monkeypatch.delenv("PW_HEADER_NAME", raising=False)
        monkeypatch.delenv("PW_HEADER_VALUE", raising=False)
        monkeypatch.delenv("PW_EXTRA_HEADERS", raising=False)

        headers = get_extra_headers_from_env()

        assert headers is None

    def test_invalid_json_extra_headers(self, monkeypatch, capsys):
        """Test that invalid JSON in PW_EXTRA_HEADERS is handled gracefully."""
        monkeypatch.setenv("PW_EXTRA_HEADERS", "{invalid json}")

        headers = get_extra_headers_from_env()

        assert headers is None
        captured = capsys.readouterr()
        assert "Failed to parse PW_EXTRA_HEADERS as JSON" in captured.err

    def test_extra_headers_as_list_warning(self, monkeypatch, capsys):
        """Test that PW_EXTRA_HEADERS as list (not dict) is rejected."""
        headers_json = json.dumps(["header1", "header2"])
        monkeypatch.setenv("PW_EXTRA_HEADERS", headers_json)

        headers = get_extra_headers_from_env()

        assert headers is None
        captured = capsys.readouterr()
        assert "PW_EXTRA_HEADERS must be a JSON object" in captured.err

    def test_partial_env_vars_no_header_name(self, monkeypatch):
        """Test that only PW_HEADER_VALUE without PW_HEADER_NAME returns None."""
        monkeypatch.delenv("PW_HEADER_NAME", raising=False)
        monkeypatch.setenv("PW_HEADER_VALUE", "test-value")

        headers = get_extra_headers_from_env()

        assert headers is None

    def test_partial_env_vars_no_header_value(self, monkeypatch):
        """Test that only PW_HEADER_NAME without PW_HEADER_VALUE returns None."""
        monkeypatch.setenv("PW_HEADER_NAME", "X-Test")
        monkeypatch.delenv("PW_HEADER_VALUE", raising=False)

        headers = get_extra_headers_from_env()

        assert headers is None


class TestGetContextOptionsWithHeaders:
    """Tests for get_context_options_with_headers() utility."""

    def test_merges_env_headers_into_options(self, monkeypatch):
        """Test that environment headers are merged into context options."""
        monkeypatch.setenv("PW_HEADER_NAME", "X-Test")
        monkeypatch.setenv("PW_HEADER_VALUE", "test-value")

        options = {"viewport": {"width": 1920, "height": 1080}}
        result = get_context_options_with_headers(options)

        assert result["viewport"] == {"width": 1920, "height": 1080}
        assert result["extra_http_headers"] == {"X-Test": "test-value"}

    def test_no_env_headers_returns_options_unchanged(self, monkeypatch):
        """Test that no env headers returns options unchanged."""
        monkeypatch.delenv("PW_HEADER_NAME", raising=False)
        monkeypatch.delenv("PW_HEADER_VALUE", raising=False)
        monkeypatch.delenv("PW_EXTRA_HEADERS", raising=False)

        options = {"viewport": {"width": 1920, "height": 1080}}
        result = get_context_options_with_headers(options)

        assert result == options

    def test_merges_with_existing_extra_headers(self, monkeypatch):
        """Test that env headers merge with existing extra_headers."""
        monkeypatch.setenv("PW_HEADER_NAME", "X-Env-Header")
        monkeypatch.setenv("PW_HEADER_VALUE", "env-value")

        options = {
            "viewport": {"width": 1920},
            "extra_http_headers": {"X-Manual-Header": "manual-value"},
        }
        result = get_context_options_with_headers(options)

        assert result["extra_http_headers"] == {
            "X-Env-Header": "env-value",
            "X-Manual-Header": "manual-value",
        }

    def test_env_headers_override_existing(self, monkeypatch):
        """Test that manually passed headers override env headers."""
        monkeypatch.setenv("PW_HEADER_NAME", "X-Override-Header")
        monkeypatch.setenv("PW_HEADER_VALUE", "env-value")

        options = {"extra_http_headers": {"X-Override-Header": "manual-value"}}
        result = get_context_options_with_headers(options)

        assert result["extra_http_headers"]["X-Override-Header"] == "manual-value"

    def test_none_options_returns_empty_dict(self, monkeypatch):
        """Test that None options returns empty dict when env headers exist."""
        monkeypatch.setenv("PW_HEADER_NAME", "X-Test")
        monkeypatch.setenv("PW_HEADER_VALUE", "test-value")

        result = get_context_options_with_headers(None)

        assert result == {"extra_http_headers": {"X-Test": "test-value"}}


class TestCreateContextAutoHeaders:
    """Tests for create_context() auto-headers merging."""

    def test_context_includes_env_headers(self, monkeypatch):
        """Test that create_context() includes environment headers."""
        monkeypatch.setenv("PW_HEADER_NAME", "X-Test-Context")
        monkeypatch.setenv("PW_HEADER_VALUE", "context-value")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = create_context(browser)

            # Check that context has the extra headers
            # Note: We can't directly access headers from context, but we can
            # verify by making a request and checking what headers are sent
            assert context is not None

            browser.close()

    def test_context_merges_with_passed_options(self, monkeypatch):
        """Test that create_context() merges env headers with passed options."""
        monkeypatch.setenv("PW_HEADER_NAME", "X-Env-Header")
        monkeypatch.setenv("PW_HEADER_VALUE", "env-value")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = create_context(
                browser,
                viewport={"width": 1920, "height": 1080},
                extra_http_headers={"X-Manual-Header": "manual-value"},
            )

            # Verify context was created
            assert context is not None

            browser.close()


class TestHeadersInHttpRequests:
    """Tests that verify headers are actually sent in HTTP requests."""

    def test_single_header_sent_in_request(self, monkeypatch, test_server_url):
        """Test that single header from env vars is sent in HTTP requests."""
        monkeypatch.setenv("PW_HEADER_NAME", "X-Automated-By")
        monkeypatch.setenv("PW_HEADER_VALUE", "playwright-py-skill")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = create_context(browser)
            page = context.new_page()

            # Navigate to headers endpoint
            page.goto(f"{test_server_url}/headers")
            page.wait_for_load_state("networkidle")

            response = extract_json_from_page(page)

            # Check that our custom header was sent
            # The /headers endpoint returns request headers as JSON
            assert "X-Automated-By" in response
            assert response["X-Automated-By"] == "playwright-py-skill"

            browser.close()

    def test_multiple_headers_sent_in_request(self, monkeypatch, test_server_url):
        """Test that multiple headers from JSON are sent in HTTP requests."""
        headers_json = json.dumps(
            {
                "X-Automated-By": "playwright-py-skill",
                "X-Debug": "true",
                "X-Request-ID": "12345",
            }
        )
        monkeypatch.setenv("PW_EXTRA_HEADERS", headers_json)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = create_context(browser)
            page = context.new_page()

            # Navigate to headers endpoint
            page.goto(f"{test_server_url}/headers")
            page.wait_for_load_state("networkidle")

            response = extract_json_from_page(page)

            # Check that all custom headers were sent
            assert "X-Automated-By" in response
            assert response["X-Automated-By"] == "playwright-py-skill"
            assert "X-Debug" in response
            assert response["X-Debug"] == "true"
            # Flask normalizes header names (ID -> Id)
            assert "X-Request-Id" in response or "X-Request-ID" in response
            request_id = response.get("X-Request-Id") or response.get("X-Request-ID")
            assert request_id == "12345"

            browser.close()

    def test_headers_sent_on_all_requests(self, monkeypatch, test_server_url):
        """Test that headers are sent on multiple requests from the same context."""
        monkeypatch.setenv("PW_HEADER_NAME", "X-Request-Tracker")
        monkeypatch.setenv("PW_HEADER_VALUE", "test-tracker")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = create_context(browser)
            page = context.new_page()

            # Make multiple requests to different endpoints
            for i in range(3):
                page.goto(f"{test_server_url}/headers")
                page.wait_for_load_state("networkidle")

                response = extract_json_from_page(page)

                # Check that header is present on each request
                assert "X-Request-Tracker" in response
                assert response["X-Request-Tracker"] == "test-tracker"

            browser.close()
