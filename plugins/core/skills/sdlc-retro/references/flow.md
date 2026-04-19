# sdlc-kit:retro — full flow

## Kind and path

| Kind    | Type slug | Path                                 | Template                                    |
|---------|-----------|--------------------------------------|---------------------------------------------|
| `retro` | `retro`   | `07-retrospectives/retros/<slug>.md` | `07-retrospectives/_templates/retro.md.tpl` |

Recommended slugs: `sprint-42`, `iteration-2026-q2-w3`, `cycle-2026-04`,
`platform-sprint-12`. ASCII-lowercase, hyphen-separated.

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; abort if missing.
2. **Python 3.10+** available.
3. **Template exists** at `<vault>/07-retrospectives/_templates/retro.md.tpl`.

## The expert duo

Announce the duo at the start:
> "I'll facilitate this retro as a duo: **Agile Facilitator** (runs the round, keeps conversation balanced) and **Engineering Lead** (pushes every action item to be concrete, owned, due-dated; insists on real numbers for velocity / cycle time / bug count)."

| Section | Agile Facilitator lens | Engineering Lead lens |
|---|---|---|
| Period | Confirm sprint boundaries, pull team list | Confirm tickets/PRs closed in window |
| Keep | Invite every member to contribute; balance loud vs quiet | Validate claims with evidence (metric, ticket, PR) |
| Improve | Surface tension without blame; reframe personal as process | Distinguish process gap from tooling from skill gap |
| Stop | Name the practice precisely; no fuzzy "bad communication" | Tie each Stop to a concrete cost (time, incidents, rework) |
| Actions | Owner has *agreed*, not been assigned in absentia | Each action has a due date and check-in mechanism |
| Team mood | Pulse-check: energy, confidence, psychological safety | Correlate mood with metrics — mood dip + velocity drop is worth naming |
| Metrics | Frame as signal, not judgement | Real numbers: velocity, cycle time P50/P95, bugs, incidents, WIP |

## Flow

### List: `/sdlc-kit:retro` or `/sdlc-kit:retro list`

1. Run `retro.py --action list`.
2. Show compact table: `slug | status | title | owner | sprint | updated`.
3. Offer next: open latest draft, finalize matured draft, or create new.

### New: `/sdlc-kit:retro new <title>`

1. **Derive slug.** Prefer `sprint-<NN>` when applicable. Allow override.
2. **Capture sprint identifier** for `sprint:` frontmatter.
3. **List first** to warn about collisions.
4. **Scaffold:**
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-retro/scripts/retro.py" \
     --vault-root "<vault>" --action scaffold \
     --slug "<slug>" --title "<title>" [--owner "<facilitator>"] [--sprint "<N>"]
   ```
5. **Announce the duo** and start live interview.

### The interview (LLM-driven, duo, live during meeting)

Walk template top-to-bottom. Section-by-section via Edit. Both lenses contribute.

**Phase A — Frame the period**
1. Confirm sprint name, dates, duration. Pull task counts / specs / ADRs / incidents from auto-summary block. If numbers look wrong, flag and stop.

**Phase B — Keep / Improve / Stop**

Round-robin: every teammate contributes ≥ 1 before anyone contributes a second.
Facilitator enforces turns; Engineering Lead pushes specificity.

- **Keep** — practices/tools/rituals worth defending next sprint.
- **Improve** — mostly works but has concrete improvement path.
- **Stop** — discontinue this sprint, with a cost and an alternative.

A bullet that doesn't name a practice or that blames a person gets rewritten.

**Phase C — Actions**

Every Improve / Stop the team cares about must produce ≥ 1 Action row:
- **Description** — imperative, verifiable. "Add a PR-size lint" not "be better".
- **Owner** — real name who has *agreed*. No "TBD".
- **Deadline** — real date, usually `<next retro date>`.
- **Artifact** — link to task/ADR/doc. If none exists, create before retro closes.

**Phase D — Team mood & metrics**

- **Team mood** — energy + confidence, 🟢/🟡/🔴, plus free-text. Engineering Lead correlates with metrics.
- **Metrics** — velocity (story points or throughput), cycle time P50/P95, bugs opened/closed, incidents (count + SEV), WIP adherence. Real numbers only. If unavailable, mark `N/A — <reason>`.

Bound to ~60–90 minutes. Prefer N/A with reason over filibuster.

### Transition: `/sdlc-kit:retro {draft|final} <slug>`

```bash
python "...retro.py" --vault-root "<vault>" --action transition \
  --slug "<slug>" --to "<draft|final>"
```

Idempotent.

**Pre-final checklist** (hard gate):

- [ ] Keep / Improve / Stop each have real content (no empty; explicit `N/A — <reason>` if nothing).
- [ ] Every action has an owner (real name, not "team" or "TBD") who has *agreed*.
- [ ] Every action has a due date (usually `<next retro date>`).
- [ ] Every action has an artifact link (task, ADR, doc) or explicit plan.
- [ ] Metrics have numbers (or `N/A — <reason>`).
- [ ] Team mood captured — energy + confidence + ≥ 1 free-text note.

If any unchecked, do **not** transition. Fill the gap or mark N/A.

### Sync

After every `scaffold` or `transition`, invoke `/sdlc-kit:sync`.

## Output contract

```json
// --action list
{
  "status": "ok", "action": "list",
  "vault_root": "/abs/path/.sdlc",
  "retros": [
    {"slug": "sprint-42",
     "path": "07-retrospectives/retros/sprint-42.md",
     "title": "Retro — Sprint 42", "status": "draft",
     "owner": "Milton", "sprint": "42", "updated": "2026-04-17"}
  ],
  "count": 1, "errors": []
}

// --action scaffold
{
  "status": "ok", "action": "scaffold",
  "slug": "sprint-42",
  "retro_path": "07-retrospectives/retros/sprint-42.md",
  "was_new": true, "errors": []
}

// --action transition
{
  "status": "ok", "action": "transition",
  "slug": "sprint-42",
  "retro_path": "07-retrospectives/retros/sprint-42.md",
  "previous_status": "draft", "new_status": "final",
  "errors": []
}
```

**Exit codes:** `0` ok/dry-run · `1` user error · `2` fatal.

## Guardrails

**Never:**
- Skip the duo. Facilitator-only = gripe session; Engineering-Lead-only = vague unowned actions.
- Close (`--to final`) with actions lacking owner / due date / artifact. Hard gate.
- Close with empty Keep / Improve / Stop. Empty = filled or `N/A — <reason>`.
- Close with metrics that are guesses. Real numbers or `N/A — <reason>`.
- Rename or delete an existing retro. Slug is stable.
- Confuse retro with PR review or incident post-mortem.
- Let personal blame land in the document. Reframe to process critique.

**Always:**
- Match the user's active conversation language.
- Announce the duo at the start.
- Run `--action list` before `scaffold` to warn about collisions.
- Pre-fill `sprint:` at scaffold via `--sprint N`.
- Walk every Action through owner + due date + artifact contract before `final`.
- Invoke `/sdlc-kit:sync` after any scaffold or transition.
- Link previous retro in §References — continuity helps spot recurring themes.
- Surface generated file path.

## Examples

**Scaffolding with sprint number pre-filled:**
```
User: /sdlc-kit:retro new Sprint 42 retrospective
AI:   [list] 3 existing (latest: sprint-41 final). No collision for sprint-42.
AI:   Proposed slug: `sprint-42`. Sprint identifier: `42`. OK?
User: yes
AI:   [scaffold --slug sprint-42 --sprint 42]
AI:   "I'll facilitate as a duo. Period first: dates, duration, team present. Ready?"
```

**Closing after the meeting (pre-final checklist):**
```
User: /sdlc-kit:retro final sprint-42
AI:   [list] sprint-42 — draft.
AI:   "Walking pre-final checklist:
       - Keep: 4 with evidence ✓
       - Improve: 3 with concrete path ✓
       - Stop: 1 ('async standups') with cost ✓
       - Actions: 5 rows — verifying each has owner + date + artifact:
         1. 'Add PR-size lint' — Ana — 2026-05-02 — [[TASK-447]] ✓
         2. 'Rotate on-call to SRE' — Paulo — 2026-04-30 — [[ADR-0032]] ✓
         3. 'Document DB migration' — Milton — next retro — <no artifact yet>
       - Row 3 needs a task. Want me to create one?"
User: yes
AI:   [creates task][Edit row 3 artifact]
AI:   "Velocity 42pts, cycle-time P50 2.1d, bugs 3 opened/5 closed, 0 incidents.
       Mood: 🟢 energy, 🟡 confidence. Closing."
AI:   [transition draft→final][/sdlc-kit:sync]
```

**Idempotent + reverse (post-meeting correction):**
```
User: /sdlc-kit:retro final sprint-42
AI:   [list] already final — nothing to do.
User: actually I need to fix the velocity number, can we reopen?
AI:   [transition --to draft]
AI:   "✓ back to draft. Make the correction, then `/sdlc-kit:retro final sprint-42`."
```

## See also

- `scripts/retro.py` — file-op helper.
- `assets/vault-tree/07-retrospectives/_templates/retro.md.tpl`.
- `/sdlc-kit:review`, `/sdlc-kit:incident`, `/sdlc-kit:sync`.
