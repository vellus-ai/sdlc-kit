---
name: sdlc-dash
description: |
  Use when the user wants to open the SDLC Kit vault dashboard in their default
  browser — a static `dashboard.html` at the vault root that renders the
  kanban/status view of the current project. Typical triggers are
  `/sdlc-kit:dash`, "open the dashboard", "show the kanban", "show the vault
  dashboard", "open the vault in the browser", or in pt-BR: "abrir dashboard",
  "ver o kanban", "ver o status visual do projeto", "abre o dashboard do
  vault". Locates the current vault via `.sdlc-kit/marker.json` (or the
  explicit `--vault-root`), resolves `<vault>/dashboard.html`, and opens it
  with the OS-native handler — Windows `start`, macOS `open`, Linux
  `xdg-open`. If auto-open fails or is unavailable, prints the absolute path
  so the user can open it manually. Read-only utility; does not scaffold,
  mutate, or re-render the dashboard itself (the dashboard file is maintained
  by `/sdlc-kit:sync`). Do not invoke to *re-render* the dashboard (use
  `/sdlc-kit:sync`), to inspect vault health as JSON (use `/sdlc-kit:status`),
  or when cwd is outside a vault.
---

# sdlc-kit:dash

Opens the vault dashboard (`<vault>/dashboard.html`) in the user's default
browser.

This is a pure utility skill: one lens — **LLM assistant helping the user
navigate the vault**. No reviewer personas, no interview, no content decision.
The skill locates the file and hands it to the OS.

---

## What this skill is (and isn't)

| Dash is… | Dash isn't… |
|---|---|
| A launcher — it finds `dashboard.html` and opens it in the default browser | A renderer — `dashboard.html` is produced/refreshed by `/sdlc-kit:sync`, not here |
| Read-only — it never writes, edits, or deletes anything in the vault | A vault-health inspector — for structured JSON/diagnostic output use `/sdlc-kit:status` |
| Cross-platform — uses `start` (Windows), `open` (macOS), `xdg-open` (Linux) | Guaranteed to succeed — if the OS launcher fails, it falls back to printing the absolute path |
| Idempotent — safe to re-run; opens a fresh browser tab each time | A daemon — it exits immediately after dispatching the open command |

---

## When to invoke

Invoke when:

- The user types `/sdlc-kit:dash`.
- The user says "open the dashboard", "show the kanban", "show me the vault
  board", "open the vault in a browser", or in pt-BR: "abre o dashboard",
  "mostra o kanban", "ver o status visual", "abrir o dashboard do vault".
- After a `/sdlc-kit:sync` completes and the user wants to visually confirm
  the refreshed view.
- Right after `/sdlc-kit:init` as the "here is what your project looks like"
  reveal.

---

## When NOT to invoke

- The user wants to **regenerate** `dashboard.html` (it's missing or stale) →
  use `/sdlc-kit:sync` first.
- The user wants **structured vault-health data** (counts, coverage, gaps) →
  use `/sdlc-kit:status` (JSON) rather than a human-facing browser tab.
- cwd is not inside an SDLC Kit vault (no `.sdlc-kit/marker.json` reachable
  from cwd or from `--vault-root`) → tell the user to run `/sdlc-kit:init`
  instead.
- The user is in a headless environment where no browser is available — in
  that case the fallback path message is still useful; run it and surface the
  printed path.

---

## Pre-checks

1. **Resolve the vault.** Prefer `--vault-root` if the user named one;
   otherwise walk ancestors looking for `.sdlc-kit/marker.json`. If neither
   resolves, surface the "run `/sdlc-kit:init` first" error from the script.
2. **Confirm `dashboard.html` exists** at `<vault>/dashboard.html`. If it's
   missing, the script exits with code `1` and a message pointing at
   `/sdlc-kit:sync` — surface that guidance to the user verbatim.

---

## Flow

1. **Resolve vault** (ancestor walk or `--vault-root`).
2. **Locate** `<vault>/dashboard.html`.
3. **Dispatch** the OS launcher (`start` / `open` / `xdg-open`).
4. **Report** the absolute path and whether the launcher was dispatched
   successfully. If the launcher raised an exception, the script catches it,
   reports `"opened": false`, and still prints the path so the user can open
   it manually.

Invocation:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-dash/scripts/dash.py"
```

With an explicit vault root:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-dash/scripts/dash.py" \
  --vault-root "/abs/path/to/.sdlc"
```

Dry run (resolve and report without launching the browser):

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-dash/scripts/dash.py" --dry-run
```

---

## Output contract

All runs emit a single JSON object on stdout.

```json
// success — launcher dispatched
{
  "status": "ok",
  "path": "/abs/path/to/.sdlc/dashboard.html",
  "opened": true,
  "message": "Dashboard aberto: /abs/path/to/.sdlc/dashboard.html"
}

// success — launcher raised; fall back to manual open
{
  "status": "ok",
  "path": "/abs/path/to/.sdlc/dashboard.html",
  "opened": false,
  "message": "Abra manualmente: /abs/path/to/.sdlc/dashboard.html"
}

// dry run — no launch attempted
{
  "status": "dry-run",
  "path": "/abs/path/to/.sdlc/dashboard.html"
}

// dashboard.html missing — user must run sync first
{
  "status": "error",
  "message": "dashboard.html not found in /abs/path/to/.sdlc — run /sdlc-kit:sync to restore it"
}

// vault not resolved or marker.json missing
{
  "status": "error",
  "message": "vault not found — run /sdlc-kit:init first"
}
```

**Exit codes:**

- `0` — `ok` or `dry-run` (including the "launcher raised, path printed"
  fallback — the script still considers that a successful resolve).
- `1` — dashboard file missing (actionable: run `/sdlc-kit:sync`).
- `2` — vault not resolved or `.sdlc-kit/marker.json` missing (actionable:
  run `/sdlc-kit:init` or pass `--vault-root`).

Note: the current script's `message` string is pt-BR when `opened == true`
and the fallback message is also pt-BR. The skill is free to translate it
when surfacing to the user, but must not mutate the JSON itself.

---

## Guardrails

**Never:**

- Attempt to create, rewrite, or "repair" `dashboard.html` from this skill.
  If the file is missing, redirect to `/sdlc-kit:sync`.
- Modify any other vault file — this skill is read-only by contract.
- Pass `shell=True` arguments from user-controlled data. The script already
  hard-codes the OS launcher; don't add an `--open-command` escape hatch.
- Silently swallow the "dashboard missing" error — surface the
  `/sdlc-kit:sync` hint so the user has an obvious next step.
- Use this skill to inspect vault health or emit diagnostics — that's
  `/sdlc-kit:status`.

**Always:**

- Mirror the user's active chat language when summarising the result.
- Surface the absolute path in the final response so the user can click/copy
  it even when the browser didn't pop up (SSH session, headless shell,
  locked-down desktop, etc.).
- Treat `"opened": false` as a soft success, not a failure — the file is
  valid and the user can still open it manually.

---

## Examples

> Examples below are in English. In a real session, mirror the user's active
> conversation language in every user-facing line.

**Happy path — desktop shell:**

```
User: /sdlc-kit:dash
AI:   [dash.py]
AI:   "Dashboard opened in your default browser:
       /home/milton/projects/checkout/.sdlc/dashboard.html"
```

**Fallback — launcher couldn't open a window (headless / no DE):**

```
User: /sdlc-kit:dash
AI:   [dash.py → status=ok, opened=false]
AI:   "Couldn't auto-open a browser from this shell. Open it manually:
       /home/milton/projects/checkout/.sdlc/dashboard.html"
```

**Missing dashboard — redirect to sync:**

```
User: /sdlc-kit:dash
AI:   [dash.py → status=error, exit=1]
AI:   "No dashboard.html at the vault root yet. Run /sdlc-kit:sync first —
       that's what renders the kanban/status view — and then re-run
       /sdlc-kit:dash."
```
