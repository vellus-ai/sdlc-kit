# sdlc-kit:review — full flow

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; abort if missing.
2. **Python 3.10+** available.
3. **Template exists** at `<vault>/07-retrospectives/_templates/review.md.tpl`.

## The expert duo

Announce at the start:
> "I'll author this review as a duo: **Senior Engineer (Code Reviewer)** for design / quality / tests, and **AppSec Engineer** for security / privacy / secrets. Both lenses pass through every section before we record the decision."

| Section | Code Reviewer lens | AppSec lens |
|---|---|---|
| §1 Design & architecture | Pattern fit, separation, abstraction quality | Trust boundaries, no security-through-obscurity, threat model matches reality |
| §2 Code quality | Naming, readability, DRY/YAGNI, error handling | Error paths don't leak internals; failure modes safe-default |
| §3 Tests | Coverage on changed files, behavior over impl, PBT where useful | Negative-path tests (auth fail, validation fail, expired token); fuzz where input parsing critical |
| §4 AppSec | — | Full pass: injection, AuthN/AuthZ, secrets, supply chain, SSRF/CORS, rate limiting, error model, crypto |
| §5 Privacy & LGPD | — | Minimization, masking, subject rights, retention, consent, audit trail |
| §6 Process & delivery | Conventional Commits, CI status, docs/ADR/TRD updates, rollback plan | Observability covers security signals (auth failures, anomaly metrics) |

§4–§5 are AppSec-only — but Code Reviewer must confirm AppSec walked them. If
genuinely N/A (docs-only PR), say so explicitly in §Findings.

## Flow

### List: `/sdlc-kit:review` or `/sdlc-kit:review list`

1. Run `review.py --action list`.
2. Show: `slug | status | decision | reviewer | pr | title | updated`.
3. Offer next: open draft, finalize, decide, or new.

### New: `/sdlc-kit:review new <pr-or-title>`

1. **Derive slug.** Default `pr-<NNNN>-<short-topic>` (zero-pad PR number to 4). Allow override.
2. **Capture metadata up front** for the frontmatter:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-review/scripts/review.py" \
     --vault-root "<vault>" --action scaffold \
     --slug "pr-0042-login-google" \
     --title "PR #42 — Login with Google" \
     --pr "42" --pr-url "https://github.com/org/repo/pull/42" \
     --author "alice"
   ```
3. **Announce the duo** and walk the interview.

### The interview (LLM-driven, duo, section by section)

**Phase A — Scope & metadata**
1. **Metadata.** Confirm/fill PR number, URL, author, branch, files changed, lines ±, CI status.
2. **Scope.** What does the PR do (1–2 paragraphs)? What is intentionally **out of scope**? Link feature design, tasks, ADRs, TRDs.

**Phase B — Six-section checklist**

For each §1–§6, walk boxes and tick what's clean. **Anything left unchecked must produce a Finding** explaining why — silent unchecks are forbidden.

| # | Section | Owner lens | Minimum bar |
|---|---|---|---|
| 1 | Design & architecture | Code Reviewer | Pattern fit, no upward dependencies, no leaked abstractions |
| 2 | Code quality | Code Reviewer | Clear naming, no duplication, errors handled at right boundary |
| 3 | Tests | Code Reviewer | Coverage on changed files, edge cases, behavior-not-impl |
| 4 | AppSec | AppSec | Injection / AuthN / AuthZ / secrets / supply chain / SSRF / rate limit / error model / crypto |
| 5 | Privacy & LGPD | AppSec | Minimization / masking / subject rights / retention / consent / audit trail |
| 6 | Process & delivery | Both | Conventional Commits, CI green, docs updated, rollback plan, observability updated |

**Phase C — Findings**

Each finding carries:
- **File:** `path/file.ext:NNN` (never just "somewhere in the diff").
- **Problem:** what is wrong **and why it matters** (security risk / correctness / maintainability / user impact).
- **Suggestion:** concrete fix — diff sketch, alternative API, missing test scenario.

Severity rules:
- **🔴 Blocker** — must fix before merge. Examples: secret committed; AuthZ missing on new endpoint; data race on shared mutable; LGPD masking absent on new PII; SQL string concat; feature without any test.
- **🟡 Major** — should fix; merge can proceed only with explicit author+reviewer agreement (write a follow-up).
- **🟢 Minor / Nit** — polish, optional.
- **🔵 Praise** — what the author got right. Always include ≥ 1 when there is something to praise.

**Phase D — Decision**

Set `decision:` via `decide`. Any `changes-requested` **must** name ≥ 1 🔴 Blocker.

### Finalize: `/sdlc-kit:review finalize <slug>`

Flips `status: draft → final` — the act of *delivering* the review.

```bash
python "...review.py" --vault-root "<vault>" --action transition \
  --slug "<slug>" --to "final"
```

**Pre-finalize checklist:**
- [ ] All six sections walked; every unchecked box has a Finding.
- [ ] Every Finding has location + problem + suggestion.
- [ ] Decision is set (not `pending`).
- [ ] If decision is `changes-requested`, ≥ 1 🔴 Blocker exists.
- [ ] Both Code Reviewer and AppSec lenses acknowledged.

Idempotent.

### Decide: `/sdlc-kit:review {approve|approve-with-comments|request-changes} <slug>`

| Verb | Target decision | When |
|---|---|---|
| `approve` | `approved` | No changes required. Safe to merge. No 🔴, no 🟡 the reviewer wants enforced. |
| `approve-with-comments` | `approved-with-comments` | Merge allowed; suggestions optional. |
| `request-changes` | `changes-requested` | Mandatory fixes. **Must** name ≥ 1 🔴 Blocker. |
| (raw) | `pending` | Resets — rare; for re-evaluation. |

```bash
python "...review.py" --vault-root "<vault>" --action decide \
  --slug "<slug>" --to "<approved|approved-with-comments|changes-requested|pending>"
```

Idempotent.

**Decision is independent from finalize** — two axes:
- `decide` first, then `finalize` — most common.
- `finalize` first, then `decide` — rare; smell.

### Sync

After every `scaffold`, `transition`, or `decide`, invoke `/sdlc-kit:sync`.

## Output contract

```json
// --action list
{
  "status": "ok", "action": "list",
  "vault_root": "/abs/path/.sdlc",
  "reviews": [
    {"slug": "pr-0042-login-google",
     "path": "07-retrospectives/reviews/pr-0042-login-google.md",
     "title": "PR #42 — Login with Google",
     "status": "final", "decision": "approved-with-comments",
     "reviewer": "Milton", "author": "alice", "pr": "42",
     "updated": "2026-04-17"}
  ],
  "count": 1, "errors": []
}

// --action scaffold
{
  "status": "ok", "action": "scaffold",
  "slug": "pr-0042-login-google",
  "review_path": "07-retrospectives/reviews/pr-0042-login-google.md",
  "was_new": true, "errors": []
}

// --action transition
{
  "status": "ok", "action": "transition",
  "slug": "pr-0042-login-google",
  "previous_status": "draft", "new_status": "final",
  "errors": []
}

// --action decide
{
  "status": "ok", "action": "decide",
  "slug": "pr-0042-login-google",
  "previous_decision": "pending", "new_decision": "approved-with-comments",
  "errors": []
}
```

**Exit codes:** `0` ok/dry-run · `1` user error · `2` fatal.

## Guardrails

**Never:**
- Skip the duo. Every review goes through Code Reviewer + AppSec in parallel. If a section is N/A, say so in §Findings.
- Conflate the two lifecycle axes. `status: final` ≠ `decision: approved`.
- Decide `changes-requested` without naming ≥ 1 🔴 Blocker. Internal consistency required.
- Decide `approved` while open 🔴 Blockers exist. Downgrade with explanation, never silent approve.
- Record a Finding without location + problem + suggestion. Noise.
- Rename or delete a review. Slug is stable. If wrong, write `pr-…-followup` and link.
- Auto-approve. `approved` means the **human reviewer** signed off.
- Use this skill as substitute for the GitHub review. Vault complements; GitHub is what the platform enforces.

**Always:**
- Match the user's active conversation language.
- Announce the duo at the start.
- Run `--action list` before `scaffold`.
- Capture PR metadata (`--pr`, `--pr-url`, `--author`) at scaffold so frontmatter is actionable from save.
- Walk the pre-finalize checklist before flipping to `final`.
- Include praise (🔵) when the author got something right.
- Invoke `/sdlc-kit:sync` after any `scaffold`, `transition`, `decide`.
- Surface generated file path.

## Examples

**Recording a new review:**
```
User: /sdlc-kit:review new PR #42 — Login with Google (author: alice)
AI:   [list] 0 reviews on PR #42. Proposed slug: `pr-0042-login-google`. OK?
User: ok
AI:   [scaffold --pr 42 --pr-url … --author alice]
AI:   "Authoring as duo. §Scope — what does this PR do? What's out of scope?"
User: <answer>
AI:   [Edit §Scope]
AI:   "§1 Design — pattern fit OK. Anything to flag?"
…
AI:   "§4 AppSec: new /auth/google endpoint has rate limit and CSRF token,
       but id_token signature isn't verified against Google's JWKS. 🔴 Blocker."
AI:   [Edit §Findings — add 🔴 on auth/google.go:87]
…
AI:   "All six walked. 1 Blocker, 2 Majors, 1 Praise. Decide?"
User: request changes.
AI:   [decide --to changes-requested]
AI:   "Pre-finalize: all walked ✓ / location+suggestion ✓ / decision set ✓ / Blocker named ✓. Finalize?"
User: finalize.
AI:   [transition --to final][/sdlc-kit:sync]
```

**Approving after fixes:**
```
User: /sdlc-kit:review approve pr-0042-login-google
AI:   [list] final, decision=changes-requested.
AI:   "Confirm approving PR #42? Open 🔴 (JWKS verification) resolved + test for signature mismatch?"
User: yes, both verified.
AI:   [decide --to approved][/sdlc-kit:sync]
```

**Smell — approve with open Blockers:**
```
User: /sdlc-kit:review approve pr-0043-rate-limiting
AI:   [list] draft, pending. §Findings has 1 open 🔴 (no rate-limit on /admin/reset).
AI:   "Won't approve over an open Blocker. Either downgrade with explanation, or fix it. Which?"
```

## See also

- `scripts/review.py` — file-op helper.
- `assets/vault-tree/07-retrospectives/_templates/review.md.tpl`.
- `~/.claude/CLAUDE.md` Vellus Code Review section (this is the in-vault counterpart).
- `/sdlc-kit:retro`, `/sdlc-kit:incident`, `/sdlc-kit:status`, `/sdlc-kit:worktree`, `/sdlc-kit:sync`.
