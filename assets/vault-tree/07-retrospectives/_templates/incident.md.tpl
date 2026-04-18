---
type: incident
title: "Incident — {{TITLE}}"
slug: "{{SLUG}}"
status: open
phase: 07
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-incident
owner: "{{OWNER}}"
tags: [retrospective, incident]
severity: "SEV3"
detected_at: ""
mitigated_at: ""
resolved_at: ""
mttr_minutes: 0
---

# Incident — {{TITLE}}

> _(Incident record — severity, timeline, impact and mitigation. `status: resolved` triggers auto-generation of lessons.)_

## Metadata

- **Severity:** `SEV1` / `SEV2` / `SEV3` / `SEV4`
- **Status:** `open` / `investigating` / `mitigated` / `resolved`
- **Incident Commander:** <name>
- **Responders:** <names>

### Severity definition

- **SEV1** — total unavailability, revenue or data impact, 24/7 response.
- **SEV2** — severe degradation, significant impact on users.
- **SEV3** — partial degradation, limited impact.
- **SEV4** — cosmetic issue or no direct user impact.

## Summary

In 2–3 sentences: what happened, who was affected, how it was resolved.

## Timeline

Times in UTC. Fill in as events occur.

| Time | Event |
|---|---|
| `YYYY-MM-DD HH:MM` | **Detection** — alert fired by <source>. |
| `YYYY-MM-DD HH:MM` | **Triage** — on-call engineer starts investigation. |
| `YYYY-MM-DD HH:MM` | **Mitigation** — workaround <X> applied (traffic restored). |
| `YYYY-MM-DD HH:MM` | **Resolution** — root cause fixed and deploy promoted. |

- **MTTD (detection):** <minutes between start and detection>
- **MTTM (mitigation):** <minutes between detection and mitigation>
- **MTTR (resolution):** <minutes between detection and resolution>

## Impact

### Users

- <N affected users> / <% of base>.
- <which journeys were impacted>.

### Revenue

- <estimated loss R$ / USD>.

### Involved systems

- <service A> — <how it was affected>.
- <service B> — <how it was affected>.

## Immediate cause

What failed directly (not the root cause yet).

## Mitigation applied

- <action 1 — ex: rollback to previous version>.
- <action 2 — ex: temporary capacity increase>.

## Post-mitigation monitoring

- **Observed window:** <N> hours after mitigation.
- **Recurring symptoms:** <none / list>.

## Open immediate actions

- [ ] <short-term containment action>.
- [ ] <short-term containment action>.

## Lessons learned

_(When `status: resolved`, the hook triggers `sdlc-kit:incident lessons <slug>` which creates [[<slug>-lessons]] with 5-whys template pre-populated.)_

- **Lessons:** [[<slug>-lessons]] _(generated after `status: resolved`)_

## References

- **Related PRs:** <#numbers>
- **External tickets/alerts:** <links to Grafana, PagerDuty, Jira>
- [[_INDEX]] — global index
