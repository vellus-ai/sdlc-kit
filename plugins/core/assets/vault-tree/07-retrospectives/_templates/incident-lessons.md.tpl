---
type: incident-lessons
title: "Lessons — {{TITLE}}"
slug: "{{SLUG}}-lessons"
status: draft
phase: 07
created: {{DATE}}
updated: {{DATE}}
generated_by: sdlc-incident
owner: "{{OWNER}}"
tags: [retrospective, incident, lessons]
incident: "{{SLUG}}"
---

# Lessons — {{TITLE}}

> _(Lessons learned from incident — 5-whys analysis, corrective and preventive actions.)_

## Originating incident

- **Incident:** [[{{SLUG}}]]
- **Severity:** `<SEV>`
- **MTTR:** `<minutes>`
- **Impact:** <summary>

## 5-Whys analysis

Dig deeper until you reach the systemic root cause (person, process or technology), don't stop at "code with a bug".

1. **Why did the incident happen?**
   - <answer level 1>

2. **Why <answer 1>?**
   - <answer level 2>

3. **Why <answer 2>?**
   - <answer level 3>

4. **Why <answer 3>?**
   - <answer level 4>

5. **Why <answer 4>?** ← systemic root cause
   - <answer level 5>

## Root cause

Clear and short statement of root cause (1–3 sentences).

> _"The root cause was <X>, which existed because <Y> and was not detected because <Z>."_

## Contributing factors

Conditions that amplified or enabled the incident.

- <factor 1>
- <factor 2>

## What went well

Parts of the response we should preserve.

- <action / tool / process that helped>

## What didn't work

Failure points in detection, communication or response.

- <observability gap>
- <runbook gap>
- <alert gap>

## Corrective actions

Fix the root cause of **this** incident.

| Action | Owner | Deadline | Artifact |
|---|---|---|---|
| <description> | <name> | <date> | [[<link to task/ADR>]] |

## Preventive actions

Prevent **similar** cases from happening.

| Action | Owner | Deadline | Artifact |
|---|---|---|---|
| <description> | <name> | <date> | [[<link>]] |

## Systems and processes to improve

- **Observability:** <what to improve>.
- **Testing:** <scenarios to cover>.
- **Runbook / on-call:** <what to document>.
- **Architecture:** <what to refactor — may become ADR>.

## Proposed ADRs

If the incident exposed a missing or wrong architectural decision:

- [ ] Propose [[ADR-NNNN-<slug>]] — <title>.

## Approval

- [ ] Lessons reviewed by team on <date>.
- [ ] Actions prioritized in backlog.
- [ ] Lessons marked as `status: approved`.

## References

- **Incident:** [[{{SLUG}}]]
- [[_INDEX]] — global index
