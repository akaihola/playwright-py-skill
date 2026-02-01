#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "playwright==1.57.0",
#     "aiohttp>=3.9.0",
# ]
# ///
"""
Universal Playwright Executor for Claude Code

Executes Playwright automation code from:
- File path: uv run run.py script.py
- Inline code: uv run run.py 'await page.goto("...")'
- Stdin: cat script.py | uv run run.py

Interactive browser session mode:
- Launch:  uv run run.py --open [URL]
- Command: uv run run.py --cdp 'print(page.title())'
- Both:    uv run run.py --open URL --cdp 'print(page.title())'
- Close:   uv run run.py --close

Ensures proper module resolution by running from skill directory.
"""

import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from textwrap import dedent, indent

import asyncio
import aiohttp

# Change to script directory for proper module resolution
script_dir = Path(__file__).parent.resolve()
os.chdir(script_dir)

SESSION_FILE = Path("/tmp/pw-session.json")
DEFAULT_CDP_PORT = 9222


def check_playwright_installed():
    """Check if Playwright is installed."""
    try:
        import playwright

        return True
    except ImportError:
        return False


def get_code_to_execute(args):
    """Get code to execute from various sources.

    Args:
        args: list of positional arguments (file path, inline code, etc.)
    """
    # Case 1: File path provided
    if args and "\n" not in args[0] and len(args[0]) < 256 and Path(args[0]).exists():
        file_path = Path(args[0]).resolve()
        print(f"📄 Executing file: {file_path}")
        return file_path.read_text()

    # Case 2: File path-like argument but file doesn't exist
    # Only treat as a file path if it looks like a path (no newlines, short, has
    # path-like characteristics). This avoids misidentifying inline code that
    # happens to contain "/", ".py", or "\" as a file path.
    if (
        args
        and "\n" not in args[0]
        and len(args[0]) < 256
        and (".py" in args[0] or "/" in args[0] or "\\" in args[0])
    ):
        print(f"❌ File not found: {args[0]}", file=sys.stderr)
        print(
            "⏱️  This may be a race condition - the file may still be being written.",
            file=sys.stderr,
        )
        print("💡 Try running the command again or wait a moment.", file=sys.stderr)
        sys.exit(1)

    # Case 3: Inline code provided as argument
    if args:
        print("⚡ Executing inline code")
        return " ".join(args)

    # Case 4: Code from stdin
    if not sys.stdin.isatty():
        print("📥 Reading from stdin")
        return sys.stdin.read()

    # No input
    print("❌ No code to execute", file=sys.stderr)
    print("Usage:", file=sys.stderr)
    print("  uv run run.py script.py          # Execute file", file=sys.stderr)
    print("  uv run run.py 'code here'        # Execute inline", file=sys.stderr)
    print("  cat script.py | uv run run.py    # Execute from stdin", file=sys.stderr)
    sys.exit(1)


def cleanup_old_temp_files():
    """Clean up old temporary execution files from previous runs."""
    try:
        files = [
            f
            for f in script_dir.iterdir()
            if f.name.startswith(".temp-execution-") and f.suffix == ".py"
        ]

        for file in files:
            try:
                file.unlink()
            except (OSError, IOError):
                pass
    except (OSError, IOError):
        pass


def wrap_code_if_needed(code):
    """Wrap code in async function if not already wrapped."""
    has_pep723 = "# ///" in code and "script" in code.lower()
    has_import = "from playwright" in code or "import playwright" in code
    has_sync_playwright = "sync_playwright()" in code
    has_main = "def main():" in code or "if __name__" in code

    if has_pep723 or (has_import and (has_sync_playwright or has_main)):
        return code

    if not has_import:
        return f'''from playwright.sync_api import sync_playwright
from lib.helpers import *

# Extra headers from environment variables (if configured)
__extra_headers = get_extra_headers_from_env()

def get_context_options_with_headers(options=None):
    """Merge environment headers into context options."""
    if options is None:
        options = {{}}
    if not __extra_headers:
        return options
    return {{
        **options,
        'extra_http_headers': {{
            **__extra_headers,
            **options.get('extra_http_headers', {{}})
        }}
    }}

def main():
    {code}

if __name__ == "__main__":
    main()
'''

    return f"""def main():
    {code}

if __name__ == "__main__":
    main()
"""


def execute_code_as_module(code):
    """Write code to a temp file, import and execute it as a module."""
    import importlib.util

    temp_file = script_dir / f".temp-execution-{time.time()}.py"
    try:
        temp_file.write_text(code)
        spec = importlib.util.spec_from_file_location("temp_module", temp_file)
        if spec is None:
            raise RuntimeError(f"Failed to load module spec from {temp_file}")
        if spec.loader is None:
            raise RuntimeError(f"Failed to load module loader from {temp_file}")
        module = importlib.util.module_from_spec(spec)
        sys.modules["temp_module"] = module
        spec.loader.exec_module(module)

        main_fn = getattr(module, "main", None)
        if callable(main_fn):
            main_fn()
    finally:
        try:
            temp_file.unlink()
        except (OSError, IOError):
            pass


async def detect_dev_servers(custom_ports=None):
    """Detect running dev servers on common ports."""
    if custom_ports is None:
        custom_ports = []

    common_ports = [3000, 3001, 3002, 5173, 8080, 8000, 4200, 5000, 9000, 1234]
    all_ports = sorted(set(common_ports + custom_ports))
    detected_servers = []

    print("🔍 Checking for running dev servers...")

    async def check_port(port):
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=0.5)
            ) as session:
                async with session.head(f"http://localhost:{port}") as response:
                    if response.status < 500:
                        return f"http://localhost:{port}"
        except (aiohttp.ClientError, asyncio.TimeoutError):
            pass
        return None

    tasks = [check_port(port) for port in all_ports]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if result and isinstance(result, str):
            detected_servers.append(result)
            print(f"  ✅ Found server on port {result.split(':')[2]}")

    if not detected_servers:
        print("  ❌ No dev servers detected")

    return detected_servers


# ---------------------------------------------------------------------------
# Interactive browser session helpers
# ---------------------------------------------------------------------------


def _find_chromium_binary():
    """Find an available Chromium/Chrome binary on the system."""
    import shutil

    for name in ("chromium", "chromium-browser", "google-chrome"):
        path = shutil.which(name)
        if path:
            return path
    return None


def _read_session():
    """Read the session state file. Returns dict or None."""
    try:
        return json.loads(SESSION_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _write_session(pid, port):
    """Write session state file."""
    SESSION_FILE.write_text(json.dumps({"pid": pid, "port": port}))


def _is_port_open(port, timeout=0.3):
    """Check if a TCP port is accepting connections."""
    try:
        with socket.create_connection(("localhost", port), timeout=timeout):
            return True
    except (ConnectionRefusedError, OSError):
        return False


def wait_for_cdp(port, timeout=10.0):
    """Poll until the CDP port is reachable."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _is_port_open(port):
            return True
        time.sleep(0.3)
    return False


def launch_browser(url=None, port=DEFAULT_CDP_PORT):
    """Launch Chromium with CDP enabled. Returns the PID."""
    binary = _find_chromium_binary()
    if binary is None:
        print(
            "❌ No Chromium/Chrome binary found (tried chromium, chromium-browser, google-chrome)",
            file=sys.stderr,
        )
        sys.exit(1)

    cmd = [
        binary,
        f"--remote-debugging-port={port}",
        "--no-first-run",
        "--no-default-browser-check",
    ]
    if url:
        cmd.append(url)

    proc = subprocess.Popen(
        cmd,
        stdout=open("/tmp/chromium-cdp.log", "w"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )

    _write_session(proc.pid, port)
    print(f"Browser launched on CDP port {port} (PID {proc.pid})")
    return proc.pid


def run_cdp_scriptlet(code, port):
    """Wrap user code in the CDP connect template and execute it."""
    code = dedent(code).strip()
    wrapped = (
        dedent(
            f"""\
        from playwright.sync_api import sync_playwright

        p = sync_playwright().start()
        browser = p.chromium.connect_over_cdp("http://localhost:{port}")
        page = browser.contexts[0].pages[0]
        try:
        """
        )
        + indent(code, "    ")
        + "\n"
        + dedent(
            """\
        finally:
            p.stop()
        """
        )
    )
    execute_code_as_module(wrapped)


def close_browser():
    """Kill the browser process and remove the session file."""
    session = _read_session()
    if session is None:
        print("No active browser session found.")
        return

    pid = session["pid"]
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Browser (PID {pid}) terminated.")
    except ProcessLookupError:
        print(f"Browser (PID {pid}) was already stopped.")

    try:
        SESSION_FILE.unlink()
    except FileNotFoundError:
        pass


def _build_parser():
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        description="Universal Playwright Executor for Claude Code",
    )
    parser.add_argument(
        "--open",
        nargs="?",
        const="",
        default=None,
        metavar="URL",
        help="Launch Chromium with CDP. Optionally navigate to URL.",
    )
    parser.add_argument(
        "--cdp",
        nargs="?",
        const="",
        default=None,
        metavar="CODE",
        help="Run a scriptlet against the live CDP browser.",
    )
    parser.add_argument(
        "--close",
        action="store_true",
        help="Kill the browser and remove the session file.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_CDP_PORT,
        help=f"CDP port (default {DEFAULT_CDP_PORT}).",
    )
    return parser


def main():
    """Main execution function."""
    parser = _build_parser()
    known, remaining = parser.parse_known_args()

    is_interactive = known.open is not None or known.cdp is not None or known.close

    # ── Interactive session modes ──────────────────────────────────────
    if is_interactive:
        if known.close:
            close_browser()
            return

        port = known.port

        # --open (with optional --cdp)
        if known.open is not None:
            url = known.open or None
            launch_browser(url=url, port=port)

            if known.cdp is not None:
                if not wait_for_cdp(port):
                    print(
                        f"❌ CDP port {port} did not become reachable in time.",
                        file=sys.stderr,
                    )
                    sys.exit(1)
                cdp_code = get_code_to_execute([known.cdp] if known.cdp else [])
                run_cdp_scriptlet(cdp_code, port)
            return

        # --cdp without --open
        if known.cdp is not None:
            session = _read_session()
            if session:
                port = session["port"]

            if not _is_port_open(port):
                print(
                    f"❌ No browser session found on port {port} — did you run --open?",
                    file=sys.stderr,
                )
                sys.exit(1)

            cdp_code = get_code_to_execute([known.cdp] if known.cdp else [])
            run_cdp_scriptlet(cdp_code, port)
            return

    # ── Default mode (existing behaviour) ─────────────────────────────
    print("🎭 Playwright Skill - Universal Executor\n")
    cleanup_old_temp_files()

    raw_code = get_code_to_execute(remaining)
    code = wrap_code_if_needed(raw_code)

    print("🚀 Starting automation...\n")
    try:
        execute_code_as_module(code)
    except Exception as error:
        print(f"❌ Execution failed: {error}", file=sys.stderr)
        import traceback

        print("\n📋 Stack trace:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
