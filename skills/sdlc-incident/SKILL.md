---
name: sdlc-incident
description: |
  Use when the user wants to record, walk, or close a **production incident** —
  the real-time event report plus the post-mortem lessons doc. One file per
  incident under `07-retrospectives/incidents/<slug>.md`, slug-based (usually
  `inc-YYYY-MM-DD-<short-topic>`) because the slug is what on-call, responders
  and stakeholders will reference forever after. Typical triggers in English:
  `/sdlc-kit:incident`, `/sdlc-kit:incident new <title>`, `/sdlc-kit:incident
  list`, `/sdlc-kit:incident mitigate <slug>`, `/sdlc-kit:incident resolve
  <slug>`, `/sdlc-kit:incident post-mortem <slug>`, or phrases like "log an
  incident", "open an incident", "we have a SEV1", "start an incident record",
  "the API is down — capture it", "P0 outage", "run the post-mortem",
  "attach the lessons learned". Typical triggers in pt-BR: "registrar um
  incidente", "abrir incidente", "temos um SEV1", "o gateway caiu, documenta
  isso", "rodar o pós-mortem", "anexar lições aprendidas", "incidente P0". This
  skill is co-authored by a duo of expert personas: an **SRE / On-Call
  Engineer** (drives detection, mitigation, timeline, SLO impact, RCA under
  time pressure) and an **Engineering Lead** (drives the lessons doc, action
  items, ownership, and follow-through after the customer pressure is gone).
  Incidents move through a strict 4-state lifecycle (`open → mitigated →
  resolved → post-mortem`). Every severity is enforced (SEV1 | SEV2 | SEV3 |
  SEV4) — no custom severity strings. The script auto-fills `mitigated_at` and
  `resolved_at` frontmatter timestamps when flipping status so the MTTD/MTTM/
  MTTR math in `_INDEX.md` stays honest. The LLM drives the narrative content
  (summary, timeline rows, impact, mitigation applied, lessons) via Edit/Write,
  always mirroring the user's active conversation language. Slugs are stable
  references — incidents are NEVER deleted, even after post-mortem, because
  the vault's incident history is a learning asset. After scaffold or
  transition, invokes `/sdlc-kit:sync` so MOCs and `_INDEX.md` reflect the
  change. Do not invoke for sprint retrospectives (use `/sdlc-kit:retro`), PR
  reviews (use `/sdlc-kit:review`), or general operational tasks
  (use `/sdlc-kit:task`).
---

# sdlc-kit:incident

Creates and walks an **incident record** from detection through post-mortem,
under `07-retrospectives/incidents/<slug>.md`.

An incident is the **single source of truth for one production event** — the
timeline the on-call engineer builds during the event, plus the lessons the
Engineering Lead distills afterward. The vault is append-only for incidents:
every SEV1 through SEV4 event is recorded and kept forever because the next
outage usually rhymes with the last one.

---

## What an incident is (and isn't)

| Incident is… | Incident isn't… |
|---|---|
| A real production event with customer impact (or near miss) | A sprint retrospective — that's `/sdlc-kit:retro` |
| Time-stamped: `detected_at`, `mitigated_at`, `resolved_at` are first-class and feed MTTD/MTTM/MTTR | A bug report — that's a task, use `/sdlc-kit:task` |
| Slug-based (`inc-2026-04-18-db-outage`) and stable; never renamed, never deleted | A feature review — that's `/sdlc-kit:review` |
| Severity-rated (`SEV1..SEV4`) — the severity shapes response, comms and audit needs | A policy or runbook — link those from the record |
| Co-authored by **SRE/On-Call** (during) and **Engineering Lead** (after) | A solo document — one lens only will miss either mitigation facts or organizational learning |
| Paired with a lessons companion doc at `<slug>-lessons.md` once it reaches `post-mortem` | An incident is only "closed" when it hits `post-mortem` — `resolved` means the *technical* fix shipped, not that the organization has learned |

---

## Severity scale

| Severity | Meaning | Example |
|---|---|---|
| **SEV1** | Total outage, revenue or data at risk, 24/7 response | Payments API 100% error rate; prod DB cluster down; customer data exposed |
| **SEV2** | Severe degradation, major customer impact, business hours response escalatable | Checkout latency p95 > 5s for 20% of tenants; auth provider partial outage |
| **SEV3** | Minor issue, workaround available, limited impact | One region runs on stale cache; background job queue 2h behind |
| **SEV4** | Cosmetic / tracked for follow-up, no direct user impact | Typo in empty-state copy; internal dashboard chart broken |

The severity **must** be locked in at scaffold time (`--severity SEV1` etc.) —
default is `SEV3`. The script enforces the enum via argparse choices; `SEVERE`,
`P0`, `critical`, etc. are not accepted. If severity changes during the event,
record the change in the body with justification — **never silently downgrade**
severity in the frontmatter.

---

## Lifecycle

```
open        — incident detected and recorded; responders engaged
mitigated   — bleeding stopped, customers unblocked; root cause maybe unknown;
              `mitigated_at` auto-filled with today's date when flipping in
resolved    — fix in production, no customer impact, monitoring clean;
              `resolved_at` auto-filled with today's date when flipping in
post-mortem — terminal. Lessons doc attached at
              `07-retrospectives/incidents/<slug>-lessons.md`; action items
              tracked; NO auto-fill (timestamps must already be set)
```

Rewinding to `open` after the fact (rare — only when something truly regresses)
does NOT clear the timestamps. They are historical facts and must remain
auditable.

The auto-fill uses today's date as a **best-effort default**. The LLM should
offer the user a chance to correct `mitigated_at` / `resolved_at` after the
transition if the actual event happened on a different day (common for
incidents crossing midnight UTC).

---

## When to invoke

Invoke when:

- The user types `/sdlc-kit:incident`, `/sdlc-kit:incident new <title>`,
  `/sdlc-kit:incident list`, `/sdlc-kit:incident mitigate <slug>`,
  `/sdlc-kit:incident resolve <slug>`, `/sdlc-kit:incident post-mortem <slug>`.
- The user says "we have a SEV1", "open an incident", "the API is down, log
  it", "P0 outage", "register um incidente", "rodar o pós-mortem", or any
  equivalent phrasing in any language.
- An alert fired, a customer reported an outage, or a near-miss is worth
  capturing before memory fades — **if in doubt, log it**; the cost of an
  extra SEV4 record is trivial compared to the cost of missing a pattern.

**Do not** invoke when:

- The user wants a sprint retrospective → `/sdlc-kit:retro`.
- The user wants a PR review record → `/sdlc-kit:review`.
- The user wants to track a bug or operational task that is NOT a production
  event → `/sdlc-kit:task`.
- cwd is not inside a vault.

---

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; abort if missing.
2. **Python 3.10+** available.
3. **Template exists** at
   `<vault>/07-retrospectives/_templates/incident.md.tpl`. If missing (legacy
   vault), suggest `/sdlc-kit:init` repair.

---

## The expert duo

Every incident record is co-authored by two lenses, at different phases:

| Phase | SRE / On-Call lens | Engineering Lead lens |
|---|---|---|
| `open` → `mitigated` | **Primary driver.** Real-time timeline rows, symptom vs cause, mitigation attempts, SLO burn, comms to stakeholders | Supports: helps compose status updates, protects responders from distractions |
| `mitigated` → `resolved` | **Primary driver.** Drives the technical fix, verification, monitoring, unblock confirmation | Supports: queues up the post-mortem process, starts the lessons skeleton |
| `resolved` → `post-mortem` | Supports: provides facts, reviews the 5-whys, sanity-checks the timeline reconstruction | **Primary driver.** Owns the `<slug>-lessons.md` companion doc, drives the 5-whys / systemic root cause, assigns action items with owners and by-when |

Announce the duo at the start of the interaction so the user knows which lens
is active now:

> "I'll run this incident as a duo: **SRE / On-Call** drives mitigation while
> we're in the event; **Engineering Lead** owns the lessons doc and follow-up
> once we're past `resolved`. Right now we're in `<current-status>`, so the
> **<primary>** lens is leading."

---

## Flow

### List: `/sdlc-kit:incident` or `/sdlc-kit:incident list`

1. Run `incident.py --action list`. Parse the JSON `incidents` array.
2. Show a compact table: `slug | severity | status | title | owner | updated`.
3. If empty, offer: "No incidents yet. Open one with
   `/sdlc-kit:incident new <title>` when the next alert fires."
4. Otherwise, highlight any `open` or `mitigated` rows — those are live and
   deserve attention first.

### New incident: `/sdlc-kit:incident new <title>`

This is usually invoked **under time pressure** (the event is happening now).
Keep the pre-scaffold interview to a minimum — the minimum viable scaffold is
just severity and a short title. The interview expands after `mitigated`.

1. **Severity first.** Ask which SEV (1/2/3/4) with a one-line example for
   each. If the user answers "SEV1 / P0 / critical" style, map to `SEV1` and
   confirm.
2. **Derive the slug.** Default to `inc-<YYYY-MM-DD>-<short-kebab>`. The date
   prefix is not required by the slug regex but strongly recommended — it
   keeps the `list` output chronologically meaningful.
3. **List first** so you can warn about a collision early.
4. **Scaffold.** Run:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-incident/scripts/incident.py" \
     --vault-root "<vault>" --action scaffold \
     --slug "<slug>" --title "<title>" \
     --severity "<SEV1|SEV2|SEV3|SEV4>" \
     [--owner "<incident commander>"] \
     [--detected-at "<YYYY-MM-DD>"]
   ```
   `--severity` defaults to `SEV3` if omitted. `--detected-at` defaults to
   today. The script refuses to overwrite an existing slug unless `--force`
   is passed; never pass `--force` without the user's explicit instruction.
5. **Minimum content during the event** (SRE/On-Call lens):
   - One-line **Summary** — what, who's affected, current state.
   - First **Timeline** row — detection time + source (alert name, customer
     report, synthetic check).
6. Everything else — full impact, mitigation details, immediate cause — can
   wait until after `mitigated`.

### Walking through the lifecycle

#### `open` → `mitigated`: `/sdlc-kit:incident mitigate <slug>`

1. **SRE lens drives.** Confirm with the user that bleeding has actually
   stopped — no new errors, customer journeys restored, SLO burn flattening.
2. Run:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-incident/scripts/incident.py" \
     --vault-root "<vault>" --action transition \
     --slug "<slug>" --to mitigated
   ```
   The script auto-fills `mitigated_at` in the frontmatter. Report back the
   value from `timestamps_updated` so the user can correct it if the event
   actually mitigated on a different day (crossed midnight UTC, etc.).
3. Expand the body (still SRE lens): fill the Timeline rows that were missing,
   capture the Mitigation section, fill MTTD/MTTM placeholders.

#### `mitigated` → `resolved`: `/sdlc-kit:incident resolve <slug>`

1. **SRE lens drives, Engineering Lead warms up.** The fix is in production,
   monitoring is clean, post-mitigation observation window elapsed.
2. Run:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-incident/scripts/incident.py" \
     --vault-root "<vault>" --action transition \
     --slug "<slug>" --to resolved
   ```
   `resolved_at` auto-fills; `mitigated_at` is left alone.
3. Fill the Impact section fully (users, revenue, systems), MTTR, immediate
   cause.

#### `resolved` → `post-mortem`: `/sdlc-kit:incident post-mortem <slug>`

**This is a hard gate.** Do NOT run the transition until the following
pre-post-mortem checklist is green:

- [ ] `mitigated_at` is set in the frontmatter (not empty).
- [ ] `resolved_at` is set in the frontmatter (not empty).
- [ ] Body has a **root cause** narrative (5-whys or equivalent) — not just
      the immediate cause, the systemic one.
- [ ] Companion lessons doc exists at
      `07-retrospectives/incidents/<slug>-lessons.md`. The Engineering Lead
      owns this file; create it via **Write** with the 5-whys, contributing
      factors, "what went well / what went wrong / what we'll change", and
      an **action items table** (`owner | by-when | tracker link`).
- [ ] Every action item in the lessons doc has a named owner and a by-when
      date. "Unassigned / TBD" is not acceptable at post-mortem — that's
      how action items die.

If any box is unchecked, do NOT transition — invite the user to close the gap
first. If they push past, capture the exception in the body before running
the transition.

Run:
```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-incident/scripts/incident.py" \
  --vault-root "<vault>" --action transition \
  --slug "<slug>" --to post-mortem
```

No timestamps auto-fill at this stage — `timestamps_updated` will be `[]`.
The incident is now **terminal**. It stays in the vault forever, feeding the
next "has this happened before?" search.

#### Rewind to `open`: `/sdlc-kit:incident reopen <slug>`

Rare — only use when something truly regresses and you need to walk the
lifecycle again. The existing timestamps are NOT cleared (they remain
historical). Consider whether a **new** incident with a different slug would
be more honest than a rewind.

### Sync

After every `scaffold` or `transition`, invoke `/sdlc-kit:sync` so
`_INDEX.md`, `07-retrospectives/_MOC.md`, and the open-incidents counter
reflect the change. During an active SEV1 you can defer the sync until the
event mitigates — but never skip it past `resolved`.

---

## Output contract

```json
// --action list
{
  "status": "ok",
  "action": "list",
  "vault_root": "/abs/path/.sdlc",
  "incidents": [
    {
      "slug": "inc-2026-04-18-db-outage",
      "path": "07-retrospectives/incidents/inc-2026-04-18-db-outage.md",
      "title": "Database outage on 2026-04-18",
      "status": "mitigated",
      "severity": "SEV1",
      "owner": "Milton",
      "detected_at": "2026-04-18",
      "mitigated_at": "2026-04-18",
      "resolved_at": "",
      "updated": "2026-04-18"
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
  "slug": "inc-2026-04-18-db-outage",
  "incident_path": "07-retrospectives/incidents/inc-2026-04-18-db-outage.md",
  "was_new": true,
  "errors": []
}

// --action transition (with timestamp side-effect)
{
  "status": "ok",
  "action": "transition",
  "vault_root": "/abs/path/.sdlc",
  "slug": "inc-2026-04-18-db-outage",
  "incident_path": "07-retrospectives/incidents/inc-2026-04-18-db-outage.md",
  "previous_status": "open",
  "new_status": "mitigated",
  "timestamps_updated": ["mitigated_at"],
  "errors": []
}

// --action transition (idempotent or no side-effect)
{
  "status": "ok",
  "action": "transition",
  "vault_root": "/abs/path/.sdlc",
  "slug": "inc-2026-04-18-db-outage",
  "incident_path": "07-retrospectives/incidents/inc-2026-04-18-db-outage.md",
  "previous_status": "resolved",
  "new_status": "post-mortem",
  "timestamps_updated": [],
  "errors": []
}
```

**Exit codes:** `0` ok/dry-run · `1` user error (invalid slug/status/severity,
incident not found, collision without `--force`) · `2` fatal (permission
denied, IO, missing template).

---

## Guardrails

**Never:**
- **Delete an incident.** Even a SEV4 typo-level event. The vault's incident
  history is a learning asset; every record is reachable forever. If an
  incident was logged in error (the alert was flapping, no real impact),
  transition to `post-mortem` with a lessons doc that says so — don't erase.
- **Downgrade severity silently.** If a SEV1 turns out to be a SEV3 after
  investigation, update the frontmatter AND write a body paragraph
  explaining the re-grade with timestamps. No quiet edits.
- **Skip to `post-mortem` before the pre-post-mortem checklist is green.**
  The lessons doc must exist; action items must have owners; timestamps
  must be set. The gate is there so post-mortems don't become rituals.
- **Auto-fill a timestamp that already has a value.** The script deliberately
  checks for empty fields before writing, and the LLM must never pass
  instructions that would override a historical timestamp.
- **Rename an incident.** The slug is a stable reference — dashboards, Slack
  threads, Jira tickets and runbooks link to it. If the title was wrong, edit
  the `title:` frontmatter key; never move the file.
- **Skip the duo.** SRE lens drives during the event, Engineering Lead drives
  after. If either lens is missing, the record is incomplete — either the
  mitigation facts or the organizational learning will be wrong.
- **Write the lessons doc in the main incident file.** The lessons file is a
  separate artifact at `<slug>-lessons.md` so it can evolve independently
  (action item reviews, follow-up tickets) without thrashing the incident
  timeline.

**Always:**
- Match the user's active conversation language — in a live incident, speed
  matters; match the language the responders are speaking.
- Announce the duo and name the currently-active lens at each transition.
- Run `--action list` before `scaffold` so you can report collisions early.
- After `mitigate` / `resolve`, show the user the `timestamps_updated` value
  and offer to correct it if the real event happened on a different day.
- Before `post-mortem`, walk the pre-post-mortem checklist with the user,
  item by item. Don't skip the checklist just because the responders are
  tired.
- Invoke `/sdlc-kit:sync` after any scaffold or transition (deferrable during
  live SEV1, mandatory by `resolved`).
- Surface the generated file path in the final report so the user can open it.

---

## Examples

> Examples below are in English. In a real session, mirror the user's active
> conversation language in every user-facing line.

**Opening a SEV2 incident mid-event:**
```
User: /sdlc-kit:incident new Checkout p95 latency spike
AI:   "Severity? SEV1 = total outage, SEV2 = severe degradation with
       customer impact, SEV3 = minor/workaround, SEV4 = cosmetic."
User: SEV2, latency is at 4s for ~20% of tenants.
AI:   [list] 0 incidents today. Proposed slug: `inc-2026-04-18-checkout-latency`.
User: go.
AI:   [scaffold --slug inc-2026-04-18-checkout-latency --severity SEV2
         --title "Checkout p95 latency spike"]
      created 07-retrospectives/incidents/inc-2026-04-18-checkout-latency.md
      (status=open, severity=SEV2, detected_at=2026-04-18).
AI:   "SRE lens active. One-line Summary, and the first Timeline row
       (detection time UTC + alert source)?"
User: Detected 14:07 UTC by `checkout-latency-p95` Grafana alert.
      20% of tenants affected, ~R$ 4k/min revenue at risk.
AI:   [Edit §Summary and §Timeline][/sdlc-kit:sync deferred — live incident]
```

**Transitioning to mitigated:**
```
User: /sdlc-kit:incident mitigate inc-2026-04-18-checkout-latency
AI:   "Confirming: bleeding stopped, new requests landing under 1s p95,
       no new alerts firing? [yes/no]"
User: yes, latency back to ~800ms p95 for 5min.
AI:   [transition --to mitigated]
      previous_status=open → new_status=mitigated.
      timestamps_updated=["mitigated_at"] → set to 2026-04-18.
AI:   "Mitigated at 2026-04-18 (today). If the actual mitigation happened
       on a different day, I can correct `mitigated_at` now — otherwise I'll
       leave it. Now let's fill the rest of the Timeline rows and the
       Mitigation Applied section while it's fresh."
```

**Closing with post-mortem (hard gate):**
```
User: /sdlc-kit:incident post-mortem inc-2026-04-18-checkout-latency
AI:   "Engineering Lead lens active. Walking the pre-post-mortem checklist
       before I flip the status:
       - mitigated_at set? ✓ (2026-04-18)
       - resolved_at set? ✓ (2026-04-18)
       - Root-cause narrative in body (5-whys)? ✓
       - Companion lessons doc at
         07-retrospectives/incidents/inc-2026-04-18-checkout-latency-lessons.md? ✗
       - Action items with named owners + by-when? (blocked on lessons doc)"
AI:   "Lessons doc doesn't exist yet. Want me to Write it now with the
       5-whys skeleton + action item table so we can fill it before
       flipping to post-mortem?"
User: yes, create it and let's fill it.
AI:   [Write <slug>-lessons.md with 5-whys skeleton][interview lessons content]
AI:   "Lessons doc ready, 3 action items each with owner + by-2026-05-02.
       Ready to transition to post-mortem."
AI:   [transition --to post-mortem]
      previous_status=resolved → new_status=post-mortem.
      timestamps_updated=[] (no auto-fill at post-mortem).
      [/sdlc-kit:sync]
AI:   "✓ Incident inc-2026-04-18-checkout-latency is now closed (post-mortem).
       Lessons at [[inc-2026-04-18-checkout-latency-lessons]]. 3 action items
       queued — I can open tickets for each if you want."
```

---

## See also

- `scripts/incident.py` — file-op helper.
- `assets/vault-tree/07-retrospectives/_templates/incident.md.tpl` — canonical
  incident template (timeline + impact + mitigation + references).
- `assets/vault-tree/07-retrospectives/_templates/incident-lessons.md.tpl` —
  companion lessons template (5-whys + action items), created manually by the
  LLM via Write at post-mortem time.
- `/sdlc-kit:retro` — sprint retrospectives (not incident-specific).
- `/sdlc-kit:review` — PR review records.
- `/sdlc-kit:sync` — always invoked after incident edits.
