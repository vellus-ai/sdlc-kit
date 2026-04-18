---
name: sdlc-review
description: |
  Use when the user wants to record, finalize, or transition a code-review
  record for a Pull Request — one file per review under
  `07-retrospectives/reviews/<slug>.md` (slug usually
  `pr-NNNN-<short-topic>`). English triggers: `/sdlc-kit:review`,
  `/sdlc-kit:review new <pr-or-title>`, `/sdlc-kit:review list`,
  `/sdlc-kit:review approve <slug>`,
  `/sdlc-kit:review approve-with-comments <slug>`,
  `/sdlc-kit:review request-changes <slug>`,
  `/sdlc-kit:review finalize <slug>`, "review PR #42",
  "code review the login PR", "approve that review",
  "request changes on the rate-limiting PR". pt-BR triggers:
  "revisar o PR #42", "fazer code review do PR de login",
  "aprovar aquele review", "solicitar mudanças no PR de rate limiting".
  Co-authored by a duo of expert personas running in parallel through the
  full checklist: a **Senior Engineer (Code Reviewer)** (design &
  architecture, code quality, tests, process) and an **AppSec Engineer**
  (security, privacy/LGPD, supply chain). The script tracks two independent
  lifecycle axes: `status` (draft → final — is the write-up delivered?) and
  `decision` (pending → approved | approved-with-comments | changes-requested
  — the reviewer's verdict). Findings are tagged by severity (🔴 Blocker /
  🟡 Major / 🟢 Minor / 🔵 Praise), each with `path/file.ext:NNN`, problem,
  and concrete suggestion — a finding without location or suggestion is not
  actionable. The script does deterministic file ops only — listing,
  scaffolding from `07-retrospectives/_templates/review.md.tpl`, and the two
  transitions; the LLM drives the section-by-section checklist pass via
  Edit, mirroring the user's chat language. After scaffold, transition, or
  decide, invokes `/sdlc-kit:sync` so MOCs and `_INDEX.md` reflect the
  change. Do not invoke for sprint or release retrospectives
  (`/sdlc-kit:retro`), incident post-mortems (`/sdlc-kit:incident`), or
  vault-completeness audits (`/sdlc-kit:status`).
---

# sdlc-kit:review

Records and matures Pull Request code reviews under `07-retrospectives/reviews/`.

A review is the **persistent artefact** of a PR review — checklist passed, findings logged with severity, decision delivered. It outlives the PR thread on GitHub: when the PR is squashed or the conversation rots, the review record is the source of truth for "what was caught, what was waived, and why".

---

## What a review is (and isn't)

| Review is… | Review isn't… |
|---|---|
| The persistent record of a PR review with checklist + findings + decision | A scratchpad of in-flight comments — reach a conclusion, then write the review |
| Co-authored by **Senior Engineer (Code Reviewer) + AppSec Engineer** running both lenses in parallel | A single-perspective rubber-stamp |
| Severity-tagged findings (🔴 Blocker / 🟡 Major / 🟢 Minor / 🔵 Praise), each with location + suggestion | A bag of observations without severity or actionable fix |
| A two-axis lifecycle: `status` (draft → final) **and** `decision` (pending → approved \| approved-with-comments \| changes-requested) | Conflated into one status — the write-up being final ≠ the PR being approved |
| Linked from the feature design, the PR branch, and any ADR/TRD it implements or deviates from | Standalone — every review references the artefacts it judged |
| The mandatory artefact for the `/code-review` Vellus skill in `~/.claude/CLAUDE.md` | A replacement for the reviewer's GitHub review — it complements the GitHub thread, it doesn't replace it |

Lifecycles:

- **Status** — `draft` (being written by the reviewer) → `final` (delivered to the author).
- **Decision** — `pending` (no verdict yet) → `approved` | `approved-with-comments` | `changes-requested`.

A `final + changes-requested` review is normal: the reviewer delivered the verdict, the author has work to do. A `final + approved` review unlocks merge. A `draft + approved` review is a reviewer's working hypothesis — not yet delivered.

---

## When to invoke

Invoke when:

- The user types `/sdlc-kit:review`, `/sdlc-kit:review new <pr-or-title>`, `/sdlc-kit:review list`, `/sdlc-kit:review finalize <slug>`, `/sdlc-kit:review approve <slug>`, `/sdlc-kit:review approve-with-comments <slug>`, `/sdlc-kit:review request-changes <slug>`.
- The user says "review PR #42", "code review the login PR", "approve that review", "request changes on the rate-limiting PR", or equivalent phrasing in any other language.
- A PR is open and a review is needed before merge — and a record needs to live in the vault, not only on GitHub.
- A reviewer has finished walking the checklist on a PR and wants to deliver the verdict + capture the artefact in one step.

**Do not** invoke when:

- The user wants a sprint or release retrospective → `/sdlc-kit:retro`.
- The user wants an incident post-mortem → `/sdlc-kit:incident`.
- The user wants a vault-completeness audit (frontmatter coverage, orphan files, stale ADRs) → `/sdlc-kit:status`.
- The PR thread is still in active discussion and no verdict is near — write the review when there is something to say.
- cwd is not inside a vault.

---

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; abort if missing.
2. **Python 3.10+** available.
3. **Template exists** at `<vault>/07-retrospectives/_templates/review.md.tpl`. If missing (legacy vault), suggest `/sdlc-kit:init` repair.

---

## The expert duo

Every review is co-authored, on every PR, by two personas working in parallel — never one without the other. Announce the duo at the start of the interview so the user knows which lenses are active:

> "I'll author this review as a duo: **Senior Engineer (Code Reviewer)** for design / quality / tests, and **AppSec Engineer** for security / privacy / secrets. Both lenses pass through every section before we record the decision."

| Section | Code Reviewer lens | AppSec lens |
|---|---|---|
| §1 Design & architecture | Pattern fit, separation of concerns, abstraction quality | Trust boundaries respected, no security-through-obscurity, threat model matches reality |
| §2 Code quality | Naming, readability, DRY/YAGNI, error handling | Error paths don't leak internals; failure modes are safe defaults |
| §3 Tests | Coverage on changed files, behavior over implementation, PBT where useful | Negative-path tests (auth fail, validation fail, expired token); fuzz where input parsing is critical |
| §4 AppSec | — | Full pass: injection, AuthN/AuthZ, secrets, supply chain, SSRF/CORS, rate limiting, error model, crypto |
| §5 Privacy & LGPD | — | Minimization, masking, subject rights, retention, consent, audit trail |
| §6 Process & delivery | Conventional Commits, CI status, docs/ADR/TRD updates, rollback plan | Observability covers security signals (auth failures, anomaly metrics) |

§4 and §5 are **AppSec-only** — but the Code Reviewer must still confirm AppSec walked them, never silently skip. If a section is genuinely "not applicable" (e.g. a docs-only PR), say so explicitly in §Findings rather than leaving boxes unchecked.

This skill aligns with the user's `~/.claude/CLAUDE.md` Code Review section — the expanded checklist (Design, Code Quality, Testing, AppSec, LGPD, Process) is identical, just persisted in the vault.

---

## Flow

### List: `/sdlc-kit:review` or `/sdlc-kit:review list`

1. Run `review.py --action list`. Parse the JSON `reviews` array.
2. Show a compact table: `slug | status | decision | reviewer | pr | title | updated`.
3. If empty, offer: "No reviews yet. Want to record one with `/sdlc-kit:review new <pr>`?"
4. Otherwise, offer next actions: open a draft, finalize, decide, or create a new one.

### New review: `/sdlc-kit:review new <pr-or-title>`

1. **Derive the slug.** Default convention: `pr-<NNNN>-<short-topic>` (zero-pad PR number to 4). For non-PR reviews (e.g. spike reviews), use a topic-based slug. Confirm with the user; they can override with `--slug`.
2. **Capture metadata up front** (PR number, PR url, author) so they go in the frontmatter at scaffold time:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-review/scripts/review.py" \
     --vault-root "<vault>" --action scaffold \
     --slug "pr-0042-login-google" \
     --title "PR #42 — Login with Google" \
     --pr "42" --pr-url "https://github.com/org/repo/pull/42" \
     --author "alice"
   ```
   Refuses to overwrite an existing slug unless `--force` is passed; never pass `--force` without the user's explicit instruction.
3. **Announce the duo** and walk the interview (see below).

### The interview (LLM-driven, duo, section by section)

Walk the template top-to-bottom. One focused question per section, editing in place via the Edit tool — never rewrite the whole file in one go. For each section, both lenses contribute before moving on.

**Phase A — Scope & metadata**
1. **Metadata.** Confirm/fill PR number, URL, author, branch, files changed, lines ±, CI status at review time.
2. **Scope.** What does the PR do, in 1–2 paragraphs? What is intentionally **out of scope** for this PR? Link the related feature design, tasks, ADRs and TRDs.

**Phase B — Six-section checklist**

For each of §1 through §6, walk the boxes and tick what's clean. **Anything left unchecked must produce a Finding** (any severity) explaining why — silent unchecked boxes are forbidden.

| # | Section | Owner lens | Minimum quality bar |
|---|---|---|---|
| 1 | Design & architecture | Code Reviewer | Pattern fit, no upward dependencies, no leaked abstractions |
| 2 | Code quality | Code Reviewer | Clear naming, no duplication, errors handled at the right boundary |
| 3 | Tests | Code Reviewer | Coverage on changed files, edge cases, behavior-not-implementation |
| 4 | AppSec | AppSec | Injection / AuthN / AuthZ / secrets / supply chain / SSRF / rate limit / error model / crypto |
| 5 | Privacy & LGPD | AppSec | Minimization / masking / subject rights / retention / consent / audit trail |
| 6 | Process & delivery | Both | Conventional Commits, CI green, docs updated, rollback plan, observability updated |

**Phase C — Findings**

Group findings by severity. Every finding carries:

- **File:** `path/file.ext:NNN` (or a clearly named unit of change — never just "somewhere in the diff").
- **Problem:** what is wrong **and why it matters** (security risk / correctness / maintainability / user impact).
- **Suggestion:** a concrete fix the author can apply — diff sketch, alternative API, missing test scenario.

Severity rules:

- **🔴 Blocker** — must fix before merge. Examples: secret committed; AuthZ missing on a new endpoint; data race on a shared mutable; LGPD masking absent on a new PII field; SQL string concatenation; a feature without any test.
- **🟡 Major** — should fix; merge can proceed only with explicit author+reviewer agreement (write a follow-up). Examples: subtle abstraction leak; missing observability on a critical path; missing rollback plan; coverage drops on changed files.
- **🟢 Minor / Nit** — polish, optional.
- **🔵 Praise** — what the author got right. Always include at least one when there is something to praise — reinforcement is part of the review craft.

**Phase D — Decision**

Set `decision:` via `decide` (see below). Any `changes-requested` decision **must** name at least one 🔴 Blocker — otherwise the decision is inconsistent with the findings.

### Finalize: `/sdlc-kit:review finalize <slug>`

Flips `status: draft → final`. This is the act of *delivering* the review — after this point, the write-up is the record the author and team will read.

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-review/scripts/review.py" \
  --vault-root "<vault>" --action transition \
  --slug "<slug>" --to "final"
```

**Pre-finalize checklist:**

- [ ] All six checklist sections walked; every unchecked box has a corresponding Finding.
- [ ] Every Finding has location + problem + suggestion.
- [ ] Decision is set (not `pending`) — finalize without a decision is a bug.
- [ ] If decision is `changes-requested`, at least one 🔴 Blocker exists.
- [ ] Both Code Reviewer and AppSec lenses acknowledged (not silently skipped on §1–§3 or §4–§5).

Idempotent: if already `final`, the script writes nothing.

### Decide: `/sdlc-kit:review {approve|approve-with-comments|request-changes} <slug>`

Map verb → target decision:

| Verb | Target decision | When to use |
|---|---|---|
| `approve` | `approved` | No changes required. Safe to merge. No 🔴 Blockers, no 🟡 Majors that the reviewer wants to enforce. |
| `approve-with-comments` | `approved-with-comments` | Merge allowed; suggestions are optional. Common with 🟢 Minors and praise. |
| `request-changes` | `changes-requested` | Mandatory fixes required. **Must** name at least one 🔴 Blocker. |
| (raw) | `pending` | Resets to pending — rare; use when reopening a review for re-evaluation. |

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-review/scripts/review.py" \
  --vault-root "<vault>" --action decide \
  --slug "<slug>" --to "<approved|approved-with-comments|changes-requested|pending>"
```

Idempotent: same decision = no write.

**Decision is independent from finalize** — they're two axes:

- `decide` first, then `finalize` → the most common flow (decide what you think, then deliver).
- `finalize` first, then `decide` later → only if the reviewer wants to publish the write-up while still thinking about the verdict (rare; smell).

### Sync

After every `scaffold`, `transition`, or `decide`, invoke `/sdlc-kit:sync` so `_INDEX.md` and `07-retrospectives/_MOC.md` reflect the change.

---

## Output contract

```json
// --action list
{
  "status": "ok",
  "action": "list",
  "vault_root": "/abs/path/.sdlc",
  "reviews": [
    {
      "slug": "pr-0042-login-google",
      "path": "07-retrospectives/reviews/pr-0042-login-google.md",
      "title": "PR #42 — Login with Google",
      "status": "final",
      "decision": "approved-with-comments",
      "reviewer": "Milton",
      "author": "alice",
      "pr": "42",
      "updated": "2026-04-17"
    }
  ],
  "count": 1,
  "errors": []
}

// --action scaffold
{
  "status": "ok",
  "action": "scaffold",
  "vault_root": "/abs/path/.sdlc",
  "slug": "pr-0042-login-google",
  "review_path": "07-retrospectives/reviews/pr-0042-login-google.md",
  "was_new": true,
  "errors": []
}

// --action transition
{
  "status": "ok",
  "action": "transition",
  "vault_root": "/abs/path/.sdlc",
  "slug": "pr-0042-login-google",
  "review_path": "07-retrospectives/reviews/pr-0042-login-google.md",
  "previous_status": "draft",
  "new_status": "final",
  "errors": []
}

// --action decide
{
  "status": "ok",
  "action": "decide",
  "vault_root": "/abs/path/.sdlc",
  "slug": "pr-0042-login-google",
  "review_path": "07-retrospectives/reviews/pr-0042-login-google.md",
  "previous_decision": "pending",
  "new_decision": "approved-with-comments",
  "errors": []
}
```

**Exit codes:** `0` ok/dry-run · `1` user error (invalid slug/status/decision, review not found, collision without `--force`) · `2` fatal (permission denied, IO, missing template).

---

## Guardrails

**Never:**
- Skip the duo. Every review goes through Code Reviewer + AppSec in parallel — never one without the other. If a section is N/A, say so explicitly in §Findings; do not silently leave it unchecked.
- Conflate the two lifecycle axes. `status: final` ≠ `decision: approved`. `finalize` delivers the write-up; `decide` records the verdict. Communicate both clearly.
- Decide `changes-requested` without naming at least one 🔴 Blocker. The decision and the findings must be internally consistent.
- Decide `approved` while open 🔴 Blockers exist in §Findings. If a Blocker is no longer a blocker, downgrade it to 🟡 Major and explain why; never silently approve over it.
- Record a Finding without location + problem + suggestion. A finding the author can't act on is noise.
- Rename or delete a review record. The slug is a stable reference — if a review was wrong, write a new one (`pr-0042-login-google-followup`) and link them.
- Auto-approve. `approved` means the **human reviewer** signed off — always require explicit user approval before invoking `--action decide --to approved`.
- Use this skill as a substitute for the reviewer's GitHub review. The vault record complements the GitHub thread; the GitHub review is what the platform enforces.

**Always:**
- Match the user's active conversation language.
- Announce the duo at the start of the interview.
- Run `--action list` before `scaffold` so you can warn about a slug collision early.
- Capture PR metadata (number, URL, author) at `scaffold` time via `--pr / --pr-url / --author` so the frontmatter is actionable from the first save.
- Walk the pre-finalize checklist with the user before flipping to `final`.
- After every Findings pass, ensure praise (🔵) is present when the author got something right — reinforcement matters as much as critique.
- Invoke `/sdlc-kit:sync` after any `scaffold`, `transition` or `decide`.
- Surface the generated file path in the final report so the user can open it.

---

## Examples

> Examples below are in English. In a real session, mirror the user's active conversation language in every user-facing line.

**Recording a new review:**
```
User: /sdlc-kit:review new PR #42 — Login with Google (author: alice)
AI:   [list] 0 reviews on PR #42. Proposed slug: `pr-0042-login-google`. OK?
User: ok
AI:   [scaffold --slug pr-0042-login-google --pr 42 --pr-url https://… --author alice
        --title "PR #42 — Login with Google"]
AI:   created 07-retrospectives/reviews/pr-0042-login-google.md (status=draft, decision=pending).
AI:   "I'll author this as a duo — Senior Engineer + AppSec. Let's start with §Scope.
       What does this PR do, and what is intentionally out of scope?"
User: <answer>
AI:   [Edit §Scope]
AI:   "§1 Design & architecture — pattern fit OK, separation OK. Anything you want to flag?"
…
AI:   "§4 AppSec lens: I see the new /auth/google endpoint has rate limiting and CSRF token,
       but the id_token signature isn't verified against Google's JWKS. That's a 🔴 Blocker."
AI:   [Edit §Findings — add 🔴 Blocker on auth/google.go:87]
…
AI:   "All six sections walked. 1 Blocker, 2 Majors, 1 Praise. Ready to decide?"
User: yes, request changes.
AI:   [decide --slug pr-0042-login-google --to changes-requested]
AI:   "Walking pre-finalize checklist: all sections walked ✓ / findings have location+suggestion ✓
       / decision is set ✓ / Blocker named on the changes-requested ✓. Finalize?"
User: finalize.
AI:   [transition --slug pr-0042-login-google --to final] [/sdlc-kit:sync]
AI:   "✓ Review delivered. status=final, decision=changes-requested. PR thread can now point at
       07-retrospectives/reviews/pr-0042-login-google.md."
```

**Listing reviews:**
```
User: /sdlc-kit:review list
AI:   | slug                       | status | decision               | reviewer | pr  | updated    |
      |----------------------------|--------|------------------------|----------|-----|------------|
      | pr-0040-pricing-page       | final  | approved               | Milton   | 40  | 2026-04-15 |
      | pr-0042-login-google       | final  | changes-requested      | Milton   | 42  | 2026-04-17 |
      | pr-0043-rate-limiting      | draft  | pending                | Ana      | 43  | 2026-04-17 |
AI:   "3 reviews. Want to walk the rate-limiting draft toward delivery?"
```

**Approving after fixes:**
```
User: /sdlc-kit:review approve pr-0042-login-google
AI:   [list] pr-0042-login-google — final, decision=changes-requested.
AI:   "Confirm approving PR #42? Open 🔴 Blockers — JWKS verification — has been resolved in
       latest commit, and the new test covers signature mismatch?"
User: yes, both verified.
AI:   [decide --slug pr-0042-login-google --to approved] [/sdlc-kit:sync]
AI:   "✓ decision=approved. Safe to merge."
```

**Idempotent decide:**
```
User: /sdlc-kit:review approve pr-0040-pricing-page
AI:   [list] pr-0040-pricing-page already approved — nothing to do. Skipping sync.
```

**Smell — approve with open Blockers:**
```
User: /sdlc-kit:review approve pr-0043-rate-limiting
AI:   [list] pr-0043-rate-limiting — draft, decision=pending. §Findings shows 1 open 🔴 Blocker
       (no rate-limit on /admin/reset).
AI:   "Won't approve over an open Blocker. Either: (1) the Blocker is no longer a Blocker —
       downgrade it and explain why, or (2) the author needs to fix it. Which is it?"
```

---

## See also

- `scripts/review.py` — file-op helper.
- `assets/vault-tree/07-retrospectives/_templates/review.md.tpl` — canonical review template (six-section checklist + severity-tagged findings + decision).
- `~/.claude/CLAUDE.md` — Vellus Code Review section (this skill is the in-vault counterpart of the `/code-review` Claude command).
- `/sdlc-kit:retro` — sprint or release retrospective (different artefact, different cadence).
- `/sdlc-kit:incident` — incident post-mortem (different lifecycle).
- `/sdlc-kit:status` — vault-completeness audit (frontmatter coverage, orphans, stale ADRs).
- `/sdlc-kit:worktree` — links the review record to the PR branch lifecycle.
- `/sdlc-kit:sync` — always invoked after review edits.
