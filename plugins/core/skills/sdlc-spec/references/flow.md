# sdlc-kit:spec — full flow

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; abort if missing.
2. **Python 3.10+** available.
3. **Templates exist** at `<vault>/04-specs/_templates/{requirements,design,tasks}.md.tpl`.

## Flow

### Zero-arg: `/sdlc-kit:spec`

1. Run `spec.py --action list`.
2. Show one-line summary: `login-google — R:approved D:draft T:missing`.
3. Suggest next action.

### `new`: `/sdlc-kit:spec new <feature>`

1. **Derive slug** — lowercase, hyphen-separated, ASCII. Confirm (slug = folder name + wikilink key, hard to change).
2. **Scaffold**:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-spec/scripts/spec.py" \
     --vault-root "<vault>" --action scaffold --slug <slug> --title "<Title>"
   ```
3. **Begin requirements interview**. Never jump to design until user explicitly approves requirements.

### Existing trio: `/sdlc-kit:spec <slug>` or contextual

1. **List status** first.
2. Branch on lifecycle stage:
   - `R:draft` → continue requirements.
   - `R:approved D:draft` → start design.
   - `R:approved D:approved T:draft` → expand tasks.
   - All approved/implemented → offer: `[r] review`, `[a] archive`, `[s] show summary`.

## The three interviews

**Universal rules:**
- Mirror user's chat language — templates ship in English but LLM prompts and edits match user's active language.
- Walk template sections in order. Edit **section-by-section via the Edit tool**.
- Don't fabricate — leave placeholders.
- After substantive edits, run `/sdlc-kit:sync`.

Each interview has an explicit **expert triad** — role-play all three voices and keep them honest.

### 1. Requirements interview — *Senior PM + Software Engineer + Solutions Architect*

Gate: must complete and user approve before design.

**Triad lenses:**
- **Senior PM** — Who is the user? What outcome? Which KPI? MoSCoW priority? Smallest thing that solves the problem?
- **Software Engineer** — Testable? Unambiguous AC? What edge cases? Realistic effort?
- **Solutions Architect** — Which NFRs does this inherit (latency, availability, security, LGPD, observability, cost)? Upstream/downstream systems? Architectural constraints?

The triad signs off on every FR and NFR: PM owns *why*, engineer owns *verification*, architect owns *fit*.

Walk the template, one focused question per section:

1. **Product context (§1)** — problem statement, personas (+ anti-persona), KPIs with baseline/target/window, strategic parent links (PRD / epic / OKR). *PM leads.*
2. **Scope (§2)** — in / out / assumptions / dependencies (upstream / downstream / external). *PM + Architect.*
3. **Actors & triggers (§3)** — actor-kind-trigger table. *Engineer + Architect.*
4. **User stories (§4)** — `As a <persona>, I want <capability>, so that <outcome>`. Each story lists REQs it covers. *PM leads.*
5. **Functional requirements (§6)** — elicit each REQ in **EARS** with **MoSCoW priority**, ≥ 1 **testable AC** (`Given / When / Then`) and explicit **rationale** linking to persona/KPI. *Engineer owns testability.*
6. **Non-functional requirements (§7)** — walk **all ten** sub-sections, confirm or mark `N/A (<reason>)`:
   - 7.1 Performance — p95 latency, throughput.
   - 7.2 Scalability & capacity — horizontal scaling, data volume ceilings.
   - 7.3 Reliability & availability — SLO, error budget, RPO/RTO.
   - 7.4 Security — AuthN, AuthZ, input validation, secrets, transport.
   - 7.5 Privacy & compliance — **LGPD** minimization, subject rights, masking, retention, audit trail.
   - 7.6 Observability — structured logs, RED/USE metrics, OTEL traces, SLO-burn alerts.
   - 7.7 Accessibility & usability — **WCAG 2.1 AA** on user-facing surfaces.
   - 7.8 Maintainability & quality — coverage, linter/type-checker gates, docs.
   - 7.9 Portability & i18n — locales, runtime.
   - 7.10 Cost — budget at the load profile.
   Each NFR is **testable** (metric, target, measurement method). Cross-cutting NFRs go in the TRD (`[[TRD-<slug>]]`); link, don't duplicate. *Architect leads.*
7. **Edge cases & failure modes (§8)** — triad's failure brainstorm; each item maps to AC or is explicitly tolerated. *Engineer leads.*
8. **Explicitly out of scope (§9)** — sharpen §2.2. *PM leads.*
9. **Traceability matrix (§10)** — REQ ↔ story ↔ task ↔ test. Orphans block at tasks-approval. *Engineer maintains.*
10. **Open questions (§11)** — with owner and deadline.

Approve:
```bash
python "...spec.py" --action transition --slug <slug> --doc requirements --to approved
```
Then `/sdlc-kit:sync` and proceed to design.

### 2. Design interview — *Senior SWE + AppSec Engineer + Software Architect*

Gate: requirements must be `approved`. If not, stop and say so.

**Triad lenses:**
- **Senior SWE** — Simplest thing that works? Module boundary? Plausible failures? How will we know at 3 a.m.?
- **AppSec** — Trust boundary? STRIDE? Least-privilege? Logging anything we shouldn't? Input validated at boundary?
- **Software Architect** — Which pattern? Alternatives rejected? Stays inside architectural style? Evolves without breaking consumers?

Design by **deliberate pattern choice**. Every structural decision names problem, chosen pattern, rationale, rejected alternatives.

Walk the template:

1. **Overview (§1)** — 2 paragraphs: what + why this shape. *Engineer leads.*
2. **Architectural drivers (§2)** — pull NFRs from `[[<feature>-requirements]]` §7; each driver drives ≥ 1 design implication. *Architect leads.*
3. **Design principles & patterns (§3)** — principles adopted (DDD / hexagonal / clean / CQRS / event-driven / functional core …) **with rationale**; *Patterns in use* table one row per problem with pattern + rationale + alternatives rejected; explicit non-goals. *Architect + Engineer.*
4. **System architecture (§4)** — Mermaid C4 container/component; layering and module boundaries; new + modified components. Reflect **reality**, not intent. *Architect leads.*
5. **Main flows (§5)** — sequence diagrams for happy path + ≥ 1 failure/compensation path. *Engineer leads.*
6. **Data model (§6)** — conceptual (aggregates + invariants), physical schema, **indexing strategy** (one row per index with query it serves), **consistency model** (strong/eventual, transactions, concurrency), **migrations & evolution** (expand/contract, backfill volume + duration + risk), **data classification** (public/internal/personal/sensitive → at-rest/in-transit/in-logs). *Engineer + AppSec (classification).*
7. **Contracts (§7)** — sync APIs (table + OpenAPI/proto + **RFC 7807** error model + backwards-compat); async events (direction, schema, delivery semantics, partition key, DLQ); external integrations (SLA, auth, rate limits, circuit-breaker params). *Architect leads; Engineer owns schemas.*
8. **Security design (§8)** — **threat-model before implementation** as a merge gate. Trust boundaries → **STRIDE-per-component** table → AuthN/AuthZ → input validation & output encoding → secrets & key management → privacy (LGPD/GDPR) → dependency & supply chain (SBOM, vuln SLA, signed images) → logging/telemetry hardening (PII/secret scrubber, tamper-evident audit log). *AppSec leads.*
9. **Observability (§9)** — **SLIs & SLOs** table with error budgets; structured log format + levels; **RED + USE** metrics (names explicit); OTEL traces with baggage; dashboards + alerts (SLO burn fast/slow, DLQ > 0) + runbook. *Engineer leads; Architect signs SLOs.*
10. **Performance & capacity plan (§10)** — load profile, per-layer budget, hot-path / N+1 audit, load-test plan mapped to NFR-PERF-*. *Architect + Engineer.*
11. **Resilience & failure modes (§11)** — failure/detection/response/recovery table; patterns (circuit breaker, bulkhead, timeout + retry with jitter, graceful degradation, idempotent consumers, outbox, saga compensations). *Engineer leads.*
12. **Deployment & rollout (§12)** — environments, feature flag + ramp + kill-switch, migration ordering (expand → code → backfill → cutover → contract), rollback with data-loss boundary. *Architect + Engineer.*
13. **Testing strategy (§13)** — unit / contract / integration / E2E / security / performance / chaos — sets contract for `tasks.md` Phase 3+. *Engineer leads.*
14. **Local decisions (§14)** — feature-scoped only; structural/cross-feature decisions → `/sdlc-kit:adr`.
15. **Technical risks (§15)** — risk / likelihood / impact / mitigation / owner.
16. **Open questions (§16)** — owner and deadline.

Approve:
```bash
python "...spec.py" --action transition --slug <slug> --doc design --to approved
```

### 3. Tasks expansion — *TDD-driven, bite-sized, Conventional Commits, git-worktree per task, Kiro markers*

Gate: design must be `approved`. If not, stop.

This is an **executable playbook**. The scaffolded `tasks.md` already carries the full playbook (Kiro markers table, 4 invariants, Conventional Commits allowed-types, git-worktree skeleton and copy-this-block task template). Populate — don't rewrite the playbook.

**Invariants for every task:**

1. **TDD mandatory.** Red → green → refactor → commit. Each step 2–5 min.
2. **Bite-sized.** ≤ 2h; split if any step balloons.
3. **One worktree per task.** Isolated `git worktree` branch (`.worktrees/<task-slug>`, per `superpowers:using-git-worktrees`). Main stays clean.
4. **Conventional Commits for branch *and* commit.** Branch: `<type>(<slug>)/<task-slug>`. Commit: `<type>(<slug>): <subject>`. Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `build`, `ci`.
5. **Kiro markers — only one `[-]` at a time per `tasks.md`.** Drive via `/sdlc-kit:task {start|complete|block|reopen}`. Never edit text, IDs, or `Requirements satisfied` refs — only marker + blocker note.

| Marker | Logical status | Meaning |
|---|---|---|
| `- [ ]` | `queued` | Planned, not started. |
| `- [-]` | `in_progress` | Actively being worked on. **Only one per file.** |
| `- [x]` | `completed` | Delivered, merged, worktree cleaned. |
| `- [~]` | `needs_attention` | Blocked; reason noted on the line below. |

**Populating `tasks.md`:**

1. **Preserve the playbook.** Leave "How to read this file", "Invariants", "Conventional Commits", "Git worktree workflow" sections untouched.
2. **Remove example TASKs** and replace with real ones from the design:

   | Phase | Pull from `design.md` |
   |---|---|
   | **Phase 1 — Setup** | migrations (§6.5), scaffolding (§4.1 new components), feature-flag wiring (§12). |
   | **Phase 2 — Domain logic (TDD)** | one TASK per aggregate / use case in §6.1; one TASK per validation rule (§8.4). |
   | **Phase 3 — Transport** | one TASK per endpoint happy-path (§7.1); one per error-mapping suite (RFC 7807); one per emitted/consumed event (§7.2). |
   | **Phase 4 — Observability** | one TASK per SLI/metric/log/trace from §9; one per alert. |
   | **Phase 5 — Deploy** | migration in staging → canary → promote, per §12. |

3. **Use the template's copy-me block** for each TASK:
   ```
   - [ ] **TASK-NNN** — <short imperative title>
     - **Branch:** `<cc-type>({{SLUG}})/<task-slug>`
     - **Worktree:** `.worktrees/<task-slug>`
     - **Requirements satisfied:** [[<slug>-requirements#REQ-NNN]]
     - **Steps:**
       1. Write failing test `<path/to/test>` asserting `<behavior>`.
       2. Run `<test-command>` — expect failure with `<expected-error>`.
       3. Implement minimal change in `<path/to/file>`.
       4. Run `<test-command>` — expect pass.
       5. Refactor (optional).
       6. Commit: `<cc-type>({{SLUG}}): <commit-subject>`.
       7. Push branch + open PR.
       8. After merge: `git worktree remove` + delete branch.
   ```
   Every TASK must: (a) name real paths/commands/errors; (b) link to ≥ 1 `[[<slug>-requirements#REQ-NNN]]`; (c) pick a branch `type` matching the work.

4. **Update the Summary section** (total tasks, critical path, parallelizable tracks).

5. **Traceability check before approving:** every REQ in §6 maps to ≥ 1 TASK; every TASK maps to ≥ 1 REQ. Reject orphans.

Approve:
```bash
python "...spec.py" --action transition --slug <slug> --doc tasks --to approved
```

From this point, **task lifecycle is operated by `/sdlc-kit:task`**.

## Status transitions reference

| Intent | Verb | Target |
|---|---|---|
| User approves a doc | "approve" / "looks good" / "ship it" | `approved` |
| Implementation done | "implemented" / "done building" | `implemented` |
| Obsolete, keep for history | "archive" / "shelve" | `archived` |
| Re-open for edits | "reopen" / "back to draft" | `draft` |

Bulk archive:
```bash
python "...spec.py" --action transition --slug <slug> --doc all --to archived
```

## Output contract

```json
// --action list
{
  "status": "ok", "action": "list",
  "vault_root": "/abs/path/.sdlc",
  "features": [
    {
      "slug": "login-google",
      "path": "04-specs/login-google",
      "docs": [
        {"kind": "requirements", "path": "04-specs/login-google/requirements.md",
         "exists": true, "title": "Requirements — Login with Google",
         "status": "approved", "updated": "2026-04-14"},
        {"kind": "design", "path": "04-specs/login-google/design.md",
         "exists": true, "title": "Design — Login with Google",
         "status": "draft", "updated": "2026-04-16"},
        {"kind": "tasks", "path": "04-specs/login-google/tasks.md",
         "exists": false, "title": "", "status": "", "updated": ""}
      ]
    }
  ],
  "count": 1, "errors": []
}

// --action scaffold
{
  "status": "ok", "action": "scaffold",
  "slug": "login-google",
  "spec_dir": "04-specs/login-google",
  "docs": [
    {"kind": "requirements", "path": "…/requirements.md", "was_new": true, "skipped": false},
    {"kind": "design",       "path": "…/design.md",       "was_new": true, "skipped": false},
    {"kind": "tasks",        "path": "…/tasks.md",        "was_new": true, "skipped": false}
  ],
  "errors": []
}

// --action transition --doc requirements --to approved
{
  "status": "ok", "action": "transition",
  "slug": "login-google",
  "spec_dir": "04-specs/login-google",
  "docs": [
    {"kind": "requirements", "path": "…/requirements.md",
     "previous_status": "draft", "new_status": "approved", "changed": true}
  ],
  "errors": []
}
```

**Exit codes:** `0` ok/dry-run · `1` user error · `2` fatal.

## Guardrails

**Never:**
- Start design before `requirements.md` is `approved`.
- Start tasks before `design.md` is `approved`.
- Rewrite a doc in one Edit call.
- Auto-promote to `approved`.
- Overwrite scaffold without `--force` and explicit confirmation.
- Fabricate content. Leave placeholders.
- Skip the expert triad. If a lens has nothing to add, state it explicitly.
- Leave NFR sub-sections (7.1–7.10) unvisited. Fill or `N/A (<reason>)`.
- Skip the §8 threat model. AppSec is a merge gate.
- Approve `tasks.md` with orphan REQs or orphan TASKs.
- Approve `tasks.md` if any step isn't 2–5 min, or any TASK lacks Branch/Worktree/Requirements/Steps, or any branch violates Conventional Commits.
- Edit Kiro markers by hand — use `/sdlc-kit:task`.
- Touch `CLAUDE.md` or `_MOC.md`.

**Always:**
- Mirror user's chat language; announce triad at the top of each interview.
- Run `--action list` before scaffold/transition.
- Confirm slug before scaffolding.
- Invoke `/sdlc-kit:sync` after any scaffold, edit, or transition.
- Include wikilinks between siblings: `[[<slug>-requirements]]`, `[[<slug>-design]]`, `[[<slug>-tasks]]`.
- Keep §10 traceability matrix updated; run it before approving `tasks.md`.
- Cross-cutting NFRs → TRD; link, don't duplicate.
- Preserve the invariants / Kiro / CC / git-worktree sections of `tasks.md.tpl`.

## Examples

**Fresh trio:**
```
User: /sdlc-kit:spec new "Login with Google"
AI:   "Proposed slug: `login-with-google`. Keep or rename?"
User: "login-google"
AI:   [scaffold --slug login-google --title "Login with Google"]
AI:   "Let's fill requirements section by section. First: **Scope** — what does this feature do, and what's out?"
User: <answer>
AI:   [Edit: replace Scope]
…
AI:   "All sections filled. Approve requirements and move to design?"
User: y
AI:   [transition --doc requirements --to approved][/sdlc-kit:sync]
AI:   "✓ approved. Starting design. **Overview** — 2 paragraphs on technical approach."
…
```

**Mid-flight resume:**
```
User: continua a spec do login-google
AI:   [list] R:approved D:draft T:missing. Resuming design at **Data model**.
```

**Gate violation:**
```
User: pode ir direto para as tasks do login-google
AI:   "Design is `draft` — tasks are gated on approved design. Finish design first, or approve as-is?"
```

**Archive:**
```
User: archive the old login-password spec
AI:   [transition --doc all --to archived][/sdlc-kit:sync]
```

## See also

- `scripts/spec.py` — file-op helper.
- `assets/vault-tree/04-specs/_templates/`.
- `/sdlc-kit:prd`, `/sdlc-kit:adr`, `/sdlc-kit:trd`, `/sdlc-kit:task`, `/sdlc-kit:sync`.
