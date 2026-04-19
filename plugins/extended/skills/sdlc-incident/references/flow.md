# sdlc-kit:incident — full flow

## Pre-checks

1. **Resolve vault.** Must have `.sdlc-kit/marker.json`; abort if missing.
2. **Python 3.10+** available.
3. **Template exists** at `<vault>/07-retrospectives/_templates/incident.md.tpl`.

## The expert duo

| Phase | SRE / On-Call lens | Engineering Lead lens |
|---|---|---|
| `open` → `mitigated` | **Primary driver.** Timeline rows, symptom vs cause, mitigation attempts, SLO burn, comms | Supports: composes status updates, protects responders |
| `mitigated` → `resolved` | **Primary driver.** Drives fix, verification, monitoring, unblock confirmation | Supports: queues post-mortem process, starts lessons skeleton |
| `resolved` → `post-mortem` | Supports: facts, 5-whys sanity-check, timeline reconstruction | **Primary driver.** Owns `<slug>-lessons.md`, drives systemic RCA, assigns action items |

Announce the duo at the start:
> "I'll run this incident as a duo: **SRE / On-Call** drives mitigation during the event; **Engineering Lead** owns the lessons doc and follow-up once past `resolved`. Current status: `<status>`, so **<primary>** lens is leading."

## Flow

### List: `/sdlc-kit:incident` or `/sdlc-kit:incident list`

1. Run `incident.py --action list`.
2. Show compact table: `slug | severity | status | title | owner | updated`.
3. Highlight `open` or `mitigated` rows — live incidents first.

### New: `/sdlc-kit:incident new <title>`

Usually under **time pressure**. Minimum viable scaffold = severity + short title.

1. **Severity first.** Ask which SEV. If user says "P0 / critical", map to SEV1 and confirm.
2. **Derive slug.** Default `inc-<YYYY-MM-DD>-<short-kebab>`. Date prefix keeps chronology.
3. **List first** to warn about collisions.
4. **Scaffold:**
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/sdlc-incident/scripts/incident.py" \
     --vault-root "<vault>" --action scaffold \
     --slug "<slug>" --title "<title>" \
     --severity "<SEV1|SEV2|SEV3|SEV4>" \
     [--owner "<incident commander>"] \
     [--detected-at "<YYYY-MM-DD>"]
   ```
   Defaults: `--severity SEV3`, `--detected-at` = today. Refuses overwrite without `--force`.
5. **Minimum content during event** (SRE lens):
   - One-line **Summary** — what, who's affected, current state.
   - First **Timeline** row — detection time + source.
6. Everything else waits until `mitigated`.

### `open` → `mitigated`: `/sdlc-kit:incident mitigate <slug>`

1. **SRE lens drives.** Confirm bleeding stopped — no new errors, journeys restored, SLO burn flattening.
2. Run:
   ```bash
   python "...incident.py" --vault-root "<vault>" --action transition \
     --slug "<slug>" --to mitigated
   ```
   Script auto-fills `mitigated_at`. Report `timestamps_updated` so user can correct if event crossed midnight UTC.
3. Expand body: fill missing Timeline rows, capture Mitigation, fill MTTD/MTTM.

### `mitigated` → `resolved`: `/sdlc-kit:incident resolve <slug>`

1. SRE drives, Engineering Lead warms up. Fix in prod, monitoring clean, observation window elapsed.
2. Run `--action transition --to resolved`. `resolved_at` auto-fills.
3. Fill Impact (users, revenue, systems), MTTR, immediate cause.

### `resolved` → `post-mortem`: `/sdlc-kit:incident post-mortem <slug>`

**This is a hard gate.** Do NOT run the transition until the pre-post-mortem checklist is green:

- [ ] `mitigated_at` set in frontmatter (not empty).
- [ ] `resolved_at` set in frontmatter (not empty).
- [ ] Body has **root cause** narrative (5-whys or equivalent) — the systemic one, not just immediate.
- [ ] Companion lessons doc exists at `07-retrospectives/incidents/<slug>-lessons.md` (Engineering Lead owns; create via **Write** with 5-whys, contributing factors, "what went well / wrong / change", action items table `owner | by-when | tracker link`).
- [ ] Every action item has a named owner and a by-when date. "Unassigned / TBD" is not acceptable.

If any box unchecked, do NOT transition — close the gap first.

Run `--action transition --to post-mortem`. No timestamps auto-fill. Terminal.

### Rewind to `open`: `/sdlc-kit:incident reopen <slug>`

Rare — only when something truly regresses. Existing timestamps are NOT cleared (historical).
Consider whether a **new** incident is more honest than a rewind.

### Sync

After every `scaffold` or `transition`, invoke `/sdlc-kit:sync`. During active
SEV1 you can defer sync until mitigation — but never skip past `resolved`.

## Output contract

```json
// --action list
{
  "status": "ok", "action": "list",
  "vault_root": "/abs/path/.sdlc",
  "incidents": [
    {
      "slug": "inc-2026-04-18-db-outage",
      "path": "07-retrospectives/incidents/inc-2026-04-18-db-outage.md",
      "title": "Database outage on 2026-04-18",
      "status": "mitigated", "severity": "SEV1", "owner": "Milton",
      "detected_at": "2026-04-18", "mitigated_at": "2026-04-18",
      "resolved_at": "", "updated": "2026-04-18"
    }
  ],
  "count": 1, "errors": []
}

// --action scaffold
{
  "status": "ok", "action": "scaffold",
  "slug": "inc-2026-04-18-db-outage",
  "incident_path": "07-retrospectives/incidents/inc-2026-04-18-db-outage.md",
  "was_new": true, "errors": []
}

// --action transition (with timestamp side-effect)
{
  "status": "ok", "action": "transition",
  "slug": "inc-2026-04-18-db-outage",
  "incident_path": "07-retrospectives/incidents/inc-2026-04-18-db-outage.md",
  "previous_status": "open", "new_status": "mitigated",
  "timestamps_updated": ["mitigated_at"],
  "errors": []
}

// --action transition (idempotent or no side-effect)
{
  "status": "ok", "action": "transition",
  "previous_status": "resolved", "new_status": "post-mortem",
  "timestamps_updated": [],
  "errors": []
}
```

**Exit codes:** `0` ok/dry-run · `1` user error (invalid slug/status/severity, incident not found, collision) · `2` fatal.

## Guardrails

**Never:**
- **Delete an incident.** Vault history is a learning asset.
- **Downgrade severity silently.** Update frontmatter AND write a body paragraph explaining the re-grade with timestamps.
- **Skip to `post-mortem`** before the pre-post-mortem checklist is green.
- **Auto-fill a timestamp that has a value** — the script deliberately checks.
- **Rename an incident.** Slug is stable; edit `title:` instead.
- **Skip the duo.** SRE during event, Engineering Lead after.
- **Write lessons in the main incident file** — separate `<slug>-lessons.md`.

**Always:**
- Match the user's active conversation language — in a live incident, speed matters.
- Announce the duo and name the currently-active lens at each transition.
- Run `--action list` before `scaffold` to report collisions.
- After `mitigate` / `resolve`, show `timestamps_updated` and offer correction.
- Before `post-mortem`, walk the pre-post-mortem checklist item by item.
- Invoke `/sdlc-kit:sync` after any scaffold or transition (deferrable during live SEV1, mandatory by `resolved`).
- Surface the generated file path so the user can open it.

## Examples

**Opening a SEV2 mid-event:**
```
User: /sdlc-kit:incident new Checkout p95 latency spike
AI:   "Severity? SEV1=total outage, SEV2=severe degradation, SEV3=minor, SEV4=cosmetic."
User: SEV2, latency at 4s for ~20% of tenants.
AI:   [list] 0 incidents today. Proposed slug: `inc-2026-04-18-checkout-latency`.
User: go.
AI:   [scaffold --severity SEV2]
      created (status=open, detected_at=2026-04-18).
AI:   "SRE lens active. One-line Summary + first Timeline row (UTC time + alert)?"
User: Detected 14:07 UTC by `checkout-latency-p95` Grafana alert. ~R$ 4k/min at risk.
AI:   [Edit §Summary and §Timeline][/sdlc-kit:sync deferred — live]
```

**Transitioning to mitigated:**
```
User: /sdlc-kit:incident mitigate inc-2026-04-18-checkout-latency
AI:   "Confirming: bleeding stopped, p95 under 1s, no new alerts? [yes/no]"
User: yes, ~800ms p95 for 5min.
AI:   [transition --to mitigated]
      timestamps_updated=["mitigated_at"] → 2026-04-18.
AI:   "Mitigated at 2026-04-18. If actual happened on different day, I can correct.
       Now let's fill the rest of the Timeline and Mitigation while fresh."
```

**Closing with post-mortem (hard gate):**
```
User: /sdlc-kit:incident post-mortem inc-2026-04-18-checkout-latency
AI:   "Engineering Lead lens active. Walking pre-post-mortem checklist:
       - mitigated_at ✓ - resolved_at ✓ - 5-whys in body ✓
       - lessons doc ✗ - action items (blocked on lessons doc)"
AI:   "Lessons doc missing. Want me to Write with the 5-whys skeleton + action items table?"
User: yes, create it.
AI:   [Write <slug>-lessons.md][interview][3 action items with owner + by-2026-05-02]
AI:   [transition --to post-mortem][/sdlc-kit:sync]
AI:   "✓ Incident closed. Lessons at [[inc-…-lessons]]. 3 action items queued."
```

## See also

- `scripts/incident.py` — file-op helper.
- `assets/vault-tree/07-retrospectives/_templates/incident.md.tpl` — canonical template.
- `assets/vault-tree/07-retrospectives/_templates/incident-lessons.md.tpl` — lessons template (user Writes manually at post-mortem).
- `/sdlc-kit:retro`, `/sdlc-kit:review`, `/sdlc-kit:sync`.
