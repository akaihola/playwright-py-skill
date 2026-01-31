# Interactive Browser Session Mode

## Summary

This document describes a technique for driving a live browser interactively from Claude Code
using Chromium's remote debugging protocol (CDP) and short one-shot Python commands. Instead of
writing a single monolithic script and hoping it works, the agent launches a persistent browser
and sends small inspection/action commands one at a time, observing results between each step.

This approach was developed during a real session automating the Finnish Meteorological
Institute website (fmi.fi) where the monolithic-script approach failed repeatedly because the
page structure was unknown and the React-based UI behaved in ways that couldn't be predicted
upfront.

## Why the current approach fails for unknown pages

The existing skill workflow is:

1. Write a complete script to `/tmp/playwright-test-*.py`
2. Execute it via `cd $SKILL_DIR && uv run run.py /tmp/script.py`
3. Hope it works; if not, rewrite and re-execute

Problems:

- **Blind scripting**: The agent guesses at selectors, element visibility, and page behavior
  without seeing the actual DOM.
- **No feedback loop**: Each attempt launches a fresh browser, navigates from scratch, and
  either succeeds or fails entirely.
- **Wasted context**: Each rewrite consumes context window tokens for the full script, error
  output, and the rewritten script.
- **Stale browser left on screen**: When a script hangs waiting for a non-existent element, the
  browser window sits open indefinitely with no way to recover.

## The interactive approach

### Step 1: Launch a persistent browser with CDP

```bash
nohup chromium --remote-debugging-port=9222 \
  --no-first-run --no-default-browser-check \
  https://www.fmi.fi/paikallissaa > /tmp/chromium.log 2>&1 &
echo $!
```

Key points:

- `--remote-debugging-port=9222` enables the Chrome DevTools Protocol endpoint.
- `nohup` and `&` keep the browser running independently of the shell.
- Save the PID to kill it later.
- Optionally navigate to the target URL directly in the launch command.

### Step 2: Connect and inspect with short one-shot commands

Each command connects, does one thing, and disconnects (the browser stays open):

```bash
uvx --with=playwright==1.57.0 python -c "
from playwright.sync_api import sync_playwright
p = sync_playwright().start()
browser = p.chromium.connect_over_cdp('http://localhost:9222')
page = browser.contexts[0].pages[0]
print('Title:', page.title())
print('URL:', page.url)
p.stop()
"
```

Critical details:

- `page.url` is a **property**, not a method. Don't call `page.url()`.
- `p.stop()` cleanly disconnects the Playwright client. The browser stays running.
- `browser.contexts[0].pages[0]` gets the first tab of the first browser context.

### Step 3: Inspect the DOM with `page.evaluate()`

This is the core power of the interactive approach — running JavaScript in the page:

```bash
uvx --with=playwright==1.57.0 python -c "
from playwright.sync_api import sync_playwright
p = sync_playwright().start()
browser = p.chromium.connect_over_cdp('http://localhost:9222')
page = browser.contexts[0].pages[0]
info = page.evaluate('''() => Array.from(document.querySelectorAll('input')).map((el, i) => ({
  i, visible: el.offsetParent !== null, placeholder: el.placeholder,
  value: el.value, ariaExpanded: el.ariaExpanded,
  rect: el.getBoundingClientRect(),
  parentHTML: el.parentElement.outerHTML.substring(0, 120)
}))''')
for x in info: print(x)
p.stop()
"
```

Useful inspection patterns:

| Goal                             | JavaScript                                                         |
| -------------------------------- | ------------------------------------------------------------------ |
| All inputs with metadata         | `Array.from(document.querySelectorAll('input')).map(...)`          |
| Container HTML around an element | `el.closest('[class*=\"combobox\"]').outerHTML.substring(0, 2000)` |
| Visibility check                 | `el.offsetParent !== null`                                         |
| Bounding rect                    | `el.getBoundingClientRect()`                                       |
| ARIA attributes                  | `el.ariaExpanded`, `el.getAttribute('aria-controls')`              |
| Find by role                     | `document.querySelectorAll('[role=option]')`                       |
| Full page text                   | `document.body.innerText.split(String.fromCharCode(10))`           |

### Step 4: Interact — click, type, observe

Each interaction is a separate command so the agent can observe results:

**Type into an input:**

```bash
uvx --with=playwright==1.57.0 python -c "
from playwright.sync_api import sync_playwright
import time
p = sync_playwright().start()
browser = p.chromium.connect_over_cdp('http://localhost:9222')
page = browser.contexts[0].pages[0]
inp = page.locator('input').nth(1)
inp.click()
inp.type('Espoo', delay=100)
time.sleep(2)
# Check what appeared
val = inp.evaluate('el => el.value')
expanded = inp.evaluate('el => el.ariaExpanded')
print(f'Value: {val}, expanded: {expanded}')
# Check for dropdown options
options = page.evaluate('''() => Array.from(document.querySelectorAll('[role=option]'))
  .slice(0,10).map(el => ({text: el.innerText.substring(0,60), dataValue: el.getAttribute('data-value')}))''')
print('Options:', options)
p.stop()
"
```

**Click a dropdown option:**

```bash
uvx --with=playwright==1.57.0 python -c "
from playwright.sync_api import sync_playwright
import time
p = sync_playwright().start()
browser = p.chromium.connect_over_cdp('http://localhost:9222')
page = browser.contexts[0].pages[0]
page.locator('[role=option]:has-text(\"Espoo\")').first.click()
time.sleep(3)
print('URL:', page.url)
print('Title:', page.title())
p.stop()
"
```

**Extract final data:**

```bash
uvx --with=playwright==1.57.0 python -c "
from playwright.sync_api import sync_playwright
p = sync_playwright().start()
browser = p.chromium.connect_over_cdp('http://localhost:9222')
page = browser.contexts[0].pages[0]
lines = page.evaluate('() => document.body.innerText.split(String.fromCharCode(10)).filter(l => l.trim()).slice(0, 60)')
for line in lines: print(line)
p.stop()
"
```

### Step 5: Clean up

```bash
kill <PID>
```

## Lessons learned from the fmi.fi session

### 1. Two inputs that swap visibility

The FMI weather page has two `<input>` elements. Only one is visible at a time. After
interacting with input 0, it became invisible (`offsetParent === null`, rect all zeros) and
input 1 became visible. The agent discovered this by checking visibility between steps.

### 2. `fill()` vs `type()` for React/Vue apps

`page.locator.fill('text')` sets the value directly, which may not trigger React/Vue event
handlers. `page.locator.type('text', delay=100)` simulates keystrokes and reliably triggers
autocomplete/combobox behavior. Use `type()` for modern SPA pages with custom input
components.

### 3. cmdk-style combobox pattern

The search was a `cmdk`-style combobox (common in modern React apps):

- Input has `role="combobox"` and `aria-controls="reka-combobox-content-v-10"`
- Typing triggers a search, results appear as `[role="option"]` elements
- The placeholder text ("Syötä sijainti") is rendered as a separate `<span>` overlay, not as
  an HTML `placeholder` attribute — so searching by `input[placeholder=...]` fails.

### 4. Unicode characters in `page.evaluate()` JS strings

The `°` character in the page text caused `SyntaxError` when used inside JavaScript string
literals passed via `page.evaluate()`. Workaround: use `String.fromCharCode(10)` for newline
splitting instead of `\n` when the page content contains special characters, or avoid matching
`°` in JS-side regex and filter in Python instead.

### 5. Domain redirects

`www.fmi.fi` redirects to `www.ilmatieteenlaitos.fi`. The agent discovered this by checking
`page.url` after navigation — information that would have been missed in a blind script.

## Comparison with current approach

| Aspect                      | Monolithic script                   | Interactive session         |
| --------------------------- | ----------------------------------- | --------------------------- |
| DOM visibility              | None (guessing)                     | Full JS inspection          |
| Feedback loop               | None (write → run → fail → rewrite) | Immediate per-step          |
| Recovery from errors        | Restart from scratch                | Continue from current state |
| Context window cost         | High (full script × N attempts)     | Low (short commands)        |
| Browser lifecycle           | Fresh each attempt                  | Single persistent instance  |
| Time to first useful result | Minutes (multiple rewrites)         | Seconds (incremental)       |

## Proposed feature for the skill

### Three new CLI operations

Extend `run.py` with `--open`, `--cdp`, and `--close`. The existing default mode (complete
script execution) stays unchanged.

| Operation           | Purpose                                                            |
| ------------------- | ------------------------------------------------------------------ |
| `--open [URL]`      | Launch Chromium with CDP, save state file, leave browser running   |
| `--cdp CODE`        | Connect to live browser, run scriptlet, disconnect (browser stays) |
| `--open --cdp CODE` | Launch browser **and** run the first scriptlet in one call         |
| `--close`           | Kill the browser process, remove state file                        |

### API

```bash
# Launch persistent browser, optionally navigate to a URL
cd $SKILL_DIR && uv run run.py --open https://www.fmi.fi/paikallissaa
# Output: Browser launched on CDP port 9222 (PID 12345)

# Launch and run the first scriptlet in one shot
cd $SKILL_DIR && uv run run.py --open https://www.fmi.fi/paikallissaa --cdp '
print(page.title())
print(page.url)
'

# Run a quick command against the live browser
cd $SKILL_DIR && uv run run.py --cdp '
print(page.title())
print(page.url)
'
# The wrapper auto-connects, provides `page`, `browser`, and `p` variables,
# auto-disconnects.

# Code from file or stdin also works with --cdp
cd $SKILL_DIR && uv run run.py --cdp /tmp/inspect.py
cat /tmp/inspect.py | cd $SKILL_DIR && uv run run.py --cdp

# Close the browser
cd $SKILL_DIR && uv run run.py --close
```

### CDP scriptlet wrapping

When `--cdp` is used, the user code is injected into this template:

```python
from playwright.sync_api import sync_playwright

p = sync_playwright().start()
browser = p.chromium.connect_over_cdp(f"http://localhost:{port}")
page = browser.contexts[0].pages[0]
try:
    # --- user code starts here (indented into the try block) ---
    print(page.title())
    # --- user code ends here ---
finally:
    p.stop()
```

The agent writes only the body; `page`, `browser`, and `p` are pre-bound. The `finally`
block ensures `p.stop()` runs even if the scriptlet raises.

### Code input for `--cdp` (reuses existing logic)

The same `get_code_to_execute()` function handles all three input sources for `--cdp`:

1. If the argument after `--cdp` is a path to an existing `.py` file → read from file.
2. If it's a non-empty string → inline code.
3. If stdin is not a TTY → read from stdin.

This avoids duplicating the input-source logic.

### `--open` implementation

- Find chromium binary (`chromium`, `chromium-browser`, `google-chrome`, in order).
- Launch with `subprocess.Popen` detached from the controlling terminal (equivalent to
  `nohup ... &`), passing `--remote-debugging-port=9222 --no-first-run
--no-default-browser-check` and optionally the URL argument.
- Write state to `/tmp/pw-session.json`: `{"pid": 12345, "port": 9222}`.
- Print confirmation and return.

### `--close` implementation

- Read `/tmp/pw-session.json`.
- `os.kill(pid, signal.SIGTERM)`.
- Remove the state file.
- Handle "already dead" gracefully.

### `--open --cdp` combination

When both flags are present, `run.py`:

1. Launches the browser (as `--open`).
2. Waits briefly for the CDP endpoint to become reachable (poll with short timeout).
3. Runs the scriptlet (as `--cdp`).

This lets the agent do "open browser and check the page title" in one invocation.

### Code organization in `run.py`

Refactor `main()` to dispatch based on which flags are present:

```
parse args (argparse)
├─ --open (with optional --cdp)
│   ├─ launch_browser(url, port) → writes state file
│   ├─ if --cdp: wait_for_cdp(port) → run_cdp_scriptlet(code, port)
│   └─ return
├─ --cdp (without --open)
│   ├─ read port from state file
│   └─ run_cdp_scriptlet(code, port)
├─ --close
│   ├─ read state file → kill PID → remove state file
│   └─ return
└─ default (no flags) → existing behavior unchanged
```

Key shared functions:

- `get_code_to_execute(args)` — refactored to accept an explicit arg list instead of reading
  `sys.argv`, so it can be called from both the default mode and `--cdp` mode.
- `execute_code_as_module(code)` — extracted from current `main()`, handles temp file
  creation, importlib loading, and cleanup.
- `run_cdp_scriptlet(code, port)` — wraps user code in the CDP connect template, then calls
  `execute_code_as_module()`.

### Design decisions (v1 scope)

1. **State file**: `/tmp/pw-session.json`. Single file, single session.
2. **Error handling**: `--cdp` checks if the CDP port is reachable before connecting. If not,
   prints a clear error ("No browser session found — did you run `--open`?").
3. **`--port`**: Optional flag for `--open`, defaults to 9222. Stored in the state file so
   `--cdp` and `--close` don't need it.

Features deferred to v2 (multiple sessions, timeout/watchdog, `--inspect` helpers) are
documented in `interactive-browser-session-v2.md`.
