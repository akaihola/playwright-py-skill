# Error Analysis: Interactive Browser Session (fmi.fi tests)

## Context

This document catalogs errors encountered during real sessions using the interactive browser
mode (`--open`, `--cdp`, `--close`) to scrape fmi.fi temperature forecasts, and diagnoses each
against the design in `interactive-browser-session.md`.

Two sessions have been analyzed:

- **Session 1** (2025-01-31): Original session that discovered Errors 1–4.
- **Session 2** (2025-01-31, ses_3ead6a6a): Follow-up session with claude-haiku-4-5. Confirmed
  Errors 1 and 3 still reproduce, and revealed a new variant of Error 2.

---

## Error 1: IndentationError when using `--open` with `--cdp` multiline inline code

### What happened

```bash
uv run run.py --open https://www.fmi.fi --cdp '
print("Title:", page.title())
print("URL:", page.url)
'
```

Produced:

```
IndentationError: unexpected indent
```

in the generated temp file at line 1 (`from playwright.sync_api import sync_playwright`).

### Root cause

The `--cdp` value was a multiline string starting with `\n`. In `run_cdp_scriptlet()`, the
user code was indented and inserted into a `try:` block. The original implementation used
f-string interpolation with `dedent()`:

```python
wrapped = dedent(f"""\
    from playwright.sync_api import sync_playwright
    ...
    try:
    {indent(code, "    ")}
    finally:
    ...
""")
```

This caused the first line of interpolated code to inherit the template's indentation position
(8 spaces), but subsequent lines only had 4 spaces from `indent()`. After `dedent()` normalized
the common prefix, the code lines ended up with inconsistent indentation relative to `try:`.

### Diagnosis

The template structure interaction with f-string interpolation and `dedent()` caused improper
indentation normalization. The fix requires **splitting the template into three parts** to avoid
this interaction: preamble through `try:`, user code (indented), and the `finally:` block.

### Fix

In `run_cdp_scriptlet()` (run.py:308–327), split the template string to avoid f-string
interpolation of code:

```python
wrapped = (
    dedent(
        f"""\
    from playwright.sync_api import sync_playwright
    ...
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
```

This ensures the user code's indentation is applied cleanly without interaction with `dedent()`.

### Status

✅ **Fixed** (commit: see run.py:305–327)

Comprehensive test coverage added in `tests/test_cdp_scriptlet_wrapping.py` (16 tests):

- Syntax validation with various whitespace patterns
- Regression test for leading newlines
- Port substitution verification
- Indentation consistency checks
- Playwright API support verification

### Session 2 update

**Original concern resolved.** The regression in Session 2 (file-path `--cdp` also failing)
was caused by the incomplete f-string-based fix. The new template-splitting approach fixes
both inline code and file-path code paths uniformly.

---

## Error 2: OSError ENAMETOOLONG when `--cdp` receives multiline inline code

### What happened

```bash
uv run run.py --cdp '
# Handle cookie banner if present
try:
    btn = page.locator("button").filter(has_text="Hyv")
    ...
'
```

Produced:

```
OSError: [Errno 36] File name too long: '\n# Handle cookie banner ...'
```

### Root cause

`get_code_to_execute()` (line 65) does `Path(args[0]).exists()` on the raw argument. When the
argument is a long inline code string rather than a file path, `Path.exists()` calls
`os.stat()` on the entire string. Linux file names are limited to 255 bytes, so the stat call
fails with `ENAMETOOLONG`.

### Diagnosis

The doc (§ "Code input for `--cdp`") says:

> 1. If the argument after `--cdp` is a path to an existing `.py` file → read from file.
> 2. If it's a non-empty string → inline code.

The implementation checks file existence **before** checking if the string looks like inline
code. The `Path(...).exists()` call is not guarded against strings that are clearly not file
paths (e.g. containing newlines, or exceeding OS path length limits).

### Fix

Before calling `Path(args[0]).exists()`, add a guard:

```python
if args and "\n" not in args[0] and len(args[0]) < 256 and Path(args[0]).exists():
```

Or reorder: check for `.py` extension or `/` prefix first, and only then call `.exists()`.

### Session 2 update: "File not found" variant

In Session 2, multiline inline code produced a **different error**:

```
❌ File not found: import time; time.sleep(2); text = page.evaluate("() => ...
⏱️  This may be a race condition - the file may still be being written.
💡 Try running the command again or wait a moment.
```

This happened when the inline code string was short enough to avoid `ENAMETOOLONG` (under 255
bytes) but contained shell metacharacters or quotes that caused the shell to split the argument
differently than expected. The code was treated as a file path, `Path.exists()` returned
`False`, and the "File not found" branch was taken.

**Key observation:** Simple single-line code with only single quotes worked:

```bash
uv run run.py --cdp 'import time; time.sleep(2); print("Title:", page.title())'
# ✅ This worked
```

But longer or more complex inline strings (with escaped quotes, newlines, or special
characters) consistently failed with "File not found." This confirms that the `"\n" not in`
guard alone is insufficient — shell quoting interactions cause some inline strings to be
received by Python as something that doesn't look like inline code.

---

## Error 3: Agent fell back to monolithic script approach

### What happened

After the two errors above with `--cdp`, the agent abandoned the interactive mode and wrote a
full standalone script (`/tmp/playwright-fmi-forecast.py`) that launches its own browser — the
exact "monolithic script" pattern the interactive session feature was designed to replace.

### Diagnosis

This isn't a code bug but an **agent workflow failure**. The agent should have:

1. Diagnosed the `--cdp` errors.
2. Worked around them (e.g. writing the scriptlet to a file and passing the path).
3. Continued using the interactive session pattern.

The workaround was available: the doc says `--cdp /tmp/inspect.py` (file path) is a valid
input form. The agent could have written the scriptlet to a temp file and passed the path
instead of inline code.

### Takeaway

The skill instructions (in `AGENTS.md` or the skill prompt) should emphasize the file-path
workaround when inline code fails, and should discourage falling back to monolithic scripts.

### Session 2 update

Session 2 (claude-haiku-4-5) reproduced this exact pattern. The agent:

1. Tried multiline inline `--cdp` → "File not found" error.
2. Tried file-based `--cdp /tmp/inspect_fmi.py` → `IndentationError`.
3. Tried simple one-liner `--cdp` → worked.
4. Tried more complex inline `--cdp` → "File not found" again.
5. Tried another file-based `--cdp` → `IndentationError` again.
6. Closed the browser session (`--close`).
7. Was about to write a monolithic standalone script when the session ended.

The agent **did** try the file-path workaround (step 2), but it failed due to Error 1. Since
both inline and file-based `--cdp` were broken, the agent had no viable path to continue
interactive mode. This demonstrates that **Error 1 must be fixed first** — the file-path
workaround is the critical fallback, and if it's broken, agents have no choice but to abandon
interactive mode entirely.

---

## Error 4: Cookie banner not handled (silent failure)

### What happened

The monolithic script attempted to handle the cookie banner but the banner was still visible in
the screenshot. The `try/except` swallowed any error silently.

### Diagnosis

This is a consequence of the monolithic approach — no feedback loop. With the interactive
session, the agent would have seen whether the banner was dismissed and could have tried
alternative selectors. Not a bug in the skill code itself, but illustrates the value of the
interactive approach described in the doc.

---

## Summary table

| #   | Error                           | Component             | Severity | Status                 |
| --- | ------------------------------- | --------------------- | -------- | ---------------------- |
| 1   | IndentationError (leading `\n`) | `run_cdp_scriptlet`   | Bug      | ✅ Fixed + tested      |
| 2   | ENAMETOOLONG on inline code     | `get_code_to_execute` | Bug      | Fixed + new variant    |
| 3   | Agent fell back to monolithic   | Agent workflow        | Workflow | Reproduced (Session 2) |
| 4   | Cookie banner not handled       | N/A (monolithic)      | Minor    | N/A                    |

## Key takeaway from Session 2

The file-path `--cdp` workaround is the **critical fallback** when inline code fails. Error 1
(IndentationError in `run_cdp_scriptlet`) breaks this fallback, leaving agents with no working
path for interactive mode. **Fixing Error 1 is the highest priority** — it unblocks both the
file-path workaround and the agent's ability to stay in interactive mode.
