# Interactive Browser Session — v2 Features

These features were explicitly deferred in the v1 design document
(`interactive-browser-session.md`) and are collected here for future implementation.

---

## 1. Multiple concurrent sessions

> From v1 doc § "Design decisions": "Multiple sessions: Deferred to v2. One browser at a time
> for now."

### Requirements

- Support multiple browser instances, each with its own CDP port and PID.
- The state file (`/tmp/pw-session.json`) becomes a dictionary keyed by session name or port.
- `--open`, `--cdp`, and `--close` accept an optional `--session NAME` or `--port PORT` to
  target a specific instance.
- Default behavior (no `--session`) targets the most recently opened session.

---

## 2. Timeout / watchdog

> From v1 doc § "Design decisions": "Timeout/watchdog: Deferred. Agent is responsible for
> `--close`."

### Requirements

- Auto-kill the browser after a configurable idle timeout (e.g. 10 minutes with no `--cdp`
  command).
- Implement as a background thread or a separate watchdog process that checks the session
  file's mtime.
- `--cdp` commands touch the session file to reset the timer.
- `--open --timeout 300` sets a custom timeout in seconds.

---

## 3. `--inspect` helper commands

> From v1 doc § "Design decisions": "`--inspect` helpers: Deferred to v2. The boilerplate
> elimination is the high-value change; the agent can write its own `page.evaluate()` JS."

### Requirements

Built-in inspection shortcuts that eliminate repetitive `page.evaluate()` boilerplate:

| Command                        | Equivalent to                                           |
| ------------------------------ | ------------------------------------------------------- |
| `--inspect inputs`             | List all `<input>` elements with visibility, value, etc |
| `--inspect links`              | List all `<a>` elements with href and text              |
| `--inspect text`               | Full visible page text (first 200 lines)                |
| `--inspect selectors SELECTOR` | Query a CSS selector and return element metadata        |
| `--inspect screenshot [PATH]`  | Take a screenshot, save to given path or default        |

These should be implemented as named scriptlet templates, not hardcoded logic — making it easy
to add new inspectors.
