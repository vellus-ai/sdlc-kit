---
name: sdlc-retro
description: |
  Use when the user wants to hold, facilitate, or close out a sprint / iteration retrospective —
  the team ritual at the end of a delivery cycle where the team names what went well, what went
  badly, and commits to concrete action items. One file per retro under
  `07-retrospectives/retros/<slug>.md`, slug-based (e.g. `sprint-42`, `iteration-2026-q2-w3`).
  Typical triggers are `/sdlc-kit:retro`, `/sdlc-kit:retro new <title>`, `/sdlc-kit:retro list`,
  `/sdlc-kit:retro final <slug>`, or phrases like "hold retrospective", "sprint retro", "close
  iteration", "end-of-sprint retro", "run the retro", "ratify retro actions", "fazer retro",
  "retrospectiva de sprint", "fechar ciclo", "encerrar sprint", "retrô do time" — in any
  language the user happens to be using. This skill is co-authored by a duo of expert personas:
  an **Agile Facilitator / Scrum Master** (runs the meeting, keeps the conversation safe and
  balanced, ensures every voice is heard) and an **Engineering Lead** (ensures every action
  item is concrete, owned, measurable, and that metrics like velocity, cycle time and bug
  count are captured with real numbers — not vibes). The script only does deterministic file
  ops — listing, scaffolding from `07-retrospectives/_templates/retro.md.tpl`, and the two-state
  lifecycle transition `draft → final`. The LLM drives the live interview (Keep / Improve /
  Stop, Actions with owner + due date, team mood, metrics) via Edit/Write, always mirroring the
  user's active conversation language. Slugs are stable references and retros are never renamed.
  After scaffold or transition, invokes `/sdlc-kit:sync` so MOCs and `_INDEX.md` reflect the
  change. Do NOT invoke for PR reviews (use `/sdlc-kit:review`), for incident post-mortems
  (use `/sdlc-kit:incident`), or forward-looking planning (out of scope).
---

# sdlc-kit:retro

Facilitates and records sprint / iteration retrospectives under `07-retrospectives/retros/`.

A retro is the **team's closing ritual** for a delivery cycle — a fixed-length box where the team
looks back honestly, names what to keep, what to improve, what to stop, and ratifies a short list
of concrete, owned action items. The document that remains after the meeting is the audit trail:
future retros reference it, action items are tracked against it, and the cycle's metrics
(velocity, cycle time, bug count, incidents) live alongside the narrative.

---

## What a retro is (and isn't)

| Retro is… | Retro isn't… |
|---|---|
| A sprint/iteration closing ritual — team-level, time-boxed, recurring | A PR review — that belongs to `/sdlc-kit:review` |
| Focused on process, collaboration, delivery flow | An incident post-mortem — a SEV incident gets its own `/sdlc-kit:incident` |
| Forward-looking: every "Improve" or "Stop" produces a concrete action item with owner + due date | A complaint log — a gripe with no action is not actionable |
| Evidence-based: metrics (velocity, cycle time, bugs, incidents) are captured with real numbers | A vibes-only meeting — "felt slow" is not a metric |
| Co-authored by **Agile Facilitator + Engineering Lead** | A solo write-up — if the facilitator leaves it to one person, the team has no retro |

Statuses form a simple two-state lifecycle: `draft` → `final`.

- `draft` — the retro meeting is in progress, or the facilitator is still collecting
  input. Keep/Improve/Stop bullets are being added, action items are being ratified,
  metrics are being filled in.
- `final` — the retro meeting is closed. Every action item has an owner and a due
  date. Keep/Improve/Stop each have real content. Metrics have numbers. The record
  is now historical and the next retro may reference it.

Transitions are idempotent: re-running `--to final` on an already-final retro is a
no-op. Reverse transitions (`final → draft`) are allowed because sometimes a retro
needs one more revision after the meeting (missed action item, corrected metric).

---

## Kind and path

| Kind    | Type slug | Path                                 | Template                                      |
|---------|-----------|--------------------------------------|-----------------------------------------------|
| `retro` | `retro`   | `07-retrospectives/retros/<slug>.md` | `07-retrospectives/_templates/retro.md.tpl`   |

Slug is mandatory at scaffold time. Recommended forms:

- Sprint-numbered: `sprint-42`, `sprint-43`
- Time-boxed iteration: `iteration-2026-q2-w3`, `cycle-2026-04`
- Team-scoped: `platform-sprint-12`, `mobile-iter-07`

Keep them short, ASCII-lowercase, hyphen-separated. The script rejects anything else.

---

## When to invoke

Invoke when:

- The user types `/sdlc-kit:retro`, `/sdlc-kit:retro new <title>`, `/sdlc-kit:retro list`,
  `/sdlc-kit:retro final <slug>`.
- The user says "hold retrospective", "sprint retro", "close iteration", "run the retro",
  "fazer retro", "retrospectiva de sprint", "fechar ciclo", or equivalent phrasing in any
  other language.
- A sprint just ended and the team is about to sit down to inspect it.
- The facilitator wants to pre-scaffold the retro note before the meeting so bullets can
  be captured live.

**Do NOT** invoke when:

- The user wants to review a Pull Request → `/sdlc-kit:review`.
- The user wants to post-mortem a production incident → `/sdlc-kit:incident`.
- The user wants to plan the next sprint (backlog grooming, capacity planning) →
  (out of scope; this skill captures past cycles only).
- The user wants a long-horizon portfolio retrospective spanning many projects →
  that's a PMO-level artifact, not a per-sprint retro.
- cwd is not inside a vault.

---

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; abort if missing.
2. **Python 3.10+** available.
3. **Template exists** at `<vault>/07-retrospectives/_templates/retro.md.tpl`. If missing
   (legacy vault), suggest `/sdlc-kit:init` repair.

---

## The expert duo

Every retro is co-authored, from scaffold forward. Announce the duo at the start of the
interview so the team knows which lenses are active:

> "I'll facilitate this retro as a duo: **Agile Facilitator** (runs the round,
> keeps the conversation balanced, makes sure every voice is heard) and
> **Engineering Lead** (pushes every action item to be concrete, owned, and
> due-dated, and insists on real numbers for velocity / cycle time / bug
> count). Let's walk the sections one at a time."

| Section | Agile Facilitator lens | Engineering Lead lens |
|---|---|---|
| Period | Confirm sprint boundaries, pull team list | Confirm which tickets/PRs closed in the window |
| Keep | Invite every team member to contribute at least one; balance louder vs quieter voices | Validate claims with evidence (metric, ticket, PR) |
| Improve | Surface tension without blame; reframe personal critique as process critique | Distinguish process gap from tooling gap from skill gap — each has a different fix |
| Stop | Name the practice precisely; no fuzzy "bad communication" | Tie each `Stop` to a concrete cost (time, incidents, rework) |
| Actions | Ensure every action has an owner who has *agreed*, not been assigned in absentia | Ensure every action has a due date and a check-in mechanism (next retro, task, ADR) |
| Team mood | Pulse-check: energy, confidence, psychological safety | Correlate mood with metrics — mood dip + velocity drop is worth naming |
| Metrics | Frame metrics as signal, not judgement | Fill numbers: velocity, cycle time P50/P95, bugs opened/closed, incidents, WIP |

---

## Flow

### List: `/sdlc-kit:retro` or `/sdlc-kit:retro list`

1. Run `retro.py --action list`. Parse the JSON `retros` array.
2. Show a compact table: `slug | status | title | owner | sprint | updated`.
3. If empty, offer: "No retros yet. Starting a new one? `/sdlc-kit:retro new <title>`."
4. Otherwise, offer next actions: open the latest draft, finalize a matured draft,
   or create a new one.

### New retro: `/sdlc-kit:retro new <title>`

1. **Derive the slug.** Propose a slug (lowercase ASCII, hyphen-separated) from the
   title — prefer the numeric sprint form `sprint-<NN>` when it applies. The user can
   override with `--slug`.
2. **Capture the sprint identifier** if the team uses one. It goes into the `sprint:`
   frontmatter field at scaffold time so `/sdlc-kit:retro list` can show it.
3. **List first** so you can warn about a slug collision early.
4. **Scaffold.** Run:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-retro/scripts/retro.py" \
     --vault-root "<vault>" --action scaffold \
     --slug "<slug>" --title "<title>" [--owner "<facilitator>"] [--sprint "<N>"]
   ```
   The script refuses to overwrite an existing slug unless `--force` is passed; never
   pass `--force` without the user's explicit instruction.
5. **Announce the duo** and start the live interview.

### The interview (LLM-driven, duo, live during the meeting)

Walk the template top-to-bottom. One focused prompt per section — edit in place via
the Edit tool, not a full-file rewrite. For each section, apply both lenses.

**Phase A — Frame the period**
1. Confirm sprint name, start date, end date, duration. Pull task counts / specs /
   ADRs / incidents from the automatic summary block if present. If the numbers look
   wrong, flag them and stop — a retro on the wrong period is worse than none.

**Phase B — Keep / Improve / Stop** (the core)

For each of the three buckets, do a round-robin: every teammate contributes at
least one item before anyone contributes a second. The facilitator lens enforces
turn-taking; the engineering lead lens pushes for specificity.

- **Keep** — practices / tools / rituals worth defending next sprint.
- **Improve** — things that mostly work but have a concrete improvement path.
- **Stop** — practices to discontinue *this sprint*, with a cost and an alternative.

A bullet that doesn't name a practice, or that blames a person rather than a
process, gets rewritten before it lands in the document.

**Phase C — Actions** (the commitment)

Every `Improve` or `Stop` bullet that the team cares about must produce at least
one Action row. Each action row must have:

- **Description** — imperative, verifiable. "Add a PR-size lint" not "be better".
- **Owner** — a real name who has *agreed* to own it. No "TBD".
- **Deadline** — a real date, usually `<next retro date>`.
- **Artifact** — link to the task / ADR / doc that will carry the work. If none
  exists yet, create it before the retro closes.

**Phase D — Team mood & metrics**

- **Team mood** — energy + confidence, 🟢/🟡/🔴, plus free-text pulse. This is
  qualitative on purpose. The engineering lead lens correlates mood with the
  metrics numbers.
- **Metrics** — velocity (story points or throughput), cycle time P50/P95, bugs
  opened / closed, incidents (count + SEV distribution), WIP ceiling adherence.
  Real numbers only. If a number isn't available, mark it `N/A — <reason>` rather
  than guess.

Keep the meeting bounded — roughly 60–90 minutes. Prefer N/A with a reason over
filibuster.

### Transition: `/sdlc-kit:retro {draft|final} <slug>`

Map verb → target status:

| Verb | Target status | When to use |
|---|---|---|
| `draft` | `draft` | Meeting ongoing, or post-meeting revision in progress |
| `final` | `final` | Meeting closed, actions ratified, metrics filled |

Run:
```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-retro/scripts/retro.py" \
  --vault-root "<vault>" --action transition \
  --slug "<slug>" --to "<draft|final>"
```

Idempotent: if the retro is already at the target status, the script writes nothing.

**Before transitioning to `final`**, walk the pre-final checklist with the team:

- [ ] **Keep / Improve / Stop each have real content** — no empty sections, no
  single-word bullets. A section with nothing to say is marked
  `N/A — <reason>` explicitly.
- [ ] **Every action item has an owner** (real name, not "team" or "TBD") who
  has *agreed* to own it.
- [ ] **Every action item has a due date**, usually `<next retro date>`.
- [ ] **Every action item has an artifact link** (task, ADR, doc) or an
  explicit plan for where it will be tracked.
- [ ] **Metrics have numbers** — velocity, cycle time, bugs, incidents.
  Missing numbers are `N/A — <reason>`, not silent gaps.
- [ ] **Team mood captured** — energy + confidence + at least one free-text note.

If any box is unchecked, do **not** transition to `final`. Ask the team to fill
the gap, or explicitly mark it N/A before closing.

### Sync

After every `scaffold` or `transition`, invoke `/sdlc-kit:sync` so `_INDEX.md` and
`07-retrospectives/_MOC.md` reflect the change.

---

## Output contract

```json
// --action list
{
  "status": "ok",
  "action": "list",
  "vault_root": "/abs/path/.sdlc",
  "retros": [
    {
      "slug": "sprint-42",
      "path": "07-retrospectives/retros/sprint-42.md",
      "title": "Retro — Sprint 42",
      "status": "draft",
      "owner": "Milton",
      "sprint": "42",
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
  "slug": "sprint-42",
  "retro_path": "07-retrospectives/retros/sprint-42.md",
  "was_new": true,
  "errors": []
}

// --action transition
{
  "status": "ok",
  "action": "transition",
  "vault_root": "/abs/path/.sdlc",
  "slug": "sprint-42",
  "retro_path": "07-retrospectives/retros/sprint-42.md",
  "previous_status": "draft",
  "new_status": "final",
  "errors": []
}
```

**Exit codes:** `0` ok/dry-run · `1` user error (invalid slug/status, retro not found,
collision without `--force`) · `2` fatal (permission denied, IO, missing template).

---

## Guardrails

**Never:**
- Skip the duo. The facilitator lens and the engineering lead lens are both required —
  a retro with no facilitator becomes a gripe session; a retro with no engineering lead
  produces vague, unowned actions.
- Close a retro (`--to final`) with actions that have no owner, no due date, or no
  artifact. The pre-final checklist is a hard gate.
- Close a retro with empty Keep / Improve / Stop sections. An empty section is
  either filled or explicitly marked `N/A — <reason>`.
- Close a retro with metrics that are guesses. Real numbers or `N/A — <reason>`.
- Rename or delete an existing retro. The slug is a stable reference — historical
  retros must remain reachable by future retros.
- Confuse a retro with a PR review (`/sdlc-kit:review`) or an incident post-mortem
  (`/sdlc-kit:incident`). Each has its own flow and its own artifact.
- Let personal blame land in the document. Reframe "X keeps breaking the build" as
  "our pre-push hook doesn't catch this class of error" and put the fix in Actions.

**Always:**
- Match the user's active conversation language.
- Announce the duo at the start of the interview.
- Run `--action list` before `scaffold` so you can warn about slug collisions.
- Pre-fill `sprint:` at scaffold time when the user knows the sprint number —
  `--sprint N` saves a manual edit pass and makes `list` output useful.
- Walk every Action item through the owner + due date + artifact contract before
  transitioning to `final`.
- Invoke `/sdlc-kit:sync` after any scaffold or transition.
- Link the previous retro in §References — continuity across retros is how the team
  spots recurring themes.
- Surface the generated file path in the final report so the user can open it.

---

## Examples

> Examples below are in English. In a real session, mirror the user's active conversation
> language in every user-facing line.

**Scaffolding a new retro with the sprint number pre-filled:**
```
User: /sdlc-kit:retro new Sprint 42 retrospective
AI:   [list] 3 existing retros (latest: sprint-41, final). No slug collision for sprint-42.
AI:   Proposed slug: `sprint-42`. Sprint identifier: `42`. Facilitator: Milton. OK?
User: yes.
AI:   [scaffold --slug sprint-42 --title "Sprint 42 Retrospective" --sprint 42]
AI:   created 07-retrospectives/retros/sprint-42.md (status=draft, sprint="42").
AI:   "I'll facilitate as a duo — Agile Facilitator + Engineering Lead. Period first:
       dates, duration, team present. Ready?"
```

**Closing a retro after the meeting (pre-final checklist):**
```
User: /sdlc-kit:retro final sprint-42
AI:   [list] sprint-42 — draft.
AI:   "Before closing, let's walk the pre-final checklist together."
AI:   "- Keep: 4 bullets with evidence ✓
       - Improve: 3 bullets, each tied to a concrete path ✓
       - Stop: 1 bullet ('async standups on Monday') with cost ✓
       - Actions: 5 rows — let me verify each has owner + due date + artifact…
         1. 'Add PR-size lint' — Ana — 2026-05-02 — [[TASK-447]] ✓
         2. 'Rotate on-call to SRE' — Paulo — 2026-04-30 — [[ADR-0032]] ✓
         3. 'Document DB migration flow' — Milton — next retro — <no artifact yet>
       - Row 3 needs a task link before we close. Want me to create one?"
User: yes, create a doc task.
AI:   [creates task] [Edit row 3 artifact]
AI:   "All 5 actions now have owner + date + artifact. Metrics: velocity 42pts, cycle-time
       P50 2.1d, bugs 3 opened / 5 closed, 0 incidents. Team mood: 🟢 energy, 🟡 confidence.
       Checklist all green — closing."
AI:   [transition draft→final] [/sdlc-kit:sync]
AI:   "✓ sprint-42 is now final. Next retro will reference it in §References."
```

**Idempotent + reverse transition (post-meeting correction):**
```
User: /sdlc-kit:retro final sprint-42
AI:   [list] sprint-42 already final — nothing to do.
User: actually I need to fix the velocity number, can we reopen?
AI:   [transition --to draft]
AI:   "✓ sprint-42 back to draft. Make the correction, then /sdlc-kit:retro final sprint-42."
```

---

## See also

- `scripts/retro.py` — file-op helper.
- `assets/vault-tree/07-retrospectives/_templates/retro.md.tpl` — canonical retro template.
- `/sdlc-kit:review` — PR code-review record (different artifact, same `07-retrospectives/` area).
- `/sdlc-kit:incident` — production incident post-mortem.

- `/sdlc-kit:sync` — always invoked after retro edits.
