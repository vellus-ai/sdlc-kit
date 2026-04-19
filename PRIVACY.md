# Privacy Policy — SDLC Kit

**Effective date:** 2026-04-18
**Maintainer:** Vellus AI · milton.antonio.jr@gmail.com
**Repository:** https://github.com/vellus-ai/sdlc-kit

---

## What this plugin does with your data

**Nothing leaves your machine.** SDLC Kit is a local-first plugin:

- Reads and writes Markdown files inside the `.sdlc/` folder of the
  Git repository where you invoke it.
- Maintains a local SQLite tracker at `.sdlc-kit/db.sqlite` (same repo).
- Renders a dashboard from those local files via the browser's
  File System Access API. No upload, no remote rendering.

## What this plugin does NOT do

- ❌ No telemetry, analytics, or "phone-home" calls.
- ❌ No HTTP requests to Vellus AI servers, Anthropic servers, or any
  third party.
- ❌ No collection of user names, IPs, project contents, or usage data.
- ❌ No background processes, no persistent daemons.

## Third-party data flows

- The PostToolUse hook only emits an `additionalContext` cue back into
  Claude Code's local process — Claude Code itself decides whether/how
  to send that to Anthropic per its own privacy policy.
- The optional `gh` CLI integration (used by `/sdlc-kit:worktree` to read
  PR status) talks to GitHub on your behalf, governed by GitHub's own
  privacy policy and your local `gh auth` credentials.

## Your data, your responsibility

The `.sdlc/` vault is part of your Git repository. If you push it to a
public remote, anyone with access sees it. The plugin makes no effort to
mask, redact, or sandbox any content you write into it.

## Contact

Privacy questions or data requests:
**[milton.antonio.jr@gmail.com](mailto:milton.antonio.jr@gmail.com)**.

## Changes

This policy is versioned in the repo. Updates appear in the commit log
and in the project [`CHANGELOG.md`](./CHANGELOG.md).
