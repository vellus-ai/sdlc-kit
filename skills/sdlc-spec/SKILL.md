---
name: sdlc-spec
description: |
  Use when the user wants to create or mature a Spec-Driven Development (SDD)
  trio — `requirements.md` (EARS notation, FR + NFR across 10 axes),
  `design.md` (architectural drivers, patterns, C4, flows, data model,
  contracts, threat-modelled security, SLI/SLO observability, resilience,
  rollout) and `tasks.md` (executable TDD + bite-sized task list with Kiro
  markers, Conventional Commits branch/commit, and one git worktree per
  task) — under `04-specs/<feature-slug>/`. English triggers:
  `/sdlc-kit:spec`, `/sdlc-kit:spec new <feature>`,
  `/sdlc-kit:spec requirements approve`,
  `/sdlc-kit:spec design approve`, "start a spec for X",
  "write requirements for Y", "approve the design",
  "the tasks for feature Z are ready", "archive the old login spec".
  pt-BR triggers: "começar uma spec para X",
  "escrever os requisitos para Y", "aprovar o design",
  "as tasks da feature Z estão prontas", "arquivar a spec antiga de login".
  The trio is the unit of work: scaffolding creates all three files from
  `04-specs/_templates/` at once, then the LLM drives the interview
  section-by-section under explicit expert triads — requirements is authored
  by a **Senior PM + Software Engineer + Solutions Architect** triad; design
  is authored by a **Senior Software Engineer + AppSec Engineer + Software
  Architect** triad; tasks is driven by a TDD-first operator obeying Kiro
  markers. Hard approval gates (requirements → design → tasks) ensure design
  cannot start before requirements are approved and tasks cannot start
  before design is approved. Status transitions are per-doc
  (`draft` → `approved` → `implemented` → `archived`). Always invokes
  `/sdlc-kit:sync` after any edit. Do not invoke for single technical
  decisions (`/sdlc-kit:adr`), cross-cutting requirements
  (`/sdlc-kit:trd`), or initiative-level product scope (`/sdlc-kit:prd`).
---

# sdlc-kit:spec

Materializes and matures the three-document Spec-Driven Development trio under `04-specs/<slug>/`.

---

## The trio

| Doc | Purpose | Template | Lifecycle |
|---|---|---|---|
| `requirements.md` | *What* the system must do — EARS notation, acceptance criteria, non-functional requirements, out-of-scope. | `_templates/requirements.md.tpl` | `draft` → `approved` → `implemented` → `archived` |
| `design.md` | *How* it will be built — architecture, flows, data model, external contracts, local decisions, security, observability. | `_templates/design.md.tpl` | same |
| `tasks.md` | Executable task list (TASK-NNN) grouped by phase, each traced back to a requirement. | `_templates/tasks.md.tpl` | same |

All three share one `slug:` frontmatter field — that's what binds them into a trio.

---

## When to invoke

Invoke when:

- The user types `/sdlc-kit:spec`, `/sdlc-kit:spec new <feature>`, `/sdlc-kit:spec <kind> approve`, `/sdlc-kit:spec list`, `/sdlc-kit:spec archive <slug>`.
- The user says "start a spec", "write requirements for X", "approve the design", "tasks are ready", "mark the spec as implemented" — or equivalent phrasing in any other language.
- A PRD was just approved (`/sdlc-kit:prd`) and the user wants to break the initiative into feature specs.

**Do not** invoke when:

- The user wants to record a single architecture decision → use `/sdlc-kit:adr`.
- The user wants cross-cutting technical requirements → use `/sdlc-kit:trd`.
- The user wants product vision / scope at the initiative level → use `/sdlc-kit:prd`.
- cwd is not inside a vault.

---

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; abort if missing.
2. **Python 3.10+** available.
3. **Templates exist** at `<vault>/04-specs/_templates/{requirements,design,tasks}.md.tpl`. If any are missing (legacy vault), suggest `/sdlc-kit:init` repair.

---

## Flow

### Zero-arg: `/sdlc-kit:spec`

1. Run `spec.py --action list`. Parse the JSON `features` array.
2. Show the user a one-line summary per feature: `login-google — R:approved D:draft T:missing`.
3. Suggest next action:
   - If a feature has `R:approved D:draft` → "Want to start the design interview for `<slug>`?"
   - If a feature has `R:approved D:approved T:draft` → "Want to expand the tasks for `<slug>`?"
   - If no feature is in progress → "Want to scaffold a new spec? Give me the feature name."

### `new`: `/sdlc-kit:spec new <feature>`

1. **Derive slug** from the feature name: lowercase, hyphen-separated, ASCII. Confirm with the user before proceeding (critical — slug is the folder name and wikilink key, hard to change later).
2. **Scaffold**:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-spec/scripts/spec.py" \
     --vault-root "<vault>" --action scaffold --slug <slug> --title "<Title>"
   ```
3. **Begin the requirements interview** (see below). Never jump to design until the user explicitly approves the requirements.

### Existing trio: `/sdlc-kit:spec <slug>` or contextual

1. **List status** first.
2. Branch on the lifecycle stage:
   - `R:draft` → continue the requirements interview.
   - `R:approved D:draft` → start design interview.
   - `R:approved D:approved T:draft` → expand tasks.
   - All three `approved` or `implemented` → offer: `[r] review`, `[a] archive`, `[s] show summary`.

---

## The three interviews (LLM-driven, section by section)

**Universal rules:**

- Always mirror the user's active conversation language — the templates ship in English but every LLM prompt and every edited section must match the user's active conversation language.
- Walk the template's sections in order. Edit **section-by-section via the Edit tool**, never rewrite the whole file at once.
- Do not fabricate. If the user has no answer for a section, leave the placeholder and offer to revisit later.
- After substantive edits, run `/sdlc-kit:sync`.

Each interview is led by an explicit **expert triad** — you role-play all three voices and keep them honest with each other. Announce the triad at the start of each interview so the user knows which lens you're applying.

---

### 1. Requirements interview  — *Senior PM + Software Engineer + Solutions Architect*

Gate: this interview must complete and the user must approve before design starts.

**Triad lenses (run every question through all three):**
- **Senior Product Manager** — Who is the user? What outcome are we chasing? What KPI moves? What's the MoSCoW priority? Is this the smallest thing that solves the problem?
- **Software Engineer** — Is this testable? Is the acceptance criterion unambiguous? What edge cases are we glossing over? What's realistic effort-wise?
- **Solutions Architect** — What NFRs does this feature inherit from the platform (latency, availability, security, LGPD, observability, cost)? What upstream/downstream systems are we committing to? What constraints does the target architecture impose?

The triad must sign off on every FR and NFR: the PM owns *why*, the engineer owns *how we'll verify it*, the architect owns *how it fits the system*.

Walk the template's sections in order, one focused question per section:

1. **Product context (§1)** — problem statement, personas (+ anti-persona), business KPIs with baseline/target/window, and strategic parent links (PRD / epic / OKR). *PM leads.*
2. **Scope (§2)** — in / out / assumptions / dependencies split (upstream / downstream / external). *PM + Architect.*
3. **Actors & triggers (§3)** — the actor-kind-trigger table. *Engineer + Architect.*
4. **User stories (§4)** — `As a <persona>, I want <capability>, so that <outcome>`; each story lists the REQs it covers. *PM leads.*
5. **Functional requirements (§6)** — elicit each REQ in **EARS** with **MoSCoW priority**, ≥ 1 **testable acceptance criterion** (`Given / When / Then`) and an explicit **rationale** linking back to a persona or KPI. *Engineer owns testability.*
6. **Non-functional requirements (§7)** — walk **all ten** NFR sub-sections and explicitly confirm or mark "N/A (reason)" for each:
   - 7.1 Performance — p95 latency, throughput.
   - 7.2 Scalability & capacity — horizontal scaling, data volume ceilings.
   - 7.3 Reliability & availability — SLO, error budget, RPO/RTO.
   - 7.4 Security — AuthN, AuthZ, input validation, secrets, transport.
   - 7.5 Privacy & compliance — **LGPD** data minimization, subject rights, masking, retention, audit trail.
   - 7.6 Observability — structured logs, RED/USE metrics, OTEL traces, SLO-burn alerts.
   - 7.7 Accessibility & usability — **WCAG 2.1 AA** on user-facing surfaces; usable error messages.
   - 7.8 Maintainability & quality — coverage, linter/type-checker gates, docs.
   - 7.9 Portability & i18n — locales, runtime.
   - 7.10 Cost — budget at the load profile.
   Each NFR is **testable** — metric, target, measurement method. Cross-cutting NFRs that belong to the platform go in the TRD (`[[TRD-<slug>]]`); link, do not duplicate. *Architect leads.*
7. **Edge cases & failure modes (§8)** — the triad's "failure brainstorm": every item maps to an acceptance criterion or is explicitly tolerated. *Engineer leads.*
8. **Explicitly out of scope (§9)** — sharpen what's in §2.2. *PM leads.*
9. **Traceability matrix (§10)** — REQ ↔ story ↔ task ↔ test. Orphan REQs (no task) or orphan TASKs (no REQ) are a blocker at tasks-approval time. *Engineer maintains.*
10. **Open questions (§11)** — each with owner and deadline. *All three.*

When the user approves:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-spec/scripts/spec.py" \
  --vault-root "<vault>" --action transition --slug <slug> --doc requirements --to approved
```

Then invoke `/sdlc-kit:sync` and proceed to the design interview.

---

### 2. Design interview  — *Senior Software Engineer + AppSec Engineer + Software Architect*

Gate: requirements must be `approved`. If they aren't, stop and say so.

**Triad lenses (run every section through all three):**
- **Senior Software Engineer** — What's the simplest thing that works? What's the module boundary? Which failure modes are plausible? How will we know this is broken at 3 a.m.?
- **AppSec Engineer** — What's the trust boundary here? Which STRIDE threat applies? What's the least-privilege version of this? Are we logging anything we shouldn't? Is input validated at the boundary?
- **Software Architect** — Which pattern solves this class of problem best? What are the alternatives and why are we not picking them? Does this stay inside the system's architectural style? How does it evolve without breaking consumers?

Design by **deliberate pattern choice**, not by default. Every structural decision names the problem, the chosen pattern, the rationale and the alternatives rejected. Copy-paste defaults ("just add a retry", "just cache it") are not design — they're a smell.

Walk the template's sections in order:

1. **Overview (§1)** — 2 paragraphs: what + why this shape. *Engineer leads.*
2. **Architectural drivers (§2)** — pull the NFRs from [[<feature>-requirements]] §7 into a table; each driver drives at least one design implication. *Architect leads.*
3. **Design principles & patterns (§3)** — state the principles adopted (DDD / hexagonal / clean / CQRS / event-driven / functional core …) **with rationale**; fill the *Patterns in use* table one row per real problem with pattern + rationale + alternatives rejected; list explicit non-goals. *Architect + Engineer.*
4. **System architecture (§4)** — Mermaid C4 container/component; layering and module boundaries; new + modified components. Update the diagram to **reflect reality**, not intent. *Architect leads.*
5. **Main flows (§5)** — sequence diagrams for the **happy path** and at least one **failure / compensation path**. *Engineer leads.*
6. **Data model (§6)** — conceptual model (aggregates + invariants), physical schema, **indexing strategy** (one row per index with the query it serves), **consistency model** (strong / eventual boundaries, transactions, concurrency control), **migrations & evolution** (expand/contract plan; backfill volume + duration + risk), **data classification** table (public / internal / personal / sensitive → at-rest / in-transit / in-logs treatment). *Engineer + AppSec (classification).*
7. **Contracts (§7)** — synchronous APIs (table + OpenAPI/proto source + **RFC 7807** error model + backwards-compat policy); asynchronous events (direction, schema source, delivery semantics, partition key, DLQ); external integrations (SLA, auth, rate limits, circuit-breaker params). *Architect leads; Engineer owns schemas.*
8. **Security design (§8)** — **threat-model before implementation** and treat this as a merge gate. Walk trust boundaries, then the **STRIDE-per-component** table, then AuthN/AuthZ, input validation & output encoding, secrets & key management, privacy (LGPD/GDPR), dependency & supply chain (SBOM, vuln SLA, signed images), logging/telemetry hardening (PII/secret scrubber, tamper-evident audit log). *AppSec leads.*
9. **Observability (§9)** — **SLIs & SLOs** table with error budgets; structured log format and levels; **RED + USE** metrics (names explicit); OTEL traces with baggage; dashboards + alerts (SLO burn fast/slow, DLQ > 0) + runbook link. *Engineer leads; Architect signs off on SLOs.*
10. **Performance & capacity plan (§10)** — load profile, per-layer performance budget, hot-path / N+1 audit, load-test plan mapped to NFR-PERF-*. *Architect + Engineer.*
11. **Resilience & failure modes (§11)** — failure / detection / response / recovery table; patterns used (circuit breaker, bulkhead, timeout + retry with jitter, graceful degradation, idempotent consumers, outbox, saga compensations). *Engineer leads.*
12. **Deployment & rollout (§12)** — environments, feature flag + ramp plan + kill-switch, migration ordering (expand → code → backfill → cutover → contract), rollback strategy with data-loss boundary. *Architect + Engineer.*
13. **Testing strategy (§13)** — unit / contract / integration / E2E / security / performance / chaos — sets the contract for `tasks.md` Phase 3+. *Engineer leads.*
14. **Local decisions (§14)** — feature-scoped only; structural or cross-feature decisions → `/sdlc-kit:adr`. *All three.*
15. **Technical risks (§15)** — risk / likelihood / impact / mitigation / owner. *All three.*
16. **Open questions (§16)** — each with owner and deadline. *All three.*

When the user approves:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-spec/scripts/spec.py" \
  --vault-root "<vault>" --action transition --slug <slug> --doc design --to approved
```

Then invoke `/sdlc-kit:sync` and proceed to the tasks interview.

---

### 3. Tasks expansion  — *TDD-driven, bite-sized, Conventional Commits, git-worktree per task, Kiro markers*

Gate: design must be `approved`. If it isn't, stop and say so.

This is **not** a task-estimation template — it is an **executable playbook**. The scaffolded `tasks.md` already carries the full playbook (Kiro markers table, 4 invariants, Conventional Commits allowed-types table, git-worktree workflow skeleton and the copy-this-block task template). Do not rewrite that playbook — populate it.

**Invariants for every task you expand (enforced by the template):**

1. **TDD mandatory.** Every task is a red → green → refactor cycle: write the failing test → run it → implement the minimum → run it → refactor → commit. Each step is **2–5 minutes** of focused work.
2. **Bite-sized.** A task fits in ≤ 2h; if a step balloons, split it.
3. **One worktree per task.** Work happens on an isolated `git worktree` branch (prefer `.worktrees/<task-slug>`, per `superpowers:using-git-worktrees`). Main stays clean.
4. **Conventional Commits for branch *and* commit.** Branch: `<type>(<slug>)/<task-slug>`. Commit: `<type>(<slug>): <subject>`. Allowed types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `build`, `ci`.
5. **Kiro markers — only one `[-]` at a time per `tasks.md`.** Never edit markers by hand — drive them via `/sdlc-kit:task {start|complete|block|reopen}`. Never edit task text, IDs, or `Requirements satisfied` refs — only the marker and the blocker note.

| Marker | Logical status | Meaning |
|---|---|---|
| `- [ ]` | `queued` | Planned, not started. |
| `- [-]` | `in_progress` | Actively being worked on. **Only one per file.** |
| `- [x]` | `completed` | Delivered, merged, worktree cleaned. |
| `- [~]` | `needs_attention` | Blocked; reason noted on the line below. |

**How to populate `tasks.md` from an approved design:**

1. **Preserve the playbook.** Leave the "How to read this file", "Invariants", "Conventional Commits" and "Git worktree workflow" sections untouched — they are the contract the downstream engineer reads.
2. **Remove the example TASKs** that shipped with the template (TASK-001 scaffold, TASK-010 service happy path, etc.) and replace them with real ones drawn from the design:

   | Phase in `tasks.md` | What to pull from `design.md` |
   |---|---|
   | **Phase 1 — Setup** | migrations (§6.5), scaffolding (§4.1 new components), feature-flag wiring (§12). |
   | **Phase 2 — Domain logic (TDD)** | one TASK per aggregate / use case in §6.1; one TASK per validation rule (§8.4). |
   | **Phase 3 — Transport** | one TASK per endpoint happy-path (§7.1); one TASK per error-mapping suite (RFC 7807); one TASK per emitted/consumed event (§7.2). |
   | **Phase 4 — Observability** | one TASK per SLI/metric/log/trace from §9; one TASK per alert. |
   | **Phase 5 — Deploy** | migration in staging → canary → promote, following §12's ramp plan. |

3. **For each TASK use the copy-me block the template provides:**
   ```
   - [ ] **TASK-NNN** — <short imperative title>
     - **Branch:** `<cc-type>({{SLUG}})/<task-slug>`
     - **Worktree:** `.worktrees/<task-slug>`
     - **Requirements satisfied:** [[<slug>-requirements#REQ-NNN]]
     - **Steps:**
       1. Write failing test `<path/to/test>` asserting `<behavior>`.
       2. Run `<test-command>` — expect failure with `<expected-error>`.
       3. Implement minimal change in `<path/to/file>` to satisfy the test.
       4. Run `<test-command>` — expect pass.
       5. Refactor (optional).
       6. Commit: `<cc-type>({{SLUG}}): <commit-subject>`.
       7. Push branch + open PR.
       8. After merge: `git worktree remove` and delete branch.
   ```
   Every TASK must: (a) name real paths / commands / errors; (b) link to at least one `[[<slug>-requirements#REQ-NNN]]`; (c) pick a branch `type` that matches the work (`feat` for new capability, `test` for test-only tasks, `refactor` for no-behavior-change, `chore` for tooling/deploy).

4. **Update the Summary section** (total tasks, critical path, parallelizable tracks). Keep it honest — this is what the user sees first.

5. **Traceability check before approving:** every REQ in §6 of the requirements file maps to ≥ 1 TASK; every TASK maps to ≥ 1 REQ. Run the matrix in `requirements.md §10` and reject orphans on either side.

When the user approves the task list:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-spec/scripts/spec.py" \
  --vault-root "<vault>" --action transition --slug <slug> --doc tasks --to approved
```

From this point on, **task lifecycle is operated by `/sdlc-kit:task`** — this skill scaffolds the list, `/sdlc-kit:task` flips the markers.

---

## Status transitions reference

| Intent | Verb | Target status |
|---|---|---|
| User approves a doc | "approve" / "looks good" / "ship it" | `approved` |
| Implementation done for that doc | "implemented" / "done building" | `implemented` |
| Spec is obsolete but kept for history | "archive" / "shelve" | `archived` |
| Re-opening for edits | "reopen" / "back to draft" | `draft` |

Bulk archive (all three docs at once):

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-spec/scripts/spec.py" \
  --vault-root "<vault>" --action transition --slug <slug> --doc all --to archived
```

---

## Output contract

```json
// --action list
{
  "status": "ok",
  "action": "list",
  "vault_root": "/abs/path/.sdlc",
  "features": [
    {
      "slug": "login-google",
      "path": "04-specs/login-google",
      "docs": [
        {"kind": "requirements", "path": "04-specs/login-google/requirements.md",
         "exists": true, "title": "Requirements — Login with Google",
         "status": "approved", "updated": "2026-04-14"},
        {"kind": "design",       "path": "04-specs/login-google/design.md",
         "exists": true, "title": "Design — Login with Google",
         "status": "draft",    "updated": "2026-04-16"},
        {"kind": "tasks",        "path": "04-specs/login-google/tasks.md",
         "exists": false, "title": "", "status": "", "updated": ""}
      ]
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
  "slug": "login-google",
  "spec_dir": "04-specs/login-google",
  "docs": [
    {"kind": "requirements", "path": "04-specs/login-google/requirements.md", "was_new": true,  "skipped": false},
    {"kind": "design",       "path": "04-specs/login-google/design.md",       "was_new": true,  "skipped": false},
    {"kind": "tasks",        "path": "04-specs/login-google/tasks.md",        "was_new": true,  "skipped": false}
  ],
  "errors": []
}

// --action transition --doc requirements --to approved
{
  "status": "ok",
  "action": "transition",
  "vault_root": "/abs/path/.sdlc",
  "slug": "login-google",
  "spec_dir": "04-specs/login-google",
  "docs": [
    {"kind": "requirements", "path": "04-specs/login-google/requirements.md",
     "previous_status": "draft", "new_status": "approved", "changed": true}
  ],
  "errors": []
}
```

**Exit codes:** `0` ok/dry-run · `1` user error (missing arg, invalid slug/status, spec not found) · `2` fatal (permission denied, IO, template missing).

---

## Guardrails

**Never:**
- Start the design interview before `requirements.md` has `status: approved`.
- Start the tasks interview before `design.md` has `status: approved`.
- Rewrite a doc in one Edit call — always section-by-section.
- Auto-promote to `approved` — always require explicit user approval.
- Overwrite an existing scaffold without `--force` and explicit user confirmation.
- Fabricate content. If the user doesn't have an answer, leave the placeholder and offer to revisit later.
- Skip the expert triad. Every section must be read through all three lenses (PM/Eng/SolArch for requirements; SE/AppSec/SwArch for design). If a lens has nothing to add, state that explicitly — don't silently ignore it.
- Leave NFR sub-sections unvisited. For each of 7.1–7.10 either fill it or mark `N/A (<reason>)`. A blank section is never acceptable.
- Skip the §8 threat model in `design.md`. AppSec is a merge gate — if STRIDE-per-component is empty, the design is not approvable.
- Approve `tasks.md` with orphan REQs (no TASK) or orphan TASKs (no REQ). The §10 traceability matrix is the source of truth.
- Approve `tasks.md` if any TASK step is not 2–5 minutes, or any TASK lacks its Branch / Worktree / Requirements satisfied / Steps block, or any branch name violates Conventional Commits.
- Edit Kiro markers by hand inside `tasks.md`. Marker transitions are the exclusive job of `/sdlc-kit:task {start|complete|block|reopen}`.
- Touch `CLAUDE.md` or `_MOC.md` — those are managed by `/sdlc-kit:sync` and the user.

**Always:**
- Mirror the user's active conversation language — announce the expert triad in that language at the top of each interview.
- Run `--action list` before scaffold/transition so you know the current state.
- Confirm the slug with the user before scaffolding (it's the folder name and wikilink key).
- Invoke `/sdlc-kit:sync` after any scaffold, edit, or transition.
- Include wikilinks between sibling docs (`[[<slug>-requirements]]`, `[[<slug>-design]]`, `[[<slug>-tasks]]`) — the templates ship with placeholders; keep them accurate.
- Keep the §10 requirements traceability matrix updated as REQs and TASKs are added; run it before approving `tasks.md`.
- Cross-cutting NFRs belong in a TRD (`/sdlc-kit:trd`); link, do not duplicate.
- Preserve the invariants section, Kiro markers table, Conventional Commits table and git-worktree workflow that ship with `tasks.md.tpl` — they are the contract the downstream engineer reads.

---

## Examples

> Examples below are in English. In a real session, mirror the user's active conversation language in every user-facing line.

**Fresh trio — user starts from scratch:**
```
User: /sdlc-kit:spec new "Login with Google"
AI:   "Proposed slug: `login-with-google`. Keep it or rename?"
User: "login-google"
AI:   [scaffold --slug login-google --title "Login with Google"]
AI:   [scaffold] created 04-specs/login-google/{requirements,design,tasks}.md.
AI:   "Let's fill out requirements section by section. First: **Scope** — in
       2–3 sentences, what does this feature do, and what's explicitly out?"
User: <answer>
AI:   [Edit tool: replace Scope section]
AI:   "Next: **Actors and triggers** — who kicks this off?"
…
AI:   "All sections filled. Approve requirements and move to design? (y/n)"
User: y
AI:   [transition --slug login-google --doc requirements --to approved]
AI:   [/sdlc-kit:sync]
AI:   "✓ requirements approved. Starting design. First: **Overview** — 2 paragraphs
       on the technical approach."
…
```

**Mid-flight resume:**
```
User: continua a spec do login-google
AI:   [spec.py --action list]
AI:   "login-google — R:approved D:draft T:missing. Resuming the design interview.
       We left off at **Data model**. Want me to show the current Mermaid and
       iterate from there?"
```

**Gate violation — user tries to skip to tasks:**
```
User: pode ir direto para as tasks do login-google
AI:   "Design is still `draft` — tasks are gated on an approved design. Want to
       finish the design interview first, or approve design as-is (I can show you
       the current state)?"
```

**Archive an obsolete trio:**
```
User: archive the old login-password spec
AI:   [transition --slug login-password --doc all --to archived]
AI:   [/sdlc-kit:sync]
AI:   "✓ All three docs of `login-password` marked archived."
```

---

## See also

- `scripts/spec.py` — file-op helper.
- `assets/vault-tree/04-specs/_templates/` — canonical templates (copied into each vault at init time).
- `/sdlc-kit:prd` — initiative-level product scope; a PRD typically fans out into multiple specs.
- `/sdlc-kit:adr` — structural decisions referenced from the spec's "Local decisions" section.
- `/sdlc-kit:trd` — cross-cutting technical requirements referenced from NFR sections.
- `/sdlc-kit:task` — per-task lifecycle; `/sdlc-kit:spec` scaffolds the list, `/sdlc-kit:task` operates on individual tasks.
- `/sdlc-kit:sync` — always invoked after spec edits.
